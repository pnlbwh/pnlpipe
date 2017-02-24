from plumbum import local
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

OUTDIR = local.path('_data')
DBDIR = local.path('_data/db')


class Node(object):
    def __init__(self, kwargs):
        self.db = {'value': None, 'deps': {}}
        for key, val in kwargs.items():
            if key == 'self':
                continue
            self.__setattr__(key, val)
        # self.caseid = kwargs['caseid']
        if not hasattr(self, 'deps'):
            self.deps = []
        if not hasattr(self, 'opts'):
            self.opts = []
    def name(self):
        return self.__class__.__name__
    def show(self):
        depsString = ','.join([d.show() for d in self.deps] + self.opts)
        return self.name() + bracket(depsString)

class GeneratedNode(Node):
    def path(self):
        return OUTDIR / self.caseid / (self.show() + '-' + self.caseid + '.nrrd')

class Src(Node):
    def __init__(self, caseid, pathsKey):
        self.deps=[]
        self.opts=[pathsKey]
        Node.__init__(self, locals())
    def path(self):
        return lookupPathKey(self.pathsKey, self.caseid, PATHS)
    def build(self):
        pass


def lookupPathKey(key, caseid, pathsDict):
    try:
        pathPattern = pathsDict[key]
        filepath = local.path(pathPattern.replace('{case}', caseid))
        if not filepath.exists():
            logging.error(
                str(filepath) + ' does not exist, maybe a typo in PATHS?')
            sys.exit(1)
        return filepath
    except KeyError:
        logging.error("Key '{}' not in PATHS, maybe a typo?".format(key))
        sys.exit(1)


def dbfile(node):
    return DBDIR / node.path().name


def readDB(node):
    if not dbfile(node).exists():
        return None
    with open(dbfile(node), 'r') as f:
        return yaml.load(f)


def readCurrentValue(node):
    logging.debug('readCurrentValue: ' + node.__class__.__name__ +
                      ' path: ' + str(node.path()))
    mtime = node.path().stat().st_mtime
    return mtime


def need(parentNode, childNode):
    logging.info('need: ' + parentNode.name() + ' needs ' + childNode.name() +
                 ', updating')
    val = update(childNode)
    parentNode.db['deps'][pickle.dumps(childNode)] = (childNode.path().__str__(), val)


def buildNode(node):
    node.build()
    db = node.db
    db['value'] = readCurrentValue(node)
    del node.db
    with open(dbfile(node), 'w') as f:
        yaml.dump(db, f)
    return db['value']


def update(node):
    db = readDB(node)
    currentValue = None if not node.path().exists() else readCurrentValue(node)
    nodeChanged = False
    if db == None:
        logging.info(node.path() + ': doesn\'t exist (has no db), so building')
        return buildNode(node)
    if db['value'] != currentValue:
        logging.info(node.path() + ': it\'s value has changed, so rebuilding')
        return buildNode(node)
    # else, node is up to date, now check deps
    depsHaveChanged = False
    for depKey, (_, depVal) in db['deps'].items():
        depNode = pickle.loads(depKey)
        newDepVal = readCurrentValue(depNode)
        depsHaveChanged = True if depVal != newDepVal else False
    if depsHaveChanged:
        logging.info(node.path() + ': deps changed, so rebuilding')
        return buildNode(node)
    logging.info(node.path() +
                 ': it or its dependencies haven\'t changed, so doing nothing')
    return currentValue

def bracket(s):
    return '(' + s + ')'
