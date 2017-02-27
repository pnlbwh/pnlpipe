from plumbum import local
import sys
import yaml
import pickle
import hashlib
# from abc import abstractmethod, abstractproperty

from os.path import basename
def logfmt(scriptname):
    return '%(asctime)s ' + basename(scriptname) + ' %(levelname)s  %(message)s'


import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))
# logging.basicConfig(level=logging.INFO, format=logfmt(__file__))
from python_log_indenter import IndentedLoggerAdapter
log = IndentedLoggerAdapter(logger, indent_char='.')


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
        return OUTDIR / self.caseid / (
            self.show() + '-' + self.caseid + '.nrrd')


class Src(Node):
    def __init__(self, caseid, pathsKey):
        self.deps = []
        self.opts = [pathsKey]
        Node.__init__(self, locals())

    def path(self):
        return lookupPathKey(self.pathsKey, self.caseid, INPUT_PATH_PATTERNS)

    def build(self):
        pass


def lookupPathKey(key, caseid, pathsDict):
    try:
        pathPattern = pathsDict[key]
        filepath = local.path(pathPattern.replace('{case}', caseid))
        if not filepath.exists():
            log.error(
                str(filepath) + ' does not exist, maybe a typo in PATHS?')
            sys.exit(1)
        return filepath
    except KeyError:
        log.error("Key '{}' not in PATHS, maybe a typo?".format(key))
        sys.exit(1)


def readHash(filepath):
    BLOCKSIZE = 65536
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()


def dbfile(node):
    return DBDIR / node.path().name


def readDB(node):
    if not dbfile(node).exists():
        return None
    with open(dbfile(node), 'r') as f:
        return yaml.load(f)


def readCurrentValue(node):
    log.debug('readCurrentValue: ' + node.__class__.__name__ + ' path: ' +
                  str(node.path()))
    mtime = node.path().stat().st_mtime
    return mtime


def need(parentNode, childNode):
    log.debug(' need: {} needs {}, update'.format(parentNode.show(),
                                                    childNode.show()))
    val = update(childNode)
    parentNode.db['deps'][pickle.dumps(childNode)] = (
        childNode.path().__str__(), val)


def needDeps(node):
    for depNode in node.deps:
        need(node, depNode)


# def needDeps(node, changedDeps=[]):
#     for depNode in node.deps:
#         if depNode not in changedDeps:
#             logging.debug('needDeps: {} already up to date, ignoring'.format(depNode.show()))
#             continue
#         need(node, depNode)


def buildNode(node):
    node.build()
    db = node.db
    db['value'] = readCurrentValue(node)
    del node.db
    with open(dbfile(node), 'w') as f:
        yaml.dump(db, f)
    log.info(' Built, recorded mtime and md5 hash').sub()
    return db['value']


def update(node):
    log.info(' Update {} ({})'.format(node.show(), node.path())).add()

    log.info(' Check if node exists or has been modified')
    db = readDB(node)
    currentValue = None if not node.path().exists() else readCurrentValue(node)
    nodeChanged = False
    rebuild = False
    if db == None:
        log.info(' doesn\'t exist (has no db), build'.format(node.path()))
        rebuild = True
    elif currentValue == None:
        log.info(' File missing ({}), rebuild'.format(node.path()))
        rebuild = True
    elif db['value'] != currentValue:
        log.info(' It\'s value has changed, rebuild'.format(
            node.show()))
        rebuild = True
    if rebuild:
        return buildNode(node)
    log.info(' Node exists and has not been modified')

    if node.name() == 'Src':
        log.info(
            ' Source node hasn\'t changed, db up to date'.format(
                node.show())).sub()
        return currentValue

    log.info(' Now check/update dependencies'.format(node.show()))
    changedDeps = []
    for depKey, (_, depVal) in db['deps'].items():
        depNode = pickle.loads(depKey)
        # log.info(' * Update {}'.format(depNode.show())).add()
        log.add()
        newDepVal = update(depNode)
        changedString = '(unchanged)'
        nodeShow = depNode.show()
        if (depVal != newDepVal):
            changedDeps.append(depNode)
            changedString = '(changed)'
            changed = True
        log.debug(
            'update: {nodeShow}: db value: {depVal}, current value: {newDepVal} {changedString}'.format(
                **locals()))
        # log.info(' {} is up to date {}'.format(depNode.show(), changedString))
        log.sub()

    if changedDeps:
        changedDepStr = ', '.join([d.show() for d in changedDeps])
        log.info(' Deps changed ({}), rebuild'.format(changedDepStr))
        return buildNode(node)

    log.info(
        ' It or its dependencies haven\'t changed, do nothing'.format(
            node.show())).sub()
    return currentValue

def getSoftDir():
    import os
    environSoft = os.environ.get('soft', None)
    if 'SOFTDIR' in globals():
        return local.path(SOFTDIR)
    if environSoft:
        return local.path(environSoft)
    log.error("Either environment variable '$soft' or 'pipelinelib.SOFTDIR' must be set")
    sys.exit(1)

def getBrainsToolsPath(bthash):
    btpath = local.path(getSoftDir() / ('BRAINSTools-bin-' + bthash))
    if not btpath.exists():
        log.error(
            "{} doesn\'t exist, make it first with 'pnlscripts/software.py --commit {} brainstools".format(btpath, bthash))
        sys.exit(1)
    return btpath

def btPath(bthash):
    newpath = ':'.join(str(p) for p in [getBrainsToolsPath(bthash)] + local.env.path)
    return local.env(PATH=newpath)

def brainsToolsEnv(bthash):
    btpath = getBrainsToolsPath(bthash)
    newpath = ':'.join(str(p) for p in [btpath] + local.env.path)
    return local.env(PATH=newpath, ANTSPATH=btpath)

def getTrainingDataT1AHCCCsv():
    csv = getSoftDir() / 'trainingDataT1AHCC/trainingDataT1AHCC-hdr.csv'
    if not csv.exists():
        log.error('{} doesn\'t exist, make it first with \'pnlscripts/software.py t1s\''.format(csv))
        sys.exit(1)
    return csv

def getUKFTractography(ukfhash):
    binary = getSoftDir() / ('UKFTractography-' + ukfhash)
    if not binary.exists():
        log.error('{} doesn\'t exist, make it first with \'pnlscripts/software.py ukf\''.format(binary))


def bracket(s):
    return '(' + s + ')'

def convertImage(i, o, bthash):
    if i.suffixes == o.suffixes:
        i.copy(o)
    with brainsToolsEnv(bthash):
        from plumbum.cmd import ConvertBetweenFileFormats
        ConvertBetweenFileFormats(i, o)
