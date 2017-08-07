from plumbum import local
from pnlpipe_pipelines._pnl import node, NrrdOutput, NiftiOutput, CsvOutput, InputPathFromKey
import pnlpipe_software as soft
import pandas as pd
import sys
if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO
import logging
log = logging.getLogger(__name__)


@node(params=['BRAINSTools_hash', 'DWIConvert_flags'], deps=['dwi'])
class DwiNrrd(NrrdOutput):
    def static_build(self):
        with soft.BRAINSTools.env(self.BRAINSTools_hash):
            dwiconvert_py['-i', self.dwi, '-o', self.output(), '--flags',
                          self.DWIConvert_flags] & LOG

    def extra_output_names(self):
        return self.DWIConvert_flags.split()


@node(params=['BRAINSTools_hash', 'DWIConvert_flags'], deps=['dwi'])
class DwiNifti(NiftiOutput):
    def static_build(self):
        with soft.BRAINSTools.env(self.BRAINSTools_hash):
            dwiconvert_py['-i', self.dwi, '-o', self.output(), '--flags',
                          self.DWIConvert_flags] & LOG

    def extra_output_names(self):
        return self.DWIConvert_flags.split()


@node(
    params=['caseid', 'nrrdchecker_hash', 'BRAINSTools_hash'],
    deps=['nrrd1', 'nrrd2'])
class NrrdCompareCsv(NrrdOutput):
    def static_build(self):
        binarypath = soft.nrrdchecker.get_path(self.nrrdchecker_hash)
        nrrdchecker = local[binarypath]
        stdout = nrrdchecker('-i', self.nrrd1, '-i', self.nrrd2)
        csv = pd.read_csv(StringIO(stdout))
        csv['caseid'] = self.caseid
        csv['BRAINSTools_hash'] = self.BRAINSTools_hash
        csv.to_csv(self.output().__str__(), index=False)

    def extra_output_names(self):
        return [self.BRAINSTools_hash]


def make_pipeline(caseid,
                  inputDicomKey='dicomdir',
                  DWIConvert_flags='',
                  BRAINSTools_hash='41353e8',
                  nrrdchecker_hash='ffc358f'):

    params = locals()

    tags = {}

    tags['dicomdir'] = InputPathFromKey([inputDicomKey, caseid])

    tags['dwinrrd'] = DwiNrrd(params, deps=[tags['dicomdir']])

    tags['dwifsl'] = DwiNifti(params, deps=[tags['dicomdir']])

    tags['dwifslnrrd'] = DwiNrrd(params, deps=[tags['dwifsl']])

    tags['csv'] = NrrdCompareCsv(
        params, deps=[tags['dwinrrd'], tags['dwifslnrrd']])

    return tags


DEFAULT_TARGET = 'csv'


def summarize(extra_flags=None):
    from pnlpipe_lib import OUTDIR
    from pnlpipe_cli import read_grouped_combos

    pipename = local.path(__file__).stem
    log.info("Combine all csvs into one")
    csvs = []
    for paramid, combo, caseids in read_grouped_combos(pipename):
        pipelines = [make_pipeline(**dict(combo, caseid=caseid)) for caseid in caseids]
        csvs.extend([pipeline['csv'].output().__str__() for pipeline in pipelines])

    df = pd.concat([pd.read_csv(f, converters={'BRAINSTools_hash': str}) for f in csvs])
    outcsv = (OUTDIR / (__name__ + '-all.csv')).__str__()
    df.to_csv(outcsv)
    log.info("Made '{}'".format(outcsv))

    rmd = local.path(__file__).dirname / 'DWIConvertTest.Rmd'
    rmd.copy(OUTDIR)
    rcmd = 'library(rmarkdown); render("{}/DWIConvertTest.Rmd", output_dir="{}")'.format(OUTDIR, OUTDIR)
    from plumbum.cmd import R
    R('-e', rcmd)
    log.info("Made '{}/DWIConvertTest.html'".format(OUTDIR))
