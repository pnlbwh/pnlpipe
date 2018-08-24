#!/usr/bin/env python
from __future__ import print_function
import sys
from util import logfmt, ExistingNrrdOrNifti, TemporaryDirectory, set_log_format
from plumbum import cli, FG, local
from plumbum.cmd import unu, DWIConvert
import logging
# logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))
set_log_format(logging.INFO)
log = logging.getLogger(__file__)


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
	dwiconvert.py -i dwi.nii.gz -o dwi.nhdr
        dwiconvert.py -i dicomdir -o dwi.nii.gz --flags "useIdentityMeaseurementFrame useBMatrixGradientDirections"
        dwiconvert.py -i dwi.nrrd -o dwi.nhdr
        dwiconvert.py -i dwi.nrrd -o dwi.nii
	
    """

    force = cli.Flag(['-f','--force'], help='Force overwrite if output already exists',mandatory=False,default=False)
    dwi = cli.SwitchAttr(
        ['-i', '--input'],
        help='Input DWI (nrrd or nifti), or dicom directory',
        mandatory=True)
    out = cli.SwitchAttr(
        ['-o', '--out'],
        help='output DWI (nrrd or nifti)',
        default="",
        mandatory=True)

    flags = cli.SwitchAttr(
        ['--flags'],
        default="",
        help="Extra flags to pass to DWIConvert, e.g useIdentityMeaseurementFrame useBMatrixGradientDirections"
    )

    def main(self):
        dwi = local.path(self.dwi)
        out = local.path(self.out)
        flags = ["--"+flag for flag in self.flags.split()]

        if self.force and out.exists():
            out.delete()

        if dwi.suffixes == out.suffixes:
            dwi.copy(out)

        elif nrrd(dwi) and nrrd(out):
            unu['save', '-e', 'gzip', '-f', 'nrrd', '-i', dwi, '-o', out] & FG

        elif nrrd(dwi) and nifti(out):
            DWIConvert('--conversionMode', 'NrrdToFSL'
                        ,'--inputVolume', dwi
                        ,'-o', out, *flags)

        elif nifti(dwi) and nrrd(out):
            DWIConvert('--conversionMode', 'FSLToNrrd'
                        ,'--inputBValues', bval(dwi)
                        ,'--inputBVectors', bvec(dwi)
                        ,'--inputVolume', dwi
                        , '-o', out, *flags)
            unu['save', '-e', 'gzip', '-f', 'nrrd', '-i', out, '-o', out] & FG

        elif nifti(dwi) and nifti(out):
            DWIConvert('--inputBValues', bval(dwi)
                       ,'--inputBVectors', bvec(dwi)
                       ,'--inputVolume', dwi
                       , '-o', out, *flags)

        elif dwi.is_dir() and nifti(out):
            DWIConvert('--inputDicomDirectory', dwi
                       ,'-o', out, *flags)
        elif dwi.is_dir and nrrd(out):
            DWIConvert('--inputDicomDirectory', dwi,
                       '-o', out, *flags)
            unu['save', '-e', 'gzip', '-f', 'nrrd', '-i', out, '-o', out] & FG

        else:
            raise Exception('Input must be nrrd, nifti, or a dicom directory, and output must be nrrd or nifti.')


if __name__ == '__main__':
    App.run()
