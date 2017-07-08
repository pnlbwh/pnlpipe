import dag
import six, abc
import inspect
from plumbum import local
from hashing import dirhash, filehash
import pnlpipe_config


@six.add_metaclass(abc.ABCMeta)
class Node(dag.Node):
    @property
    def children(self):
        return self.deps.values() + [dag.Leaf(p,v) for (p,v) in self.params.items()]

    @property
    def tag(self):
        return self.__class__.__name__

    @abc.abstractproperty
    def deps(self):
        """deps"""

    @abc.abstractproperty
    def params(self):
        """params"""

    @abc.abstractproperty
    def output(self):
        """output"""

    def stamp(self):
        outpath = local.path(self.output())
        if not outpath.exists():
            return None
        if outpath.is_file():
            return filehash(outpath, hashfunc='md5')
        if outpath.is_dir():
            return dirhash(str(outpath), hashfunc='md5', ignore_hidden=True)
        raise Exception('{}: output path is neither a file nor directory.'.format(self.tag))


    def show(self):
        """Representation of Node/DAG in string format"""
        # return pnlpipe_config.show_node(self)
        return self.output() - local.cwd

    def write_provenance(self):
        def find_src_nodes(root):
            nodes = dag.preorder(root)
            src_nodes = [n for n in nodes if not n.deps]
            return src_nodes
        nodepath = local.path(self.output())
        outpath = nodepath + '.provenance'
        print find_src_nodes(self)
        src_paths = [n.output() for n in find_src_nodes(self)]
        with open(outpath, 'w') as f:
            f.write('Compressed DAG:\n')
            f.write(dag.showCompressedDAG(self) + '\n\n')
            f.write('Input Paths:\n')
            f.write('\n'.join(src_paths) + '\n\n')
            f.write('Full DAG:\n')
            f.write(dag.showDAG(self))


def relativeOutput(node):
    return str(local.path(node.output())).replace(str(local.cwd) + '/', '')


def _check_args(argType, given, sig, cls, expectedType=object):
    if len(given) != len(sig):
        raise TypeError(
            "{}() expects {} element(s) in '{}' argument ({}), instead {} given: {}".format(
                cls, len(sig), argType, sig, len(given), given))
    if not all([isinstance(n, expectedType) for n in given]):
        raise TypeError(
            "{}() expects its '{}' argument list elements to be all of type {}.".format(
                cls, argType, expectedType))


def _check_dict_args(argType, given, sig, cls, expectedType=object):
    for key in sig:
        if key not in given.keys():
            raise TypeError("{}(..): missing key '{}' in {}".format(
                cls, key, argType))
    if not all([isinstance(v, expectedType) for v in given.values()]):
        raise TypeError(
            "{}(..) expects its '{}' dict argument to have values all of type {}.".format(
                cls, argType, expectedType))


def _makeinit(Cls, paramNames, depNames):
    def nodeinit(self, params=None, deps=None):
        if not params:
            params = []
        if not deps:
            deps = []
        for argname, arginput, argkeywords, argtype in [('params', params, paramNames, object),
                                               ('deps', deps, depNames, Node)]:
            if isinstance(arginput, list):
                _check_args(argname, arginput, argkeywords, Cls.__name__,
                            argtype)
                _arginput = dict(zip(argkeywords, arginput))
                setattr(self, '_' + argname, _arginput)
            elif isinstance(arginput, dict):
                _check_dict_args(argname, arginput, argkeywords, Cls.__name__,
                                 argtype)
                _arginput = dict((k,arginput[k]) for k in argkeywords)
                setattr(self, '_' + argname, _arginput)
            else:
                raise Exception(
                    "{}(..): Wrong input type for {}, must be a list or a dictionary".format(Cls.__name__, argname))
            for k in argkeywords:
                if isinstance(_arginput[k], Node):
                    setattr(self, k, _arginput[k].output())
                else:
                    setattr(self, k, _arginput[k])

    return nodeinit


def node(params=[], deps=[]):
    paramNames = params
    depNames = deps

    def class_rebuilder(Cls):
        for abstractmethod in Cls.__abstractmethods__:
            if abstractmethod in ['params', 'deps']:
                continue

            if not hasattr(Cls, abstractmethod):
                raise Exception("basenode: {} is missing method {}".format(
                    Cls, abstractmethod))
            method = getattr(Cls, abstractmethod)

            if isinstance(method, abc.abstractproperty):
                raise Exception("basenode: {} is missing abstract property '{}'".format(
                    Cls, abstractmethod))

            if isinstance(method, abc.abstractmethod):
                raise Exception("basenode: {} is missing abstract method '{}'".format(
                    Cls, abstractmethod))

            if not callable(method):
                raise Exception("basenode: {} has invalid method '{}'".format(
                    Cls, abstractmethod))

        if deps and (not hasattr(Cls, 'build') and
                     not hasattr(Cls, 'static_build')):
            raise Exception(
                "basenode: {} has deps but is missing method build() or static_build()".format(
                    Cls))

        if deps and (hasattr(Cls, 'build') and hasattr(Cls, 'static_build')):
            raise Exception(
                "basenode: {} has method build() and static_build() defined, can only have one".format(
                    Cls))

        Cls.__init__ = _makeinit(Cls, paramNames, depNames)
        Cls.params = property(lambda x: x._params)
        Cls.deps = property(lambda x: x._deps)
        Cls.__abstractmethods__ = frozenset()

        return Cls

    return class_rebuilder

# def dagDict(node):
#     if not node.children:
#         return str(node.tag)
#     childDAGs = [dagDict(n) for n in node.children]
#     d = {}
#     d[str(node.tag)] = {'params': node.params,
#                         'deps' : childDAGs
#                         }
#     return d
