import sys
from pipelib import Src, GeneratedNode, needDeps
from pipelines.pnlscripts.util import TemporaryDirectory
import pipelib
import software
import plumbum
from plumbum import local, FG
from pipelines.pnlscripts.util.scripts import dwiconvert_py

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
        with software.BRAINSTools.env(self.hash_BRAINSTools):
            dwiconvert_py['-i', self.dwi.path(), '-o', self.path()] & FG

class DwiFSL(GeneratedNode):
    def __init__(self, caseid, dwi, hash_BRAINSTools):
        self.deps = [dwi]
        self.params = [hash_BRAINSTools]
        self.ext = '.nii.gz'
        GeneratedNode.__init__(self, locals())
    def build(self):
        needDeps(self)
        with software.BRAINSTools.env(self.hash_BRAINSTools):
            dwiconvert_py['-i', self.dwi.path(), '-o', self.path()] & FG

class NrrdCompare(GeneratedNode):
    def __init__(self, caseid, nrrd1, nrrd2, hash_nrrdchecker, hash_BRAINSTools):
        self.deps = [nrrd1, nrrd2]
        self.params = [hash_nrrdchecker, hash_BRAINSTools]
        self.ext = '.txt'
        GeneratedNode.__init__(self, locals())
    def build(self):
        needDeps(self)
        import software.nrrdchecker
        binarypath = software.nrrdchecker.getPath(self.hash_nrrdchecker)
        nrrdchecker = local[binarypath]
        retcode, stdout, stderr = nrrdchecker['-i', self.nrrd1.path(), '-r', self.nrrd2.path()].run(retcode=(0,1))
        with open(self.path(), 'w') as f:
            f.write(stderr)
            f.write(stdout[:-1] + ',{},{}'.format(self.caseid, self.hash_BRAINSTools))


def makePipeline(caseid
                 ,dwidicomdirPathKey='dwidicomdir'
                 ,hash_BRAINSTools='41353e8'
                 ,hash_nrrdchecker='133ad94'):

    pipeline = {'_name': "BRAINSTools DWIConvert test"}
    pipeline['dicoms'] = Src(caseid, dwidicomdirPathKey)
    pipeline['dwinrrd'] = DwiNrrd(caseid, pipeline['dicoms'], hash_BRAINSTools)
    pipeline['dwifsl'] = DwiFSL(caseid, pipeline['dicoms'], hash_BRAINSTools)
    pipeline['dwinrrdFromFSL'] = DwiNrrd(caseid, pipeline['dwifsl'], hash_BRAINSTools)
    pipeline['csv'] = NrrdCompare(caseid
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
