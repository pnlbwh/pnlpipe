import yaml
from plumbum import local
from contextlib import contextmanager
import dag
import logging
logger = logging.getLogger(__name__)
from python_log_indenter import IndentedLoggerAdapter
log = IndentedLoggerAdapter(logger, indent_char='.')
import pnlpipe_lib

# def readInputKeysYaml(ymlfile):
#     if not local.path(ymlfile).exists():
#         raise Exception(
#             "Missing {}, cannot set InputKey paths".format(ymlfile))
#     with open(ymlfile, 'r') as f:
#         inputkeys = yaml.load(f, Loader=yaml.loader.BaseLoader)
#     caseidPattern = inputkeys.get('caseid', '{case}')
#     for key, val in inputkeys.items():
#         if not '/' in val:
#             continue
#         inputkeys[key] = local.path(val.replace(caseidPattern, '{case}'))
#     # return inputkeys
#     return pnlpipe_config.INPUT_PATHS


class ParamNode(dag.Node):
    def __init__(self, tag):
        self.tag = tag
        self.children = []


class PathNode(dag.Node):
    def __init__(self, kwargs):
        # self.db = {'value': None, 'deps': {}}

        for key, val in kwargs.items():
            if key == 'self':
                continue
            self.__setattr__(key, val)
        # self.caseid = kwargs['caseid']

        if not hasattr(self, 'deps'):
            self.deps = []

        if not hasattr(self, 'params'):
            self.params = []

        self.tag = self.__class__.__name__
        self.children = self.deps + [ParamNode(p) for p in self.params]

    # @abstractmethod
    # def path():

    def readCurrentValue(self):
        log.debug(self.tag + ' path: ' + str(self.path()) +
                  ' (readCurrentValue)')
        return self.path().stat().st_mtime


class InputKey(PathNode):
    def __init__(self, caseid, inputKey):
        self.deps = []
        self.params = [inputKey]
        PathNode.__init__(self, locals())

    def path(self):
        return lookupPathKey(self.inputKey, self.caseid,
                             pnlpipe_lib.INPUT_KEYS)

    def showDAG(self):
        return 'InputKey-{}'.format(self.params[0])

    def showWithoutRepeats(self, repeats):
        return self.showDAG()

    def showCompressedDAG(self):
        return self.showDAG()

    def isLeaf(self):
        return True

    def build(self, db):
        if not self.path().exists():
            raise Exception(
                "Input file doesn\'t exist: {}\nCheck that the path of your input key '{}' is correct.".format(
                    self.path(), self.inputKey))


class GeneratedNode(PathNode):
    def isLeaf(self):
        return False

    def path(self):
        ext = getattr(self, 'ext', '.nrrd')
        if not ext.startswith('.'):
            ext = '.' + ext
        return pnlpipe_lib.OUTDIR / self.caseid / (
            self.showCompressedDAG() + '-' + self.caseid + ext)

    def showCompressedDAG(self):
        repeatedNodes = dag.getRepeatedNodes(self)
        depStrings = filter(lambda x: x != '',
                            [dag.showDAGWithoutRepeats(d, repeatedNodes)
                             for d in self.children])
        # now remove repeated nodes from other repeated nodes
        trimmedRepeats = []
        for n, s in repeatedNodes:
            trimmed = dag.showDAGWithoutRepeats(
                n, [(x, y) for (x, y) in repeatedNodes if y != s])
            trimmedRepeats.append(trimmed)

        if repeatedNodes:
            return '{}({})-{}'.format(self.tag, ','.join(depStrings),
                                      '-'.join(sorted(trimmedRepeats)))
        return '{}({})'.format(self.tag, ','.join(depStrings))


def lookupPathKey(key, caseid, pathsDict):
    try:
        pathFormat = pathsDict[key]
        caseidPlaceholder = pathsDict.get('caseid', '{case}')
        filepath = local.path(pathFormat.replace(caseidPlaceholder, caseid))
        return filepath
    except KeyError:
        msg = """Key '{key}' not found in pnlpipe_lib.nodes.INPUT_PATHS.
Your pipeline has a node of type 'InputKey(caseid, {key})', but {key} and its path have not been set in your 'inputPaths.yml'.
Either change '{key}' in your parameter file to a key in inputPaths.yml, or add '{key}'
to inputPaths.yml.
""".format(key=key)
        raise Exception(msg)
