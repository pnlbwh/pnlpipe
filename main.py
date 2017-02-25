#!/usr/bin/env python

from plumbum import local, FG
from pnlscripts.util.scripts import alignAndCenter_py, convertdwi_py, atlas_py, fs2dwi_py
from pnlscripts.util import TemporaryDirectory
import sys
import yaml
import pickle
from pipelinelib import logfmt, Src, GeneratedNode, update, need, lookupPathKey, bracket, needDeps, getTrainingDataT1AHCCCsv, brainsToolsEnv, convertImage


class DwiXc(GeneratedNode):
    def __init__(self, caseid, dwi, bthash):
        self.deps = [dwi]
        self.opts = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        need(self, self.dwi)
        with brainsToolsEnv(self.bthash):
            convertdwi_py['-f', '-i', self.dwi.path(), '-o', self.path()] & FG
            alignAndCenter_py['-i', self.path(), '-o', self.path()] & FG


class T1wXc(GeneratedNode):
    def __init__(self, caseid, t1):
        self.deps = [t1]
        GeneratedNode.__init__(self, locals())

    def build(self):
        need(self, self.t1)
        alignAndCenter_py['-i', self.t1.path(), '-o', self.path()] & FG

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
        fs_py['-i', self.t1.path(), '-m', self.t1mask.path(), '-f', '-o',
              self.path().dirname.dirname]


class FsInDwiDirect(GeneratedNode):
    def __init__(self, caseid, fs, dwi, dwimask, bthash):
        self.deps = [fs, dwi, dwimask]
        self.opts = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self.deps)
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
        needDeps(self.deps)
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

from os.path import dirname
SRCPATHS = {'t1raw': dirname(__file__) + '/testdata/{case}-t1w.nrrd',
            't2raw': dirname(__file__) + '/testdata/{case}-t2w.nrrd',
            'dwiraw': dirname(__file__) + '/testdata/{case}-dwi.nrrd',
            't2rawmask': dirname(__file__) + '/testdata/{case}-t2mask.nrrd'}
SOFTDIR = local.path('~/soft')

if __name__ == '__main__':
    bthash = '41353e8'
    bthash = 'e13c873'
    # get paths from user
    import pipelinelib
    pipelinelib.SRCPATHS = SRCPATHS
    pipelinelib.SOFTDIR = SOFTDIR
    t1 = Src('001', 't1raw')
    t1xc = T1wXc('001', t1)
    t1mabs = T1wMaskMabs('001', t1xc, bthash)
    t2 = Src('001', 't2raw')
    t2mask = Src('001', 't2rawmask')
    # t1rigidmask = T1wMaskRigid('001', t1xc, t2, t2mask)
    # update(t1xc)
    fs = FreeSurferUsingMask('001', t1xc, t1mabs)
    dwixc = DwiXc('001', Src('001', 'dwiraw'), bthash)
    update(t1mabs)
