#!/usr/bin/env python
from __future__ import print_function
import sys
from util import logfmt, ExistingNrrdOrNifti
from plumbum import cli, FG, local
from plumbum.cmd import unu, DWIConvert

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))


def nifti(f):
    return '.nii' in f.suffixes
def nrrd(f):
    return '.nrrd' in f.suffixes or '.nhdr' in f.suffixes
def bval(f):
    return f.with_suffix('.bval', depth=2)
def bvec(f):
    return f.with_suffix('.bvec', depth=2)


class App(cli.Application):
    """Converts DWI (or dicom directory), uses unu and DWIConvert.

    DWIConvert is called with '--allowLossyConversion'.

    Examples:
        dwiconvert.py -i dwi.nii.gz -o dwi.nrrd
        dwiconvert.py -i dicomdir -o dwi.nii.gz
        dwiconvert.py -i dwi.nrrd -o dwi.nhdr

    """

    force = cli.Flag(['-f','--force'], help='Force overwrite if output already exists',mandatory=False,default=False)
    dwi = cli.SwitchAttr(
        ['-i', '--input'],
        help='Input DWI (nrrd or nifti), or dicom directory',
        mandatory=True)
    out = cli.SwitchAttr(
        ['-o', '--out'],
        help='output DWI (nrrd or nifti)',
        mandatory=True)

    def main(self):
        dwi = local.path(self.dwi)
        out = local.path(self.out)

        if self.force and out.exists():
            out.delete()

        if dwi.suffixes == out.suffixes:
            dwi.copy(out)

        elif nrrd(dwi) and nrrd(out):
            unu('save', '-e', 'gzip', '-f', 'nrrd', '-i', dwi, '-o', out)

        elif nrrd(dwi) and nifti(out):
            DWIConvert('--conversionMode', 'NrrdToFSL'
                        ,'--inputVolume', dwi
                        ,'--allowLossyConversion'
                        ,'-o', out)

        elif nifti(dwi) and nrrd(out):
            DWIConvert('--conversionMode', 'FSLToNrrd'
                        ,'--inputBValues', bval(dwi)
                        ,'--inputBVectors', bvec(dwi)
                        ,'--inputVolume', dwi
                        ,'--allowLossyConversion'
                        , '-o', out)
            (unu['save', '-e', 'gzip', '-f', 'nrrd', '-i', out, '-o', out]) & FG

        elif nifti(dwi) and nifti(out):
            ConvertBetweenFileFormats(dwi, out)

        elif dwi.is_dir() and nifti(out):
            DWIConvert('--inputDicomDirectory', dwi
                       ,'--allowLossyConversion'
                       ,'-o', out)
        elif dwi.is_dir and nrrd(out):
            # converting straight to nrrd will make a non-identity measurement frame
            with TemporaryDirectory() as tmpdir:
                tmpnii = tmpdir / 'dwi.nii.gz'
                DWIConvert('--inputDicomDirectory', dwi
                           ,'--allowLossyConversion'
                           ,'-o', tmpnii)
                DWIConvert('--conversionMode', 'FSLToNrrd'
                        ,'--inputBValues', bval(tmpnii)
                        ,'--inputBVectors', bvec(tmpnii)
                        ,'--inputVolume', tmpnii
                        ,'--allowLossyConversion'
                        , '-o', out)
            (unu['save', '-e', 'gzip', '-f', 'nrrd', '-i', out, '-o', out]) & FG

        else:
            raise Exception('Input must be nrrd, nifti, or a dicom directory, and output must be nrrd or nifti.')


if __name__ == '__main__':
    App.run()
