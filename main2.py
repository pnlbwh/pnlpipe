from yaml import load, dump
from plumbum import local
from util.scripts import alignAndCenter_py
import sys
from os.path import getmtime
from collections import namedtuple


T1wGiven = namedtuple('T1wGiven', 'key caseid')
T1wXc = namedtuple('T1wXc', 'key caseid')
# T1w = namedtuple('T1w', 't1type caseid')

def makeNode(mytuple):
    nodeType = type(mytuple).__name__
    thisModule = sys.modules[__name__]
    nodeClass = getattr(thisModule, nodeType)
    return nodeClass(mytuple)


T1wGiven = namedtuple('T1wGiven', 'pathKey')
T1wXc = namedtuple('T1wXc', 't1key')
class T1w(Node):
    def path(self):
        if tupname(self.typ) == 'T1wGiven':
             return local.path(paths[self.t1type.pathsKey])
        elif tupname(self.typ) == 'T1wXC':
            return outdir / self.caseid / 'T1w-' + str(self.typ) + '.nrrd'

    def show(self):
        return 'T1w-' + str(self.nodeType)

    def __init__(self, caseid, t1key):
        self.kwargs = locals()
        Node.__init__(self, locals())

    def build(self):
        if tupname(self.t1type) == 'T1wGiven':
            pass
        elif tupname(self.t1key) == 'T1wXc':
            t1 = T1w(self.caseid, self.t1key.t1key)
            self.need(t1)
            alignAndCenter_py('-i', t1.filename()
                              ,'-o', self.filename())


def tupname(atuple):
    return type(atuple).__name__
