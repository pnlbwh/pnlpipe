from plumbum import local
import yaml
import pickle
import logging
logger = logging.getLogger(__name__)
from python_log_indenter import IndentedLoggerAdapter
log = IndentedLoggerAdapter(logger, indent_char='.')
import basenode
import dag
import pnlpipe_config as config


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


DBDIR = local.path(config.OUTDIR) / 'db'


def staticdeps(static_build):
    """Decorator for node build() methods that don't have dynamic dependencies,
    saves some boilerplate"""

    def build(self, db):
        need_deps(self, db)
        self.static_build()

    return build


def _nodebuild(node, db):
    if hasattr(node, 'build'):
        node.build(db)
    else:
        staticdeps(node.static_build)(node, db)


def _exists(node):
    return local.path(node.output()).exists()


def _dbfile(node):
    nodepath = local.path(node.output())
    if nodepath.startswith(local.cwd):
        relative = nodepath - local.path(config.OUTDIR)
    else:
        relative = nodepath
    return local.path(DBDIR + '/' + relative.__str__() + '.db')


def _readDB(node):
    if not _dbfile(node).exists():
        return None
    with open(_dbfile(node), 'r') as f:
        return yaml.load(f)


def _writeDB(node, db):
    if not _dbfile(node).dirname.exists():
        _dbfile(node).dirname.mkdir()
    with open(_dbfile(node), 'w') as f:
        yaml.dump(db, f)


def need(parentNode, childNode, db):
    # log.info('Need: {}{}{}'.format(bcolors.OKGREEN,childNode.show(), bcolors.ENDC))
    if not childNode.output():
        raise TypeError("{}.output() returns NoneType, make sure it returns a valid output path.".format(childNode))
    log.debug('Need: {}'.format(childNode.show()))
    val = update(childNode)
    db['deps'][pickle.dumps(childNode)] = (childNode.output().__str__(), val)


def need_deps(node, db):
    for dep in node.deps.values():
        need(node, dep, db)


def _build(node):
    nodepath = local.path(node.output())
    db = {'value': None, 'deps': {}}
    if not node.deps:  # is input file
        if not nodepath.exists():
            raise Exception("{}: input path doesn't exist".format(node.output(
            )))
    else:
        nodepath.dirname.mkdir()
        log.info('Run {}.build()'.format(node.tag)).add()
        _nodebuild(node, db)
        nodepath = local.path(node.output())
        if nodepath.exists() and \
           nodepath.is_dir() and \
           not nodepath.list():
            nodepath.delete()
        if not _exists(node):
            raise Exception('{}: output wasn\'t created'.format(nodepath))
        node.write_provenance()
        # log.sub()
    log.info('Record value')
    db['value'] = node.stamp()
    log.debug('Node value is: {}'.format(db['value']))
    _writeDB(node, db)
    # log.info('Done')
    log.info('Done: {}{}{}'.format(bcolors.OKGREEN,node.show(),bcolors.ENDC))
    if node.deps:
        log.sub()
    return db['value']


def upToDate(node):
    log.debug('Check if output path is missing or has been modified')
    db = _readDB(node)
    currentValue = None if not _exists(node) else node.stamp()
    nodeChanged = False
    if db == None:
        log.info("Has no entry in database, build".format(
            node.output()))
        return False
    elif currentValue == None:
        log.info('File missing ({}), rebuild'.format(node.output()))
        return False
    elif db['value'] != currentValue:
        log.debug('old value: {}, new value: {}'.format(db['value'],
                                                        currentValue))
        log.info("Value has changed, rebuild")
        return False
    log.info('Node output exists and has not been modified')

    if not node.deps:
        log.info('Source node hasn\'t changed, db up to date')
        return True

    log.info('Check if dependencies are unchanged:').add()
    changedDeps = []
    for i, (depKey, (_, dbDepValue)) in enumerate(db['deps'].items()):
        depNode = pickle.loads(depKey)
        log.info('{}. {}'.format(i + 1, depNode.show()))
        # log.info('Output path: {}'.format(basenode.relativeOutput(depNode)))
        depValue = depNode.stamp()
        log.debug(
            'upToDate(): current value: {depValue}, db value: {dbDepValue}'.format(
                **locals()))
        if (depValue != dbDepValue):
            log.info('Dependency changed ({}), rebuild'.format(depNode.show(
            ))).sub().sub()
            return False
        if not upToDate(depNode):
            return False
        log.info('Dependency unchanged')
    log.sub()
    log.info('Dependencies are unchanged')
    log.info('Done: {}{}{}'.format(bcolors.OKGREEN,node.show(),bcolors.ENDC))
    return True


def update(node):
    log.info('Need: {}{}{}'.format(bcolors.HEADER, node.show(),
                                   bcolors.ENDC))
    # log.add()
    if upToDate(node):
        # log.info('Done')
        # log.sub()
        return node.stamp()
    val = _build(node)
    # log.sub()
    return val
