#!/usr/bin/env python

from __future__ import print_function
from os import getpid
from util import logfmt, TemporaryDirectory, abspath, dirname, join
from util.scripts import bse_py
from plumbum import local, cli
from plumbum.cmd import unu, ls, ConvertBetweenFileFormats, flirt, fslmerge, tar
import numpy as np
import nrrd
import nibabel as nib
import sys
from multiprocessing import Pool

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))

def _Register_vol(vol):

    volnii = vol.with_suffix('.nii.gz')
    ConvertBetweenFileFormats(vol, volnii, 'short')
    logging.info('Run FSL flirt affine registration')
    flirt('-interp' ,'sinc'
          ,'-sincwidth' ,'7'
          ,'-sincwindow' ,'blackman'
          ,'-in', volnii
          ,'-ref', 'b0.nii.gz'
          ,'-nosearch'
          ,'-o', volnii
          ,'-omat', volnii.with_suffix('.txt', depth=2)
          ,'-paddingsize', '1')

    return volnii

class App(cli.Application):
    '''Eddy current correction. The NRRD DWI must have volumes stacked along
    the last axis. If not, use `unu permute` to shuffle the axes.'''
    debug = cli.Flag('-d', help='Debug, saves registrations to eddy-debug-<pid>')
    dwi = cli.SwitchAttr('-i', cli.ExistingFile, help='DWI (nrrd)')
    out = cli.SwitchAttr('-o', help='Eddy corrected DWI')
    overwrite = cli.Flag('--force', default=False, help='Force overwrite')
    nproc = cli.SwitchAttr(
        ['-n', '--nproc'], help='''number of threads to use, if other processes in your computer 
        becomes sluggish/you run into memory error, reduce --nproc''', default= 8)

    def main(self):
        self.out = local.path(self.out)
        if self.out.exists():
            if self.overwrite:
                self.out.delete()
            else:
                logging.error("{} exists, use '--force' to overwrite it".format(self.out))
                sys.exit(1)
        outxfms = self.out.dirname / self.out.stem+'-xfms.tgz'
        with TemporaryDirectory() as tmpdir, local.cwd(tmpdir):
            tmpdir = local.path(tmpdir)

            # fileinput() caused trouble reading data file in python 3, so switching to nrrd
            # if the hdr has 'nan' in space origin, the following will take care of that
            img= nrrd.read(self.dwi)
            dwi= img[0]
            hdr= img[1]

            hdr_out= hdr.copy()
            hdr_out['space origin']= hdr_out['space origin'][0:3]

            nrrd.write('dwijoined.nhdr', dwi, header= hdr_out, compression_level = 1)

            # we want to use this hdr to write a new .nhdr file with corresponding data file
            # so delete old data file from the hdr
            if 'data file' in hdr_out.keys():
                del hdr_out['data file']
            elif 'datafile' in hdr_out.keys():
                del hdr_out['datafile']

            if 'content' in hdr_out.keys():
                del hdr_out['content']


            logging.info('Dice the DWI')

            # Since fslmerge works along the 3rd axis only, dicing also has to be along that axis
            # So, use `unu permute` to reorient the volumes to be stacked along 3rd axis only
            # Include this issue in the tutorial
            (unu['convert', '-t', 'int16', '-i', 'dwijoined.nhdr'] |
            unu['dice', '-a', '3', '-o', 'Diffusion-G'])()
            vols = tmpdir.glob('Diffusion-G*.nrrd')
            vols.sort()

            logging.info('Extract the B0')
            bse_py('-i', 'dwijoined.nhdr', '-o', 'b0.nrrd')
            ConvertBetweenFileFormats('b0.nrrd', 'b0.nii.gz', 'short')

            logging.info('Register each volume to the B0')

            # use the following multi-processed loop
            pool= Pool(int(self.nproc))
            res= pool.map_async(_Register_vol, vols)
            volsRegistered= res.get()
            pool.close()
            pool.join()

            # or use the following for loop
            # volsRegistered = []
            # for vol in vols:
            #     volnii = vol.with_suffix('.nii.gz')
            #     ConvertBetweenFileFormats(vol, volnii, 'short')
            #     logging.info('Run FSL flirt affine registration')
            #     flirt('-interp' ,'sinc'
            #           ,'-sincwidth' ,'7'
            #           ,'-sincwindow' ,'blackman'
            #           ,'-in', volnii
            #           ,'-ref', 'b0.nii.gz'
            #           ,'-nosearch'
            #           ,'-o', volnii
            #           ,'-omat', volnii.with_suffix('.txt', depth=2)
            #           ,'-paddingsize', '1')
            #     volsRegistered.append(volnii)


            fslmerge('-t', 'EddyCorrect-DWI', volsRegistered)
            transforms = tmpdir.glob('Diffusion-G*.txt')
            transforms.sort()

            # nibabel loading can be avoided by setting 'data file' = EddyCorrect-DWI.nii.gz
            # and 'byteskip' = -1
            # Tashrif updated Pynrrd package to properly handle that
            new_dwi= nib.load('EddyCorrect-DWI.nii.gz').get_data()

            logging.info('Extract the rotations and realign the gradients')

            space= hdr_out['space'].lower()
            if (space == 'left'):
                spctoras = np.matrix([[-1, 0, 0], [0, -1, 0], [0, 0, 1]])
            else:
                spctoras = np.matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
            mf = np.matrix(hdr['measurement frame'])


            # Transforms are in RAS so need to do inv(MF)*inv(SPC2RAS)*ROTATION*SPC2RAS*MF*GRADIENT
            mfras = mf.I*spctoras.I
            rasmf = spctoras*mf
            for (i,t) in enumerate(transforms):

                gDir = [float(num) for num in hdr_out['DWMRI_gradient_' + '{:04}'.format(i)].split(' ') if num]

                logging.info('Apply ' + t)
                tra = np.loadtxt(t)
                # removes the translation
                aff = np.matrix(tra[0:3,0:3])
                # computes the finite strain of aff to get the rotation
                rot = aff*aff.T
                # compute the square root of rot
                [el, ev] = np.linalg.eig(rot)
                eL = np.identity(3)*np.sqrt(el)
                sq = ev*eL*ev.I
                # finally the rotation is defined as
                rot = sq.I*aff
                newdir = np.dot(mfras*rot*rasmf,gDir)

                hdr_out['DWMRI_gradient_' + '{:04}'.format(i)]= ('   ').join(str(x) for x in newdir.tolist()[0])


            tar('cvzf', outxfms, transforms)

            nrrd.write(self.out, new_dwi, header= hdr_out, compression_level = 1)

            if self.debug:
                tmpdir.copy(join(dirname(self.out),"eddy-debug-"+str(getpid())))

if __name__ == '__main__':
    App.run()
