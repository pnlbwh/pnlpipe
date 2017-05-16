import sys
from pipelib import Src, GeneratedNode, needDeps
from pipelines.pnlscripts.util import TemporaryDirectory
import pipelib
import software
import plumbum
from plumbum import local, FG, TEE
from pipelines.pnlscripts.util.scripts import dwiconvert_py
import pandas as pd

DEFAULT_TARGET = 'csv'

def isFsl(f):
    return '.nii' in f.suffixes

def isNrrd(f):
    return '.nhdr' in f.suffixes or '.nrrd' in f.suffixes

class DwiNrrd(GeneratedNode):
    ext = '.nrrd'
    def __init__(self, caseid, dwi, hash_BRAINSTools, DWIConvert_switches):
        self.deps = [dwi]
        self.params = [DWIConvert_switches, hash_BRAINSTools]
        # self.ext = '.nrrd'
        GeneratedNode.__init__(self, locals())
    def build(self):
        needDeps(self)
        with software.BRAINSTools.env(self.hash_BRAINSTools):
            dwiconvert_py['-i', self.dwi.path(), '-o', self.path(), '--switches', self.DWIConvert_switches] & FG

class DwiFSL(DwiNrrd):
    ext = '.nii.gz'

# class DwiFSL(GeneratedNode):
#     def __init__(self, caseid, dwi, DWIConvert_switches, hash_BRAINSTools):
#         self.deps = [dwi]
#         self.params = [DWIConvert_switches, hash_BRAINSTools]
#         self.ext = '.nii.gz'
#         GeneratedNode.__init__(self, locals())
#     def build(self):
#         needDeps(self)
#         with software.BRAINSTools.env(self.hash_BRAINSTools):
#             dwiconvert_py['-i', self.dwi.path(), '-o', self.path(), '--switches', self.DWIConvert_switches] & FG

class NrrdCompareCsv(GeneratedNode):
    def __init__(self, caseid, nrrds, hash_nrrdchecker, hash_BRAINSTools):
        self.deps = nrrds
        self.params = [hash_nrrdchecker, hash_BRAINSTools]
        self.ext = '.csv'
        GeneratedNode.__init__(self, locals())
    def build(self):
        needDeps(self)
        import software.nrrdchecker
        binarypath = software.nrrdchecker.getPath(self.hash_nrrdchecker)
        nrrdchecker = local[binarypath]
        #retcode, stdout, stderr = nrrdchecker['-i', self.nrrd1.path(), '-r', self.nrrd2.path()].run(retcode=(0,1), FG=True)
        with TemporaryDirectory() as tmpdir:
            tmpcsv = tmpdir / 'out.csv'
            nrrdchecker['-i', self.nrrd1.path(), '-r', self.nrrd2.path(), '-o', tmpcsv] & FG
            csv = pd.read_csv(tmpcsv)
        csv['caseid'] = self.caseid
        csv['hash_BRAINSTools'] = self.hash_BRAINSTools
        csv.to_csv(self.path(), index=False)



def makePipeline(caseid
                 ,dwidicomdirPathKey='dwidicomdir'
                 ,hash_BRAINSTools='2d5eccb'
                 ,hash_nrrdchecker='1011097'):

    pipeline = {'_name': "BRAINSTools DWIConvert test"}
    pipeline['dicoms'] = Src(caseid, dwidicomdirPathKey)
    pipeline['dwinrrd'] = DwiNrrd(caseid, pipeline['dicoms'], hash_BRAINSTools, "--useIdentityMeaseurementFrame")
    pipeline['dwifsl'] = DwiFSL(caseid, pipeline['dicoms'], hash_BRAINSTools, "--useIdentityMeaseurementFrame")
    pipeline['dwinrrdFromFSL'] = DwiNrrd(caseid, pipeline['dwifsl'], hash_BRAINSTools, "--useIdentityMeaseurementFrame")
    pipeline['dwinrrdBMatrix'] = DwiNrrd(caseid, pipeline['dicoms'], hash_BRAINSTools, "--useIdentityMeaseurementFrame --useBMatrixGradientDirections")

    pipeline['csv'] = NrrdCompareCsv(caseid
                                 ,[pipeline['dwinrrd'], pipeline['dwinrrdFromFSL'], pipeline['dwinrrdBMatrix']]
                                 , hash_nrrdchecker
                                 , hash_BRAINSTools)
    return pipeline


def status(combos):
    for combo in combos:
        for caseid in combo['caseids']:
            pipeline = makePipeline(caseid, **combo['paramCombo'])
            with open(pipeline['csv'].path(), 'r') as f:
                print f.read()
