import sys
from pnlpipe import Src, GeneratedNode, needDeps
from pp_pipelines.pnlscripts.util import TemporaryDirectory
import pnlpipe
import pp_software
import plumbum
from plumbum import local, FG, TEE
from pp_pipelines.pnlscripts.util.scripts import dwiconvert_py
import pandas as pd
if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO


DEFAULT_TARGET = 'csv'

def isFsl(f):
    return '.nii' in f.suffixes

def isNrrd(f):
    return '.nhdr' in f.suffixes or '.nrrd' in f.suffixes

class DwiNrrd(GeneratedNode):
    def __init__(self, caseid, dwi, hash_BRAINSTools):
        self.deps = [dwi]
        self.params = [hash_BRAINSTools]
        self.ext = '.nrrd'
        GeneratedNode.__init__(self, locals())
    def build(self):
        needDeps(self)
        with pp_software.BRAINSTools.env(self.hash_BRAINSTools):
            dwiconvert_py['-i', self.dwi.path(), '-o', self.path()] & FG

class DwiFSL(GeneratedNode):
    def __init__(self, caseid, dwi, hash_BRAINSTools):
        self.deps = [dwi]
        self.params = [hash_BRAINSTools]
        self.ext = '.nii.gz'
        GeneratedNode.__init__(self, locals())
    def build(self):
        needDeps(self)
        with pp_software.BRAINSTools.env(self.hash_BRAINSTools):
            dwiconvert_py['-i', self.dwi.path(), '-o', self.path()] & FG

class NrrdCompareCsv(GeneratedNode):
    def __init__(self, caseid, nrrd1, nrrd2, hash_nrrdchecker, hash_BRAINSTools):
        self.deps = [nrrd1, nrrd2]
        self.params = [hash_nrrdchecker, hash_BRAINSTools]
        self.ext = '.csv'
        GeneratedNode.__init__(self, locals())
    def build(self):
        needDeps(self)
        import pp_software.nrrdchecker
        binarypath = pp_software.nrrdchecker.getPath(self.hash_nrrdchecker)
        nrrdchecker = local[binarypath]
        #retcode, stdout, stderr = nrrdchecker['-i', self.nrrd1.path(), '-r', self.nrrd2.path()].run(retcode=(0,1), FG=True)
        stdout = nrrdchecker('-i', self.nrrd1.path(), '-r', self.nrrd2.path())
        csv = pd.read_csv(StringIO(stdout))
        csv['caseid'] = self.caseid
        csv['hash_BRAINSTools'] = self.hash_BRAINSTools
        csv.to_csv(self.path(), index=False)


def makePipeline(caseid
                 ,dwidicomdirPathKey='dwidicomdir'
                 ,hash_BRAINSTools='41353e8'
                 ,hash_nrrdchecker='133ad94'):

    pipeline = {'_name': "BRAINSTools DWIConvert test"}
    pipeline['dicoms'] = Src(caseid, dwidicomdirPathKey)
    pipeline['dwinrrd'] = DwiNrrd(caseid, pipeline['dicoms'], hash_BRAINSTools)
    pipeline['dwifsl'] = DwiFSL(caseid, pipeline['dicoms'], hash_BRAINSTools)
    pipeline['dwinrrdFromFSL'] = DwiNrrd(caseid, pipeline['dwifsl'], hash_BRAINSTools)
    pipeline['csv'] = NrrdCompareCsv(caseid
                                 , pipeline['dwinrrd']
                                 , pipeline['dwinrrdFromFSL']
                                 , hash_nrrdchecker
                                 , hash_BRAINSTools)
    return pipeline


def status(combos):
    for combo in combos:
        for p in combo['paramPoints']:
            pipeline = makePipeline(**p)
            with open(pipeline['csv'].path(), 'r') as f:
                print f.read()
