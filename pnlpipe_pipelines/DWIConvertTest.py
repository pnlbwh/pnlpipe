import sys
from pnlpipe_pipelines._pnl import node, Node, caseid_node_to_filepath, dwiconvert_py, InputDirFromKey
from pnlpipe_software import BRAINSTools, nrrdchecker
from plumbum import local, FG, TEE
import pandas as pd
if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO

DEFAULT_TARGET = 'csv'


@node(params=['BRAINSTools_hash', 'DWIConvert_flags'],
      deps=['dwi'])
class DwiNrrd(Node):
    def static_build(self):
        with BRAINSTools.env(self.hash_BRAINSTools):
            dwiconvert_py['-i', self.dwi, '-o', self.output(), '--flags',
                          self.DWIConvert_flags]

    def output(self):
        caseid_node_to_filepath(
            self, '.nrrd', caseid_dir=False, extra_words=self.DWIConvert_flags)


@node(params=['BRAINSTools_hash', 'DWIConvert_flags'],
      deps=['dwi'])
class DwiNifti(Node):
    def static_build(self):
        with BRAINSTools.env(self.params['hash_BRAINSTools']):
            dwiconvert_py['-i', self.dwi, '-o', self.output()] & FG

    def output(self):
        caseid_node_to_filepath(
            self,
            '.nii.gz',
            caseid_dir=False,
            extra_words=self.DWIConvert_flags)


@node(
    params=['caseid', 'nrrdchecker_hash', 'BRAINSTools_hash'],
    deps=['nrrd1', 'nrrd2'])
class NrrdCompareCsv(Node):
    def static_build(self):
        binarypath = nrrdchecker.get_path(
            self.hash_nrrdchecker)
        nrrdchecker = local[binarypath]
        stdout = nrrdchecker('-i', self.nrrd1, '-r', self.nrrd2)
        csv = pd.read_csv(StringIO(stdout))
        csv['caseid'] = self.caseid
        csv['BRAINSTools_hash'] = self.BRAINSTools_hash
        csv.to_csv(self.output(), index=False)

    def output(self):
        caseid_node_to_filepath(
            self,
            '.csv',
            caseid_dir=False,
            extra_words=self.BRAINSTools_hash)



def make_pipeline(caseid,
                  inputDicomKey='dicomdir',
                  DWIConvert_flags='',
                  BRAINSTools_hash='41353e8',
                  nrrdchecker_hash='ffc358f'):

    params = locals()

    tags = {'_name': "BRAINSTools DWIConvert test"}

    tags['dicomdir'] = InputDirFromKey([inputDicomKey, caseid])

    tags['dwinrrd'] = DwiNrrd(params, deps=[tags['dicomdir']])

    tags['dwinifti'] = DwiNifti(params, deps=[tags['dicomdir']])

    tags['dwinrrdFromFSL'] = DwiNrrd(params, deps=[tags['dwifsl']])

    tags['csv'] = NrrdCompareCsv(
        params, deps=[tags['dwinrrd'], tags['dwinrrdFromFSL']])

    return tags


def status(combos):
    for combo in combos:
        for p in combo['paramPoints']:
            pipeline = make_pipeline(**p)
            with open(pipeline['csv'].path(), 'r') as f:
                print f.read()
