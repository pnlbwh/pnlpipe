#!/usr/bin/env python
from __future__ import print_function
from util import logfmt
import util
from plumbum import local, cli, FG
from plumbum.cmd import unu, ConvertBetweenFileFormats, ComposeMultiTransform, antsApplyTransforms
from util.antspath import antsRegistrationSyN_sh
from itertools import izip_longest
import pandas as pd
import sys
import numpy as np

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO, format=logfmt(__file__))

ANTSJOINTFUSION_PARAMS = ['--search-radius', 5
                         ,'--patch-radius',3
                         ,'--patch-metric','PC'
                         ,'--constrain-nonnegative',1
                         ,'--alpha', 0.4
                         ,'--beta', 3.0]

def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    if n == 1:
        return [iterable]
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)


def computeWarp(image, target, out):
    with local.tempdir() as tmpdir:
        tmpdir = local.path(tmpdir)
        pre = tmpdir / 'ants'
        warp = pre + '1Warp.nii.gz'
        affine = pre + '0GenericAffine.mat'

	# pre is the prefix (directory) for saving 1Warp.nii.gz and 0GenericAffine.mat
        antsRegistrationSyN_sh['-m', image, '-f', target, '-o', pre, '-n',
                               32] & FG

	# out is Warp{idx}.nii.gz, saved in the specified output direcotry
	# ComposeMultiTransform combines the 1Warp.nii.gz and 0GenericAffine.mat into a Warp{idx}.nii.gz file
        ComposeMultiTransform('3', out, '-R', target, warp, affine) 


def applyWarp(moving, warp, reference, out, interpolation='Linear'):
    '''Interpolation options:
    Linear
    NearestNeighbor
    MultiLabel[<sigma=imageSpacing>,<alpha=4.0>]
    Gaussian[<sigma=imageSpacing>,<alpha=1.0>]
    BSpline[<order=3>]
    CosineWindowedSinc
    WelchWindowedSinc
    HammingWindowedSinc
    LanczosWindowedSinc
    GenericLabel[<interpolator=Linear>]
    '''

    # antsApplyTransforms reads Warp{idx}.nii.gz and 
    # creates atlas{idx}.nii.gz and {labelname}{idx}.nii.gz in the specified ouput directory
    antsApplyTransforms['-d', '3', '-i', moving, '-t', warp, '-r', reference,
                        '-o', out, '--interpolation', interpolation] & FG


def fuseAntsJointFusion(target, images, labels, out):
    from plumbum.cmd import antsJointFusion

    # images are the warped images atlas{idx}.nii.gz
    # labelmaps are the warped labels {labelname}{idx}.nii.gz
    # out is {labelname}.nrrd
    antsJointFusionArgs = \
        ['-d', 3 ,'-t', target ,'-g'] + \
        images + \
        ['-l'] +  \
        labels + \
        ['-o', out] + \
        ANTSJOINTFUSION_PARAMS

    antsJointFusion(*antsJointFusionArgs)


def fuseAvg(labels, out):
    from plumbum.cmd import AverageImages
    with local.tempdir() as tmpdir:
        nii = local.path(tmpdir) / 'avg.nii.gz'
        AverageImages('3', nii, '0', *labels)

	# out is {labelname}.nrrd
        ConvertBetweenFileFormats(nii, out)

    # Binary operation, if out>0.5, pipe the output and save as {labelname}.nrrd
    (unu['2op', 'gt', out, '0.5'] | \
     	unu['save', '-e', 'gzip', '-f', 'nrrd', '-o', out]) & FG


