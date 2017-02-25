#!/usr/bin/env python

from plumbum import local, FG
from pnlscripts.util.scripts import alignAndCenter_py, convertdwi_py
import sys
import yaml
import pickle
from pipelinelib import logfmt, Src, GeneratedNode, update, need, lookupPathKey, bracket, needDeps, btPath

# def btPath(hash):
#     return [SOFTDIR / ('BRAINSTools-bin-' + hash)] + \
#         local.env.path
class DwiXc(GeneratedNode):
    def __init__(self, caseid, dwi, bthash):
        self.deps = [dwi]
        self.opts = [bthash]
        GeneratedNode.__init__(self, locals())
    def build(self):
        need(self, self.dwi)
        with btPath(self.bthash):
        # local.env.path.insert(0, btPath(self.bthash))
            convertdwi_py['-f', '-i', self.dwi.path(), '-o', self.path()] & FG
            alignAndCenter_py['-i', self.path()
                            ,'-o', self.path()] & FG


class T1wXc(GeneratedNode):
    def __init__(self, caseid, t1):
        self.deps = [t1]
        GeneratedNode.__init__(self, locals())
    def build(self):
        need(self, self.t1)
        alignAndCenter_py['-i', self.t1.path()
                            ,'-o', self.path()] & FG


class T1wMaskRigid(GeneratedNode):
    def __init__(self, caseid, t1, t2, t2mask):
        self.deps = [t1, t2, t2mask]
        GeneratedNode.__init__(self, locals())
    def build(self):
        needDeps(self)
        self.t2.path().copy(self.path())


class T1wMaskMabs(GeneratedNode):
    def __init__(self, caseid, t1):
        self.deps = [t1]
        GeneratedNode.__init__(self, locals())
    def build(self):
        needDeps(self)
        self.t1.path().copy(self.path())

class FreeSurferUsingMask(GeneratedNode):
    def __init__(self, caseid, t1, t1mask):
        self.deps = [t1, t1mask]
        GeneratedNode.__init__(self, locals())
    def build(self):
        needDeps(self)
        # alignAndCenter_py('-i', t1.filename()
        #                     ,'-o', self.path())
        self.t1mask.path().copy(self.path())

from os.path import dirname
PATHS = {'t1raw': dirname(__file__) + '/testdata/{case}-t1w.nrrd',
         't2raw': dirname(__file__) + '/testdata/{case}-t2w.nrrd',
         'dwiraw': dirname(__file__) + '/testdata/{case}-dwi.nrrd',
         't2rawmask': dirname(__file__) + '/testdata/{case}-t2mask.nrrd'
          }
SOFTDIR = local.path('~/soft')

if __name__ == '__main__':
    bthash = '41353e8'
    bthash = 'e13c873'
    # get paths from user
    import pipelinelib
    pipelinelib.PATHS = PATHS
    pipelinelib.SOFTDIR = SOFTDIR
    t1 = Src('001', 't1raw')
    t1xc = T1wXc('001', t1)
    t1mabs = T1wMaskMabs('001', t1xc)
    t2 = Src('001', 't2raw')
    t2mask = Src('001', 't2rawmask')
    t1rigidmask = T1wMaskRigid('001', t1xc, t2, t2mask)
    # update(t1xc)
    fs = FreeSurferUsingMask('001', t1xc, t1mabs)
    dwixc = DwiXc('001', Src('001', 'dwiraw'), bthash)
    update(dwixc)
