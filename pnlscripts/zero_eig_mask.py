#!/usr/bin/env python

import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    import nibabel as nib

from dipy.reconst import dti
from dipy.io import read_bvals_bvecs
from dipy.core.gradients import gradient_table
import nrrd
import numpy as np
import argparse
import os

def mask(imgFile, outFile, bvalFile= None, bvecFile= None):



    if imgFile.endswith('.nii.gz') or imgFile.endswith('.nii'):
        bvals, bvecs = read_bvals_bvecs(bvalFile, bvecFile)

        img= nib.load(imgFile)
        data = img.get_data()
        if len(data.shape)!=4:
            raise AttributeError('Not a valid dwi, check dimension')


    elif imgFile.endswith('.nrrd') or imgFile.endswith('.nhdr'):

        img= nrrd.read(imgFile)
        data= img[0]
        hdr= img[1]
        hdr_out= hdr.copy()

        if hdr['dimension']==4:
            axis_elements= hdr['kinds']
        else:
            raise AttributeError('Not a valid dwi, check dimension')

        for i in range(4):
            if axis_elements[i] == 'list' or axis_elements[i] == 'vector':
                grad_axis= i
                break


        # put the gradients along last axis
        if grad_axis!=3:
            data= np.moveaxis(data, grad_axis, 3)

        b_max= float(hdr['DWMRI_b-value'])

        N= hdr['sizes'][grad_axis]
        bvals= np.empty(N, dtype= float)
        bvecs= np.empty((N,3), dtype= float)
        for ind in range(N):
            bvec = [float(num) for num in hdr[f'DWMRI_gradient_{ind:04}'].split()]
            L_2= np.linalg.norm(bvec)
            bvals[ind]= round(L_2 ** 2 * b_max)

            if L_2:
                bvecs[ind]= bvec/L_2
            else:
                bvecs[ind]= [0, 0, 0]

        #     del hdr_out[f'DWMRI_gradient_{ind:04}']
        #
        # del hdr_out['DWMRI_b-value']
        # del hdr_out['measurement frame']
        # del hdr_out['modality']
        # del hdr_out['thicknesses']
        # hdr_out['dimension']= 3
        # hdr_out['sizes']= data.shape[:3]
        # hdr_out['space directions']= hdr['space directions'][:3,:3]
        # hdr_out['centerings']= ['cell', 'cell', 'cell']
        # hdr_out['kinds']= ['space', 'space', 'space']
        # hdr_out['encoding']= 'gzip'

    gtab = gradient_table(bvals, bvecs)
    tenmodel= dti.TensorModel(gtab)
    tenfit= tenmodel.fit(data)

    evals= tenfit.evals

    evals_zero= evals<0.

    evals_zero_mask= (evals_zero[...,0] | evals_zero[...,1] | evals_zero[...,2])*1
    evals_zero_mask= evals_zero_mask.astype('short')

    if outFile.endswith('.nii.gz') or outFile.endswith('.nii'):
        out= nib.Nifti1Image(evals_zero_mask, img.affine)
        nib.save(out, outFile)
    else:
        nrrd.write(outFile, evals_zero_mask,
                   header= {'space directions': hdr['space directions'][:3,:3],
                         'space':hdr_out['space'], 'kinds': ['space', 'space', 'space'],
                         'centerings': ['cell', 'cell', 'cell'], 'space origin':hdr_out['space origin']})


def main():
    # bvalFile = '/home/tb571/Downloads/Harmonization-Python/connectom_prisma_demoData/A/connectom/dwi_A_connectom_st_b1200.bval'
    # bvecFile = '/home/tb571/Downloads/Harmonization-Python/connectom_prisma_demoData/A/connectom/dwi_A_connectom_st_b1200.bvec'
    # imgFile = '/home/tb571/Downloads/Harmonization-Python/connectom_prisma_demoData/A/connectom/dwi_A_connectom_st_b1200.nii.gz'
    # outFile = '/home/tb571/Downloads/Harmonization-Python/connectom_prisma_demoData/A/connectom/zero_eig_mask.nii.gz'
    # mask(imgFile, outFile, bvalFile, bvecFile)

    imgFile= '/rfanfs/pnl-zorro/home/sylvain/test-epi/epi_debug.nrrd'
    outFile= '/rfanfs/pnl-zorro/home/sylvain/test-epi/zero_eig_mask.nhdr'
    mask(imgFile, outFile)

    # parser = argparse.ArgumentParser(
    #     description='Zero eigen value mask of single tensor representation of a dti')
    # parser.add_argument('-i', '--input', type=str, required=True, help='input nifti/nrrd dwi file')
    # parser.add_argument('--bval', type=str, help='bval for nifti image')
    # parser.add_argument('--bvec',  type=str, help='bvec for nifti image')
    # parser.add_argument('-o', '--output', type= str, required=True, help='output nifti/nrrd mask')
    #
    # args = parser.parse_args()
    # mask(args.input, os.path.abspath(args.output), args.bval, args.bvec)

if __name__=='__main__':
    main()