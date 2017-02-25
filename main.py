#!/usr/bin/env python

from plumbum import local
# from util.scripts import alignAndCenter_py
import sys
import yaml
import pickle
from pipelinelib import logfmt, Src, GeneratedNode, update, need, lookupPathKey, bracket, needDeps
import logging
logger = logging.getLogger()
# logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))
logging.basicConfig(level=logging.INFO, format=logfmt(__file__))


class T1wXc(GeneratedNode):
    def __init__(self, caseid, t1):
        self.deps = [t1]
        GeneratedNode.__init__(self, locals())

    def build(self):
        need(self, self.t1)
        # alignAndCenter_py('-i', t1.filename()
        #                     ,'-o', self.path())
        self.t1.path().copy(self.path())


class T1wMaskRigid(GeneratedNode):
    def __init__(self, caseid, t1, t2, t2mask):
        self.deps = [t1, t2, t2mask]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        self.t2.path().copy(self.path())


class T1wMaskMabs(GeneratedNode):
    def show(self):
        return self.name() + bracket(self.t1.show())

    def __init__(self, caseid, t1):
        self.deps = [t1]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        self.t1.path().copy(self.path())

class FreeSurferUsingMask(GeneratedNode):
    def __init__(self, caseid, t1, t1mask):
        self.deps = [t1, t1mask]
        Node.__init__(self, locals())
    def build(self):
        needDeps(self)
        # alignAndCenter_py('-i', t1.filename()
        #                     ,'-o', self.path())
        t1.path().copy(self.path())

from os.path import dirname
PATHS = {'t1raw': dirname(__file__) + '/testdata/{case}-t1w.nrrd',
         't2raw': dirname(__file__) + '/testdata/{case}-t2w.nrrd',
         'dwiraw': dirname(__file__) + '/testdata/{case}-dwi.nrrd',
         't2rawmask': dirname(__file__) + '/testdata/{case}-t2mask.nrrd'}

if __name__ == '__main__':
    # get paths from user
    import pipelinelib
    pipelinelib.PATHS = PATHS
    t1 = Src('001', 't1raw')
    t1xc = T1wXc('001', t1)
    t1mabs = T1wMaskMabs('001', t1xc)
    t2 = Src('001', 't2raw')
    t2mask = Src('001', 't2rawmask')
    t1rigidmask = T1wMaskRigid('001', t1xc, t2, t2mask)
    # update(t1xc)
    update(t1rigidmask)
