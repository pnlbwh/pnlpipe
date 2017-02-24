#!/usr/bin/env python

from plumbum import local
# from util.scripts import alignAndCenter_py
import sys
from os.path import getmtime
import yaml
import pickle
# from abc import abstractmethod, abstractproperty

def logfmt(scriptname):
    return '%(asctime)s ' + scriptname + ' %(levelname)s  %(message)s'
import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))

paths = { 't1' : 'testdata/{case}-t1w.nrrd'}
outdir = local.path('_data')

# def makeNode(mytuple):
#     nodeType = type(mytuple).__name__
#     thisModule = sys.modules[__name__]
#     nodeClass = getattr(thisModule, nodeType)
#     return nodeClass(*mytuple)

class Node(object):
    def __init__(self, kwargs):
        # self.key = namedtuple(self.__class__.__name__, args.keys())(*args.values)
        # self.typ = kwargs['typ']
        self.db = {'value' : None, 'deps' : {}}
        # self.kwargs = kwargs
        self.caseid = kwargs['caseid']

def dbfile(node):
    return outdir / 'db' / node.path().name

def readDB(node):
    if not dbfile(node).exists():
        return None
    with open(dbfile(node), 'r') as f:
        return yaml.load(f)

def readCurrentValue(node):
    mtime = node.path().stat().st_mtime
    return mtime

def need(parentNode, childNode):
    val = update(childNode)
    parentNode.db['deps'][pickle.dumps(childNode)] = val

def buildNode(node):
    node.build()
    db = node.db
    db['value'] = readCurrentValue(node)
    del node.db
    with open(dbfile(node),'w') as f:
        yaml.dump(db, f)
    return db['value']

def update(node):
    db = readDB(node)
    currentValue = None if not node.path().exists() else readCurrentValue(node)
    nodeChanged = False
    if db == None:
        logging.info(node.path() + ': has no db, so building')
        return buildNode(node)
    if db['value'] != currentValue:
        logging.info(node.path() + ': it\'s value has changed, so rebuilding')
        return buildNode(node)
    # else, node is up to date, now check deps
    depsHaveChanged = False
    for depKey, depVal in db['deps'].items():
        depNode = pickle.loads(depKey)
        newDepVal = readCurrentValue(depNode)
        depsHaveChanged = True if depVal != newDepVal else False
    if depsHaveChanged:
        logging.info(node.path() + ': deps changed, so rebuilding')
        return buildNode(node)
    logging.info(node.path() + ': node or its dependencies haven\'t changed, so doing nothing')
    return currentValue

class T1wXc(Node):
    def path(self):
        return outdir / self.caseid / (self.show() + '-' + self.caseid + '.nrrd')

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
        try:
            pathPattern = local.path(paths.get(self.pathsKey))
            filepath = local.path(pathPattern.replace('{case}', self.caseid))
            return filepath
        except KeyError:
            print(self.pathsKey + " not in paths")
            sys.exit(1)

    def show(self):
        return 'T1wGiven-'+self.pathsKey

    def build(self):
        pass


if __name__ == '__main__':
    t1xc = T1wXc('001', T1wGiven('001', 't1'))
    t1 = T1wGiven('001', 't1')
    update(t1xc)
