from plumbum import local
import sys
import yaml
import pickle
# import hashlib
# from abc import abstractmethod, abstractproperty
from collections import Counter

def logfmt(scriptname):
    return '%(asctime)s ' + local.path(scriptname).name + ' %(levelname)s  %(message)s'

import logging
logger = logging.getLogger()
#logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))
logging.basicConfig(level=logging.INFO, format=logfmt(__file__))
from python_log_indenter import IndentedLoggerAdapter
log = IndentedLoggerAdapter(logger, indent_char='.')

# Needs to be set by client code
INPUT_PATHS = None

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
        if not hasattr(self, 'params'):
            self.params = []

    def name(self):
        return self.__class__.__name__

    def show(self):
        depsString = ','.join([d.show() for d in self.deps] + [str(p) for p in self.params])
        return '{}({})'.format(self.name(), depsString)

def concat(l):
    return l if l == [] else [item for sublist in l for item in sublist]


def preorder(node, fn):
    return [(dep, fn(dep)) for dep in node.deps] + \
        concat([preorder(dep, fn) for dep in node.deps])

def preorderWithParams(node, fn):
    if not isinstance(node, Node):  # is a param leaf
        return []
    if isinstance(node, Src): # treat Src nodes as leaves (more meaningful paths)
        return []
    return [(dep, fn(dep)) for dep in (node.deps + node.params)] + \
        concat([preorderWithParams(dep, fn) for dep in (node.deps + node.params)])

def showFn(x):
    if isinstance(x, Node):
        try:
            func = getattr(x, "show")
            return func()
        except AttributeError:
            log.error("'show' not found for node")
            print 'Node is:'
            print node
            sys.exit(1)
    else:
        return str(x)


def getRepeatedNodes(node):
    nodeShowMap = preorderWithParams(node, showFn)
    subtreeCounts = Counter(nodeShowMap)
    return [(n, s) for (n, s), count in subtreeCounts.items()
            if count > 1 and not s.startswith('Src')]


def showWithoutRepeats(node, repeatedNodes):
    if showFn(node) in [s for _,s in repeatedNodes]:
        return ''
    if not isinstance(node, Node):
        return str(node)
    if isinstance(node, Src):
        return node.show()
    depStrings = filter(lambda x: x!='', [showWithoutRepeats(d, repeatedNodes) for d in (node.deps + node.params)])
    # depString = ','.join(depStrings + self.params)
    depString = ','.join(depStrings)
    if depString:
        return '{}({})'.format(node.name(), depString)
    else:
        return node.name()

class GeneratedNode(Node):
    def path(self):
        ext = getattr(self, 'ext', '.nrrd')
        if not ext.startswith('.'):
            ext = '.' + ext
        return OUTDIR / self.caseid / (
            self.showShortened() + '-' + self.caseid + ext)

    def showShortened(self):
        repeatedNodes = getRepeatedNodes(self)
        depStrings = filter(lambda x: x != '',
                            [showWithoutRepeats(d, repeatedNodes) for d in (self.deps + self.params)])
        # now remove repeated nodes from other repeated nodes
        trimmedRepeats = []
        for n, s in repeatedNodes:
            trimmed = showWithoutRepeats(n,
                [(x, y) for (x, y) in repeatedNodes if y != s])
            trimmedRepeats.append(trimmed)

        if repeatedNodes:
            # return '{}/{}({})'.format('-'.join(sorted(trimmedRepeats)), self.name(), ','.join(depStrings))
            return '{}({})-{}'.format(self.name(), ','.join(depStrings), '-'.join(sorted(trimmedRepeats)))
        return '{}({})'.format(self.name(), ','.join(depStrings))

class Src(Node):
    def __init__(self, caseid, pathsKey):
        self.deps = []
        self.params = [pathsKey]
        Node.__init__(self, locals())

    def path(self):
        return lookupPathKey(self.pathsKey, self.caseid, INPUT_PATHS)

    def show(self):
        return 'Src-{}'.format(self.params[0])
        # return self.params[0]

    def showWithoutRepeats(self, repeats):
        return self.show()

    def showShortened(self):
        return self.show()

    def build(self):
        pass

