#!/usr/bin/env python
from util import logfmt, TemporaryDirectory, ExistingNrrd, NonexistentNrrd, Nrrd
from util.scripts import bse_py
from plumbum import local, cli
import nrrd
import numpy as np
import matplotlib.pyplot as plt

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))

eps= 2.2204e-16 # for difference map generation
B= 45 # for b0 finding

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

            where_dwi= []
            bmax= float(dwi_hdr['DWMRI_b-value'])
            for i in range(dwi_data.shape[grad_axis]):
                vector= [float(x) for x in dwi_hdr['DWMRI_gradient_' + '{:04}'.format(i)].split()]
                if np.linalg.norm(vector)*bmax>B:
                    where_dwi.append(i)

            if not grad_axis:
                raise AttributeError('Gradient axis could not be determined')

            if np.shape(bse_data)!= np.shape(np.take(dwi_data,-1,axis=grad_axis)):
                raise AttributeError('Baseline and gradients have different dimensions')

            extend_bse= np.expand_dims(bse_data, grad_axis)
            extend_bse= np.repeat(extend_bse, len(where_dwi), grad_axis)

            curtail_dwi= np.take(dwi_data, where_dwi, axis= grad_axis)

            # 1/b0 * min(b0-Gi) with condition at b0~eps
            minMask= np.min(extend_bse - curtail_dwi, axis= grad_axis)/(bse_data+eps)
            minMask[(bse_data<eps) & (minMask<5*eps)]= 0.
            minMask[(bse_data<eps) & (minMask>5*eps)]= 10.
            usrMask= (minMask < eps) * 1

            prefix= str(self.out).split('.')[0]
            nrrd.write(prefix+'_minMask.nrrd', minMask, header=bse_hdr)
            nrrd.write(prefix+'_usrMask.nrrd', usrMask.astype('short'), header=bse_hdr)


if __name__ == '__main__':
    App.run()