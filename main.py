#!/usr/bin/env python

from plumbum import local
# from util.scripts import alignAndCenter_py
import sys
from os.path import getmtime
import yaml
import pickle
from pipelinelib import logfmt, SourceNode, GeneratedNode, update, need, lookupPathKey
import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))


class T1wXc(GeneratedNode):
    def show(self):
        return 'T1wXc-' + self.t1.show()
    def __init__(self, caseid, t1):
        GeneratedNode.__init__(self, locals())
    def build(self):
        need(self, self.t1)
        # alignAndCenter_py('-i', t1.filename()
        #                     ,'-o', self.path())
        self.t1.path().copy(self.path())


class T1wMaskMabs(GeneratedNode):
    def show(self):
        return self.__class__.__name__ + '-' + self.t1.show()
    def __init__(self, caseid, t1):
        GeneratedNode.__init__(self, locals())
    def build(self):
        need(self, self.t1)
        self.t1.path().copy(self.path())

# class FreeSurferUsingMask(Node):
#     def path(self):
#         return OUTDIR / self.caseid / (self.show() + '-' + self.caseid + '.nrrd')
#     def show(self):
#         return self.__class__.__name__ + '-' + self.t1.show()
#     def __init__(self, caseid, t1, t1mask):
#         self.t1=t1
#         Node.__init__(self, locals())
#     def build(self):
#         need(self, t1)
#         # alignAndCenter_py('-i', t1.filename()
#         #                     ,'-o', self.path())
#         t1.path().copy(self.path())


if __name__ == '__main__':
    t1 = SourceNode('001', 't1raw')
    t1xc = T1wXc('001', t1)
    t1mask = T1wMaskMabs('001', t1xc)
    # update(t1xc)
    update(t1mask)
