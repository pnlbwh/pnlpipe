#!/usr/bin/env python

from plumbum import local
# from util.scripts import alignAndCenter_py
import sys
from os.path import getmtime
import yaml
import pickle
import pipelinelib
from pipelinelib import logfmt, Node, update, need, lookupPathKey

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))

from os.path import dirname
PATHS = { 't1' : dirname(__file__) + '/testdata/{case}-t1w.nrrd'}
OUTDIR = local.path('_data')

class T1wXc(Node):
    def path(self):
        return OUTDIR / self.caseid / (self.show() + '-' + self.caseid + '.nrrd')
    def show(self):
        return 'T1wXc-' + self.t1.show()
    def __init__(self, caseid, t1):
        self.t1=t1
        Node.__init__(self, locals())
    def build(self):
        need(self, t1)
        # alignAndCenter_py('-i', t1.filename()
        #                     ,'-o', self.path())
        t1.path().copy(self.path())

class T1wGiven(Node):
    def __init__(self, caseid, pathsKey):
        self.pathsKey = pathsKey
        Node.__init__(self, locals())
    def path(self):
        return lookupPathKey(self.pathsKey, self.caseid, PATHS)
    def show(self):
        return 'T1wGiven-'+self.pathsKey
    def build(self):
        pass

# class FreeSurferUsingMask(Node):

if __name__ == '__main__':
    t1 = T1wGiven('001', 't1')
    t1xc = T1wXc('001', t1)
    update(t1xc)
