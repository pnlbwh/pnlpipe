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

# DEBUG = True
DEBUG = False
dbdir = local.path('_data/db')

class Node(object):
    def __init__(self, kwargs):
        self.db = {'value' : None, 'deps' : {}}
        self.caseid = kwargs['caseid']

def lookupPathKey(key, caseid, pathsDict):
    try:
        pathPattern = local.path(pathsDict.get(key))
        filepath = local.path(pathPattern.replace('{case}', caseid))
        if not filepath.exists():
            logging.error(str(filepath) + ' does not exist, maybe a typo in PATHS?')
            sys.exit(1)
        return filepath
    except KeyError:
        print(key + " not in paths")
        sys.exit(1)

def dbfile(node):
    return  dbdir / node.path().name

def readDB(node):
    if not dbfile(node).exists():
        return None
    with open(dbfile(node), 'r') as f:
        return yaml.load(f)

def readCurrentValue(node):
    if DEBUG:
        logging.debug(node.__class__.__name__ + ' path: ' + str(node.path()))
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
