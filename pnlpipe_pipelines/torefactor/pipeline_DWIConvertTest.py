import sys
from pnlpipe_pipelines.pnl import NrrdOutput, NiftiOutput
from pnlpipe_lib import node, InputKey, AutoOutput
from pnlpipe_pipelines.pnlscripts.util import TemporaryDirectory
import pnlpipe_software
import plumbum
from plumbum import local, FG, TEE
from pnlpipe_pipelines.pnlscripts.util.scripts import dwiconvert_py
import pandas as pd
if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO
import pnlpipe_software.nrrdchecker

DEFAULT_TARGET = 'csv'


def isFsl(f):
    return '.nii' in f.suffixes


def isNrrd(f):
    return '.nhdr' in f.suffixes or '.nrrd' in f.suffixes


@node(params=['hash_BRAINSTools'], deps=['dwi'])
class DwiNrrd(NrrdOutput):
    def static_build(self):
        with pnlpipe_software.BRAINSTools.env(self.hash_BRAINSTools):
            dwiconvert_py['-i', self.dwi, '-o', self.output()] & FG


@node(params=['hash_BRAINSTools'], deps=['dwi'])
class DwiFSL(NiftiOutput):
    def static_build(self):
        with pnlpipe_software.BRAINSTools.env(self.params['hash_BRAINSTools']):
            dwiconvert_py['-i', self.dwi, '-o', self.output()] & FG


@node(
    params=['caseid', 'hash_nrrdchecker', 'hash_BRAINSTools'],
    deps=['nrrd1', 'nrrd2'])
class NrrdCompareCsv(AutoOutput):
    @property
    def ext(self):
        return '.csv'

    def static_build(self):
        binarypath = pnlpipe_software.nrrdchecker.get_path(
            self.hash_nrrdchecker)
        nrrdchecker = local[binarypath]
        stdout = nrrdchecker('-i', self.nrrd1, '-r', self.nrrd2)
        csv = pd.read_csv(StringIO(stdout))
        csv['caseid'] = self.caseid
        csv['hash_BRAINSTools'] = self.hash_BRAINSTools
        csv.to_csv(self.output(), index=False)


def make_pipeline(caseid,
                 dicomKey='dwidicomdir',
                 hash_BRAINSTools='41353e8',
                 hash_nrrdchecker='133ad94'):

    pipeline = {'_name': "BRAINSTools DWIConvert test"}
    pipeline['dicoms'] = InputKey([dicomKey, caseid])
    pipeline['dwinrrd'] = DwiNrrd([hash_BRAINSTools], {'dwi': pipeline['dicoms']})
    pipeline['dwifsl'] = DwiFSL(
        params=[hash_BRAINSTools], deps=[pipeline['dicoms']])
    pipeline['dwinrrdFromFSL'] = DwiNrrd(
        params=[hash_BRAINSTools], deps=[pipeline['dwifsl']])
    pipeline['csv'] = NrrdCompareCsv(
        params=[caseid, hash_BRAINSTools, hash_nrrdchecker],
        deps=[pipeline['dwinrrd'], pipeline['dwinrrdFromFSL']])
    return pipeline


def status(combos):
    for combo in combos:
        for p in combo['paramPoints']:
            pipeline = make_pipeline(**p)
            with open(pipeline['csv'].path(), 'r') as f:
                print f.read()