class MissingInputPathsKeyException(Exception):
    pass

class DoesNotExistException(Exception):
    pass

def lookupPathKey(key, caseid, pathsDict):
    try:
        pathPattern = pathsDict[key]
        caseid_string = pathsDict.get('caseid', '{case}')
        filepath = local.path(pathPattern.replace(caseid_string, caseid))
        if not filepath.exists():
            raise DoesNotExistException(
                "pipelib: '{}' does not exist".format(filepath))
        return filepath
    except KeyError:
        msg = """Key '{key}' not found in pipelib.INPUT_PATHS.
Your pipeline has a node of type 'Src(caseid, {key})', but {key} and its path have not been set in your 'srcpaths.yml'.
""".format(key=key)
        raise MissingInputPathsKeyException(msg)


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
    return DBDIR / (node.showShortened() + '-' + node.caseid)


def readDB(node):
    if not dbfile(node).exists():
        return None
    with open(dbfile(node), 'r') as f:
        return yaml.load(f)


def readCurrentValue(node):
    log.debug(node.__class__.__name__ + ' path: ' +
                  str(node.path()) + ' (readCurrentValue)')
    mtime = node.path().stat().st_mtime
    return mtime


def need(parentNode, childNode):
    log.debug('{} needs {}'.format(parentNode.show(),
                                                    childNode.show()))
    val = update(childNode)
    parentNode.db['deps'][pickle.dumps(childNode)] = (
        childNode.path().__str__(), val)


def needDeps(node):
    log.info(' Update dependencies')
    for depNode in node.deps:
        need(node, depNode)
    log.info(' Finished updating dependencies')
    log.info(' Now make ' + node.__class__.__name__)

def buildNode(node):
    node.path().dirname.mkdir()
    node.build()
    if not node.path().exists():
        log.error('{}: output wasn\'t created'.format(node.path()))
        sys.exit(1)
    db = node.db
    db['value'] = readCurrentValue(node)
    del node.db
    if not dbfile(node).dirname.exists():
        dbfile(node).dirname.mkdir()
    with open(dbfile(node), 'w') as f:
        yaml.dump(db, f)
    log.info(' Built, recorded mtime').sub()
    return db['value']


def update(node):
    cwd = str(local.cwd) + '/'
    if isinstance(node, Src):
        relativePath = node.path()
        log.info(' * Update {} (path: {})'.format(node.show(), node.path())).add()
    else:
        relativePath = str(node.path()).replace(cwd,'')
        log.info(' * Update {}'.format(relativePath)).add()

    log.info(' Check if node exists or has been modified')
    db = readDB(node)
    currentValue = None if not node.path().exists() else readCurrentValue(node)
    nodeChanged = False
    rebuild = False
    if db == None:
        log.info(' doesn\'t exist (has no db), build'.format(node.path()))
        rebuild = True
    elif currentValue == None:
        log.info(' File missing ({}), rebuild'.format(relativePath))
        rebuild = True
    elif db['value'] != currentValue:
        log.debug('old value: {}, new value: {}'.format(db['value'], currentValue))
        log.info(' It\'s value has changed, rebuild')
        rebuild = True
    if rebuild:
        return buildNode(node)
    log.info(' Node exists and has not been modified')

    if node.name() == 'Src':
        log.info(
            ' Source node hasn\'t changed, db up to date').sub()
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
            'update: {relativePath}: db value: {depVal}, current value: {newDepVal} {changedString}'.format(
                **locals()))
        # log.info(' {} is up to date {}'.format(depNode.show(), changedString))
        log.sub()

    if changedDeps:
        changedDepStr = ', '.join([d.show() for d in changedDeps])
        log.info(' Deps changed ({}), rebuild'.format(changedDepStr))
        return buildNode(node)

    log.info(
        ' It or its dependencies haven\'t changed, do nothing').sub()
    return currentValue
