#!/usr/bin/env python

from __future__ import print_function
from os.path import basename, splitext, abspath, exists, dirname, join
from os import getpid
from util import logfmt, TemporaryDirectory
from util.scripts import bse_py
from plumbum import local, cli
from plumbum.cmd import unu, ls, ConvertBetweenFileFormats, flirt, fslmerge, tar
import numpy as np

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

            unu('save', '-f', 'nrrd', '-e', 'gzip'
                ,'-i', self.dwi
                ,'-o', 'dwijoined.nhdr')

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

            logging.info('Extract the rotations and realign the gradients')
            gDir = []
            header=''
            gNum = []
            gframe = []
            with open('dwijoined.nhdr') as f:
                for line in f:
                    if line.find('DWMRI_gradient_')!=-1:
                        gNum.append(line[15:19])
                        gDir.append( map(float,line[21:-1].split()) )
                    elif line.find('data file:')!=-1:
                        header = header+'data file: EddyCorrect-DWI.nii.gz\n'
                    elif line.find('encoding:')!=-1:
                        header = header+line+'byteskip: -1\n'
                    elif line.find('measurement frame:')!=-1:
                        header = header+line
                        mf =  np.matrix([map(float,line.split()[2][1:-1].split(',')),map(float,line.split()[3][1:-1].split(',')),map(float,line.split()[4][1:-1].split(','))])
                    elif line.find('space:')!=-1:
                        header = header+line
                        # Here I assume either lps or ras so only need to check the first letter
                        space = line.split()[1][0]
                        if (space=='l')|(space=='L'):
                            spctoras = np.matrix([[-1, 0, 0], [0,-1,0], [0,0,1]])
                        else:
                            spctoras = np.matrix([[1, 0, 0], [0,1,0], [0,0,1]])
                    else:
                        header = header+line

            with open('EddyCorrect-DWI.nhdr', 'w') as f:
                f.write(header)
                i=0
                # Transforms are in RAS so need to do inv(MF)*inv(SPC2RAS)*ROTATION*SPC2RAS*MF*GRADIENT
                mfras = mf.I*spctoras.I
                rasmf = spctoras*mf
                for t in transforms:
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
                    newdir = np.dot(mfras*rot*rasmf,gDir[i])
                    f.write('DWMRI_gradient_'+gNum[i]+':= '+str(newdir[0,0])+' '+str(newdir[0,1])+' '+str(newdir[0,2])+'\n')
                    i = i+1

            tar('cvzf', outxfms, transforms)
            unu('save', '-f', 'nrrd', '-e', 'gzip'
                ,'-i', 'EddyCorrect-DWI.nhdr'
                ,'-o', self.out)

            if self.debug:
                tmpdir.move("eddy-debug-"+str(getpid()))

if __name__ == '__main__':
    App.run()