def makeAtlases(target, trainingTable, outdir, fusion):
    outdir = local.path(outdir)
    outdir.mkdir()

    logging.info(
        'Create {} atlases: compute transforms from images to target and apply'.format(
            len(trainingTable)))
    
 
          
    for idx, r in trainingTable.iterrows(): # reads each row except the headers
        
        print('Registering image {idx} to target'.format(**locals()))
        warp = outdir / 'warp{idx}.nii.gz'.format(**locals())
        atlas = outdir / 'atlas{idx}.nii.gz'.format(**locals())
        logging.info('Make {atlas}'.format(**locals()))
	
	# warp is computed among the first column images and the target image
	# then that warp is applied to images in other columns
	# assuming first column of the dictionary contains moving images        
	computeWarp(r[0], target, warp) # first column of each row is used here
	applyWarp(r[0], warp, target, atlas) # first column of each row is used here

	# labelname is the column header and label is the image in the csv file
        for labelname, label in r.iloc[1:].iteritems(): # rest of the columns of each row are used here
            atlaslabel = outdir / '{labelname}{idx}.nii.gz'.format(**locals())
            logging.info('Make {atlaslabel}'.format(**locals()))
            
	    # creates {labelname}{idx}.nii.gz in the output directory
	    # applying Warp{idx}.nii.gz on each image under 'labelname' column in the csv file	
	    applyWarp(label,
	                warp,
        	        target,
        	        atlaslabel,
        	        interpolation='NearestNeighbor')
	
    
    
    for labelname in list(trainingTable)[1:]:  #list(d) gets column names

	out = outdir / labelname + '.nrrd'
	labelmaps = outdir // (labelname + '*')

	if fusion.lower() == 'avg':
		print(' ')                
		fuseAvg(labelmaps, out)

	elif fusion.lower() == 'antsjointfusion':
		print(' ')

		# atlasimages are the warped images
		# labelmaps are the warped labels
		atlasimages = outdir // 'atlas*.nii.gz'
		fuseAntsJointFusion(target, atlasimages, labelmaps, out)

	else:
		print('Unrecognized fusion option: {}. Skipping.'.format(fusion))


class Atlas(cli.Application):
    """Makes atlas image/labelmap pairs for a target image. Option to merge labelmaps via averaging (MABS)
    or AntsJointFusion."""

    def main(self, *args):
        if args:
            print("Unknown command {0!r}".format(args[0]))
            return 1
        if not self.nested_command:
            print("No command given")
            return 1  # error exit code


@Atlas.subcommand("args")
class AtlasArgs(cli.Application):
    """Specify training images and labelmaps via commandline arguments."""

    target = cli.SwitchAttr(
        ['-t', '--target'],
        cli.ExistingFile,
        help='target image',
        mandatory=True)
    fusion = cli.SwitchAttr(
        ['--fusion'],
        cli.Set("avg", "antsJointFusion", case_sensitive=False),
        list=True,
        help='Also create predicted labelmap(s) by fusing the atlas labelmaps')
    out = cli.SwitchAttr(
        ['-o', '--out'], help='output directory', mandatory=True)

    images = cli.SwitchAttr(
        ['-i', '--images'],
        help='list of images in quotations, e.g. "img1.nrrd img2.nrrd"',
        mandatory=True)
    labels = cli.SwitchAttr(
        ['-l', '--labels'],
        help='list of labelmap images in quotations, e.g. "mask1.nrrd mask2.nrrd cingr1.nrrd cingr2.nrrd"',
        mandatory=True)
    names = cli.SwitchAttr(
        ['-n', '--names'],
        help='list of names for generated labelmaps, e.g. "atlasmask atlascingr"',
        mandatory=True)

    def main(self):
        images = self.images.split()
        labels = self.labels.split()
        labelnames = self.names.split()
        quotient, remainder = divmod(len(labels), len(images))
        if remainder != 0:
            logging.error(
                'Wrong number of labelmaps, must be a multiple of number of images ('
                + str(len(images)) + '). Instead there is a remainder of ' +
                str(remainder))
            sys.exit(1)
        if quotient != len(labelnames):
            logging.error(
                'Wrong number of names, must match number of labelmap training sets: '
                + str(quotient))
            sys.exit(1)
        labelcols = grouper(labels, quotient)
        trainingTable = pd.DataFrame(
            dict(zip(labelnames, labelcols) + [('image', images)]))
        makeAtlases(self.target, trainingTable, self.out, self.fusion)
        logging.info('Made ' + self.out)


@Atlas.subcommand("csv")
class AtlasCsv(cli.Application):
    """Specify training images and labelmaps via a csv file.
    Put the images with any header in the first column, 
    and labelmaps with proper headers in the consecutive columns. 
    The headers in the labelmap columns will be used to name the generated atlas labelmaps.
    """

    target = cli.SwitchAttr(
        ['-t', '--target'],
        cli.ExistingFile,
        help='target image',
        mandatory=True)
    fusions = cli.SwitchAttr(
        ['-f', '--fusion'],
        cli.Set("avg", "antsJointFusion", case_sensitive=False),
        help='Also create predicted labelmap(s) by combining the atlas labelmaps')
    out = cli.SwitchAttr(
        ['-o', '--out'], help='output directory', mandatory=True)

    @cli.positional(cli.ExistingFile)
    def main(self, csvFile):
        trainingTable = pd.read_csv(csvFile)
        makeAtlases(self.target, trainingTable, self.out, self.fusions)
        logging.info('Made ' + self.out)


if __name__ == '__main__':
    Atlas.run()
