#!/usr/bin/env python
from util import logfmt, TemporaryDirectory, ExistingNrrd, NonexistentNrrd, Nrrd
from util.scripts import bse_py
from plumbum import local, cli
from plumbum.cmd import unu
import sys, nrrd
import numpy as np

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))

eps= -100

class App(cli.Application):

    dwi = cli.SwitchAttr(
        '--dwi', ExistingNrrd, help='DWI', mandatory=True)
    dwimask = cli.SwitchAttr(
        '--dwimask', ExistingNrrd, help='DWI mask', mandatory=True)
    out = cli.SwitchAttr(
        ['-o', '--out'], help='prefix for output', mandatory=True)

    def main(self):

        with TemporaryDirectory() as tmpdir:
            tmpdir = local.path(tmpdir)
            bse = tmpdir / "bsemasked.nrrd"

            logging.info('1. Extract and mask the DWI b0')
            bse_py('-m', self.dwimask, '-i', self.dwi, '-o', bse)

            logging.info('2. Calculate difference mask')

            bseImg= nrrd.read(bse)
            bse_hdr= bseImg[1]
            bse_data= bseImg[0]
            dwiImg= nrrd.read(self.dwi)
            dwi_hdr= dwiImg[1]
            dwi_data= dwiImg[0]

            axis_elements= dwi_hdr['kinds']
            grad_axis= []
            for i in range(4):
                if axis_elements[i] == 'list' or axis_elements[i] == 'vector':
                    grad_axis= i
                    break

            if not grad_axis:
                raise AttributeError('Gradient axis could not be determined')

            if np.shape(bse_data)!= np.shape(np.take(dwi_data,-1,axis=grad_axis)):
                raise AttributeError('baseline and volumes have different dimensions')

            extend_bse= np.expand_dims(bse_data, grad_axis)
            extend_bse= np.repeat(extend_bse, dwi_data.shape[grad_axis], grad_axis)

            minMask= np.min(extend_bse - dwi_data, axis= grad_axis)
            usrMask= (minMask < eps) * 1

            prefix= str(self.out).split('.')[0]
            nrrd.write(prefix+'_minMask.nrrd', minMask, header=bse_hdr)
            nrrd.write(prefix+'_usrMask.nrrd', usrMask, header=bse_hdr)


if __name__ == '__main__':
    App.run()