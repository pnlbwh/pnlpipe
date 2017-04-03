import sys
from pipelib import Src, GeneratedNode, needDeps
from pipelines.pnlscripts.util import TemporaryDirectory
import pipelib
import software
import plumbum
from plumbum import local, FG

DEFAULT_TARGET = 'dwinrrdFromFSL'

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
            from plumbum.cmd import DWIConvert, unu
            if self.dwi.path().is_dir():
                DWIConvert['--inputDicomDirectory', self.dwi.path()
                        ,'-o', self.path()] & FG
                unu['save','-e','gzip','-f','nrrd','-i',self.path(),'-o',self.path()] & FG
            elif isFsl(self.dwi.path()):
                DWIConvert['--conversionMode', 'FSLToNrrd'
                           ,'--inputVolume', self.dwi.path()
                           ,'--allowLossyConversion'
                           ,'--inputBValues', self.dwi.path().with_suffix('.bval', depth=2)
                           ,'--inputBVectors', self.dwi.path().with_suffix('.bvec', depth=2)
                           ,'-o', self.path()] & FG
                unu['save','-e','gzip','-f','nrrd','-i',self.path(),'-o',self.path()] & FG
            else:
                raise Exception("{}: Input dwi has to be a directory of dicoms or a nifti file.".format(self.__class__.__name__))

class DwiFSL(GeneratedNode):
    def __init__(self, caseid, dwi, hash_BRAINSTools):
        self.deps = [dwi]
        self.params = [hash_BRAINSTools]
        self.ext = '.nii.gz'
        GeneratedNode.__init__(self, locals())
    def build(self):
        needDeps(self)
        with software.BRAINSTools.env(self.hash_BRAINSTools):
            from plumbum.cmd import DWIConvert
            if self.dwi.path().is_dir():
                DWIConvert['--inputDicomDirectory', self.dwi.path()
                        ,'-o', self.path()] & FG
            elif isFsl(self.dwi.path()):
                DWIConvert['--conversionMode', 'NrrdToFSL'
                           ,'--inputVolume', self.dwi.path()
                           ,'--allowLossyConversion'
                           ,'-o', self.path()] & FG
            else:
                raise Exception("{}: Input dwi has to be a directory of dicoms or a nifti file.".format(self.__class__.__name__))


def makePipeline(caseid,
                 dwidicomdirPathKey='dwidicomdir',
                 hash_BRAINSTools='41353e8'):

    pipeline = {'_name': "BRAINSTools DWIConvert test"}
    pipeline['dicoms'] = Src(caseid, dwidicomdirPathKey)
    pipeline['dwinrrd'] = DwiNrrd(caseid, pipeline['dicoms'], hash_BRAINSTools)
    pipeline['dwifsl'] = DwiFSL(caseid, pipeline['dicoms'], hash_BRAINSTools)
    pipeline['dwinrrdFromFSL'] = DwiNrrd(caseid, pipeline['dwifsl'], hash_BRAINSTools)
    return pipeline
