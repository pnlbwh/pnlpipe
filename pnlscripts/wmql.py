#!/usr/bin/env python
from __future__ import print_function
from util import logfmt, TemporaryDirectory
from plumbum import local, cli, FG
from plumbum.cmd import ConvertBetweenFileFormats
from util.scripts import activateTensors_py

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))

def nrrd(f):
    return '.nhdr' in f.suffixes or '.nrrd' in f.suffixes

class App(cli.Application):
    """Runs tract_querier. Output is <out>/*.vtk"""

    ukf = cli.SwitchAttr(
        ['-i', '--in'],
        cli.ExistingFile,
        help='tractography file (.vtk or .vtk.gz), must be in RAS space',
        mandatory=True)
    fsindwi = cli.SwitchAttr(
        ['-f', '--fsindwi'],
        cli.ExistingFile,
        help='Freesurfer labelmap in DWI space (nrrd or nifti)',
        mandatory=True)
    query = cli.SwitchAttr(
        ['-q', '--query'],
        help='tract_querier query file (e.g. wmql-2.0.qry)',
        mandatory=False,
        default=local.path(__file__).dirname / 'wmql-2.0.qry')
    out = cli.SwitchAttr(
        ['-o', '--out'], cli.NonexistentPath, help='output directory', mandatory=True)

    def main(self):
        with TemporaryDirectory() as t:
            t = local.path(t)
            ukf = self.ukf
            fsindwi = self.fsindwi
            if nrrd(self.fsindwi):
                fsindwi = t / 'wmparcInDwi.nii.gz'
                ConvertBetweenFileFormats(self.fsindwi, fsindwi)
            if '.gz' in self.ukf.suffix:
                ukf = t / 'ukf.vtk'
                from plumbum.cmd import gunzip
                (gunzip['-c', self.ukf] > ukf)()

            tract_querier = local['tract_querier']
            tract_math = local['tract_math']
            ukfpruned = t / 'ukfpruned.vtk'
            # tract_math(ukf, 'tract_remove_short_tracts', '2', ukfpruned)
            tract_math[ukf, 'tract_remove_short_tracts', '2', ukfpruned] & FG
            if not ukfpruned.exists():
                raise Exception("tract_math failed to make '{}'".format(ukfpruned))
            self.out.mkdir()
            tract_querier['-t', ukfpruned, '-a', fsindwi, '-q', self.query, '-o', self.out / '_'] & FG

            logging.info('Convert vtk field data to tensor data')
            for vtk in self.out.glob('*.vtk'):
                vtknew = vtk.dirname / (vtk.stem[2:] + ''.join(vtk.suffixes))
                activateTensors_py(vtk, vtknew)
                vtk.delete()

if __name__ == '__main__':
    App.run()
