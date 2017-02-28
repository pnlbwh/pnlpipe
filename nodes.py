#!/usr/bin/env python
from plumbum import local, FG, cli
from pnlscripts.util.scripts import alignAndCenter_py, convertdwi_py, atlas_py, fs2dwi_py, eddy_py
from pnlscripts.util import TemporaryDirectory
import sys
import yaml
import pickle
from pipelinelib import logfmt, Src, GeneratedNode, update, need, lookupPathKey, bracket, needDeps, getTrainingDataT1AHCCCsv, brainsToolsEnv, convertImage, OUTDIR, log, ukftractographyEnv

defaultUkfParams = [("Ql","70")
                    ,("Qm","0.001")
                    ,("Rs","0.015")
                    ,("numTensor","2")
                    ,("recordLength","1.7")
                    ,("seedFALimit","0.18")
                    ,("seedsPerVoxel","10")
                    ,("stepLength","0.3")]

def formatParams(paramsList):
     formatted = [['--'+key, val] for key, val in paramsList]
     return [item for pair in formatted for item in pair]

class DwiEd(GeneratedNode):
    """ Eddy current correction. Accepts nrrd only. """
    def __init__(self, caseid, dwi, bthash):
        self.deps = [dwi]
        self.opts = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with brainsToolsEnv(self.bthash):
            eddy_py['-i', self.dwi.path(), '-o', self.path()] & FG

class DwiXc(GeneratedNode):
    """ Axis align and center a dWI. Accepts nrrd or nifti. """
    def __init__(self, caseid, dwi, bthash):
        self.deps = [dwi]
        self.opts = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with brainsToolsEnv(self.bthash):
            convertdwi_py['-f', '-i', self.dwi.path(), '-o', self.path()] & FG
            alignAndCenter_py['-i', self.path(), '-o', self.path()] & FG


class DwiMaskHcpBet(GeneratedNode):
    def __init__(self, caseid, dwi):
        self.deps = [dwi]
        GeneratedNode.__init__(self, locals())

    def build(self):
         needDeps(self)
         from plumbum.mcd import bet
         with TemporaryDirectory() as tmpdir:
             tmpdir = local.path(tmpdir)
             nii = tmpdir / 'dwi.nii.gz'
             bet[nii, tmpdir / 'dwi','-m','-f','0.1']
             convertImage(tmpdir / 'dwi_mask.nii.gz', self.path())

class UkfDefault(GeneratedNode):
    def __init__(self, caseid, dwi, dwimask, ukfhash):
        self.deps = [dwi]
        self.opts = [ukfhash]
        GeneratedNode.__init__(self, locals())

    def build(self):
         needDeps(self)
         with ukftractographyEnv(self.ukfhash), TemporaryDirectory() as tmpdir:
             tmpdir = local.path(tmpdir)
             tmpdwi = tmpdir / 'dwi.nrrd'
             tmpdwimask = tmpdir / 'dwimask.nrrd'
             convertdwi_py('-i', self.dwi.path(), '-o', tmpdwi)
             convertImage(self.dwimask.path(), tmpdwimask)
             params = ['--dwiFile', tmpdwi
                       ,'--maskFile', tmpdwimask
                       ,'--seedsFile', tmpdwimask
                       ,'--recordTensors'
                       ,'--tracts', self.path()] + formatParams(defaultUkfParams)
             UKFTractography(*params)


class StrctXc(GeneratedNode):
    def __init__(self, caseid, strct):
        self.deps = [strct]
        GeneratedNode.__init__(self, locals())

    def build(self):
        need(self, self.strct)
        alignAndCenter_py['-i', self.strct.path(), '-o', self.path()] & FG

# class T1wMaskRigid(GeneratedNode):
#     def __init__(self, caseid, t1, t2, t2mask):
#         self.deps = [t1, t2, t2mask]
#         GeneratedNode.__init__(self, locals())
#     def build(self):
#         needDeps(self)
#         self.t2.path().copy(self.path())


class T1wMaskMabs(GeneratedNode):
    def __init__(self, caseid, t1, bthash):
        self.deps = [t1]
        self.opts = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        log.info(' Now run MABS using pnlscripts/atlas.py')
        with TemporaryDirectory() as tmpdir, brainsToolsEnv(self.bthash):
            tmpdir = local.path(tmpdir)
            # antsRegistration can't handle a non-conventionally named file, so
            # we need to pass in a conventionally named one
            tmpt1 = tmpdir / ('t1'+''.join(self.t1.path().suffixes))
            from plumbum.cmd import ConvertBetweenFileFormats
            ConvertBetweenFileFormats[self.t1.path(), tmpt1] & FG
            atlas_py['--mabs', '-t', tmpt1, '-o', tmpdir, 'csv',
                     getTrainingDataT1AHCCCsv()] & FG
            (tmpdir / 'mask.nrrd').copy(self.path())


class FreeSurferUsingMask(GeneratedNode):
    def __init__(self, caseid, t1, t1mask):
        self.deps = [t1, t1mask]
        GeneratedNode.__init__(self, locals())

    def path(self):
        return OUTDIR / self.caseid / self.show() / 'mri/wmparc.mgz'

    def build(self):
        needDeps(self)
        from pnlscripts.util.scripts import fs_py
        fs_py['-i', self.t1.path(), '-m', self.t1mask.path(), '-f', '-o',
              self.path().dirname.dirname] & FG


class FsInDwiDirect(GeneratedNode):
    def __init__(self, caseid, fs, dwi, dwimask, bthash):
        self.deps = [fs, dwi, dwimask]
        self.opts = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        fssubjdir = self.fs.path().dirname.dirname
        with TemporaryDirectory() as tmpdir, brainsToolsEnv(self.bthash):
            tmpdir = local.path(tmpdir)
            tmpoutdir = tmpdir / (self.caseid + '-fsindwi')
            fs2dwi_py('-f', fssubjdir, '-t', self.dwi.path(), '-m',
                       self.dwimask.path(), '-o', tmpoutdir, 'direct')

class UKFTractographyDefault(GeneratedNode):
    def __init__(self, caseid, dwi, dwimask, ukfhash):
        self.deps = [dwi, dwimask]
        self.opts = [ukfhash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with TemporaryDirectory() as tmpdir, brainsToolsEnv(self.bthash):
            tmpdir = local.path(tmpdir)
            dwi = tmpdir / 'dwi.nrrd'
            dwimask = tmpdir / 'dwimask.nrrd'
            convertdwi_py('-i', self.dwi.path()
                          ,'-o', dwi)
            convertImage(self.dwimask.path(), dwimask)
            UKFTractography['--dwiFile', dwinrrd
                            ,'--maskFile', dwimasknrrd
                            ,'--seedsFile', dwimasknrrd
                            ,'--recordTensors'
                            ,'--tracts', self.path()] & FG
