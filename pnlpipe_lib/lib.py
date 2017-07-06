from plumbum import local
import yaml
import pickle
import logging
logger = logging.getLogger(__name__)
from python_log_indenter import IndentedLoggerAdapter
log = IndentedLoggerAdapter(logger, indent_char='.')
from nodes import *
from util import *
import config

def dbfile(node):
    return config.OUTDIR / 'db' / (
        node.showCompressedDAG() + '-' + node.caseid)


def readDB(node):
    if not dbfile(node).exists():
        return None
    with open(dbfile(node), 'r') as f:
        return yaml.load(f)


def writeDB(node, db):
    if not dbfile(node).dirname.exists():
        dbfile(node).dirname.mkdir()
    with open(dbfile(node), 'w') as f:
        yaml.dump(db, f)


def need(parentNode, childNode, db):
    log.debug('{} needs {}'.format(parentNode.showDAG(), childNode.showDAG()))
    val = update(childNode)
    db['deps'][pickle.dumps(childNode)] = (childNode.path().__str__(), val)


def needDeps(node, deps, db):
    log.info(' Update dependencies')
    for dep in deps:
        need(node, dep, db)
    log.info(' Finished updating dependencies')
    log.info(' Now make ' + node.tag)


def build(node):
    node.path().dirname.mkdir()
    db = {'value': None, 'deps': {}}
    node.build(db)
    if not node.path().exists():
        raise Exception('{}: output wasn\'t created'.format(node.path()))
    db['value'] = node.readCurrentValue()
    writeDB(node, db)
    log.info(' Built, recorded mtime').sub()
    return db['value']


def update(node):
    if isinstance(node, InputKey):
        log.info(' * Update {} (path: {})'.format(node.showDAG(), node.path(
        ))).add()
    else:
        relativePath = str(node.path()).replace(str(local.cwd) + '/', '')
        log.info(' * Update {}'.format(relativePath)).add()

    log.info(' Check if node exists or has been modified')
    db = readDB(node)
    currentValue = None if not node.path().exists() else node.readCurrentValue(
    )
    nodeChanged = False
    rebuild = False
    if db == None:
        log.info(' doesn\'t exist (has no db), build'.format(node.path()))
        node.db = {'value': None, 'deps': {}}
        rebuild = True
    elif currentValue == None:
        log.info(' File missing ({}), rebuild'.format(node.path()))
        rebuild = True
    elif db['value'] != currentValue:
        log.debug('old value: {}, new value: {}'.format(db['value'],
                                                        currentValue))
        log.info(' It\'s value has changed, rebuild')
        rebuild = True
    if rebuild:
        return build(node)
    log.info(' Node exists and has not been modified')

    if node.tag == 'InputKey':
        log.info(' Source node hasn\'t changed, db up to date').sub()
        return currentValue

    log.info(' Now check/update dependencies'.format(node.showDAG()))
    changedDeps = []
    for depKey, (_, depVal) in db['deps'].items():
        depNode = pickle.loads(depKey)
        # log.info(' * Update {}'.format(depNode.show())).add()
        log.add()
        newDepVal = update(depNode)
        changedString = '(unchanged)'
        nodeShow = depNode.showDAG()
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
        changedDepStr = ', '.join([d.showDAG() for d in changedDeps])
        log.info(' Deps changed ({}), rebuild'.format(changedDepStr))
        return build(node)

    log.info(' It or its dependencies haven\'t changed, do nothing').sub()
    return currentValue
