#!/usr/bin/env python

from __future__ import print_function
from os.path import basename, splitext, abspath, exists, dirname, join
from os import getpid
from util import logfmt, TemporaryDirectory
from util.scripts import bse_py
from plumbum import local, cli
from plumbum.cmd import unu, ls, ConvertBetweenFileFormats, flirt, fslmerge, tar
import numpy as np
import nrrd
import nibabel as nib
import sys

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))

class App(cli.Application):
    DESCRIPTION='Eddy current correction.'
    debug = cli.Flag('-d', help='Debug, saves registrations to eddy-debug-<pid>')
    dwi = cli.SwitchAttr('-i', cli.ExistingFile, help='DWI (nrrd)')
    out = cli.SwitchAttr('-o', help='Eddy corrected DWI')
    overwrite = cli.Flag('--force', default=False, help='Force overwrite')

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

            # if the hdr has 'nan' in space origin, the following will take care of that
            img= nrrd.read(self.dwi)
            dwi= img[0]
            hdr= img[1]

            hdr_out= hdr.copy()
            hdr_out['space origin']= hdr_out['space origin'][0:3]

            nrrd.write('dwijoined.nhdr', dwi, header= hdr_out, compression_level = 1)

            try:
                del hdr_out['data file']
            except:
                del hdr_out['content']


            logging.info('Dice the DWI')
            (unu['convert', '-t', 'int16', '-i', 'dwijoined.nhdr'] |
            unu['dice', '-a', '3', '-o', 'Diffusion-G'])()
            vols = tmpdir.glob('Diffusion-G*.nrrd')
            vols.sort()

            logging.info('Extract the B0')
            bse_py('-i', 'dwijoined.nhdr', '-o', 'b0.nrrd')
            ConvertBetweenFileFormats('b0.nrrd', 'b0.nii.gz', 'short')

            logging.info('Register each volume to the B0')
            volsRegistered = []
            for vol in vols:
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
                volsRegistered.append(volnii)
            fslmerge('-t', 'EddyCorrect-DWI', volsRegistered)
            transforms = tmpdir.glob('Diffusion-G*.txt')
            transforms.sort()

            new_dwi= nib.load('EddyCorrect-DWI.nii.gz').get_data()

            logging.info('Extract the rotations and realign the gradients')


            # header=''
            # gNum = []

            # with open('dwijoined.nhdr') as f:
            #     for line in f:
            #         if line.find('DWMRI_gradient_')!=-1:
            #             gNum.append(line[15:19])
            #             gDir.append([float(x) for x in line[21:-1].split()])
            #         elif line.find('data file:')!=-1:
            #             # header = header+'data file: EddyCorrect-DWI.nii.gz\n'
            #             header = header+'data file: dwijoined.raw.gz\n'
            #         elif line.find('encoding:')!=-1:
            #             header = header+line+'byteskip: -1\n'
            #         elif line.find('measurement frame:')!=-1:
            #             header = header+line
            #
            #             # mf =  np.matrix([map(float,line.split()[2][1:-1].split(',')),
            #             #                  map(float,line.split()[3][1:-1].split(',')),
            #             #                  map(float,line.split()[4][1:-1].split(','))])
            #
            #             # Python 3 compatible command
            #             mf = np.matrix([[float(x) for x in line.split()[2][1:-1].split(',')],
            #                             [float(x) for x in line.split()[3][1:-1].split(',')],
            #                             [float(x) for x in line.split()[4][1:-1].split(',')]])
            #
            #         elif line.find('space:')!=-1:
            #             header = header+line
            #             # Here I assume either lps or ras so only need to check the first letter
            #             space = line.split()[1][0]
            #             if (space=='l')|(space=='L'):
            #                 spctoras = np.matrix([[-1, 0, 0], [0,-1,0], [0,0,1]])
            #             else:
            #                 spctoras = np.matrix([[1, 0, 0], [0,1,0], [0,0,1]])
            #         else:
            #             header = header+line
            #
            # # Without this conversion, '.raw' file will not be generated
            # # ConvertBetweenFileFormats('EddyCorrect-DWI.nii.gz', 'EddyCorrect-DWI.nhdr', 'short')

            space= hdr_out['space'].lower()
            if (space == 'left'):
                spctoras = np.matrix([[-1, 0, 0], [0, -1, 0], [0, 0, 1]])
            else:
                spctoras = np.matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
            mf = np.matrix(hdr['measurement frame'])

            # gDir = []
            # count = 0
            # while hdr_out['DWMRI_gradient_' + '{:04}'.format(count)]:
            #     gDir[count, :] = [float(num) for num in hdr_out['DWMRI_gradient_' + '{:04}'.format(count)].split(' ') if
            #                       num]
            #     count += 1

            # Transforms are in RAS so need to do inv(MF)*inv(SPC2RAS)*ROTATION*SPC2RAS*MF*GRADIENT
            mfras = mf.I*spctoras.I
            rasmf = spctoras*mf
            for (i,t) in enumerate(transforms):

                gDir = [float(num) for num in hdr_out['DWMRI_gradient_' + '{:04}'.format(i)].split(' ') if num]

                logging.info('Apply ' + t)
                tra = np.loadtxt(t)
                #removes the translation
                aff = np.matrix(tra[0:3,0:3])
                # computes the finite strain of aff to get the rotation
                rot = aff*aff.T
                # Computer the square root of rot
                [el, ev] = np.linalg.eig(rot)
                eL = np.identity(3)*np.sqrt(el)
                sq = ev*eL*ev.I
                # finally the rotation is defined as
                rot = sq.I*aff
                newdir = np.dot(mfras*rot*rasmf,gDir)

                hdr_out['DWMRI_gradient_' + '{:04}'.format(i)]= ('   ').join(str(x) for x in newdir.tolist()[0])


            tar('cvzf', outxfms, transforms)
            # unu('save', '-f', 'nrrd', '-e', 'gzip'
            #     ,'-i', 'EddyCorrect-DWI.nhdr'
            #     ,'-o', self.out)

            nrrd.write(self.out, new_dwi, header= hdr_out, compression_level = 1)


            if self.debug:
                tmpdir.move("eddy-debug-"+str(getpid()))

if __name__ == '__main__':
    App.run()
