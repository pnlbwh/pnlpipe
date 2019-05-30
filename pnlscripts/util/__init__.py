from __future__ import print_function
from os.path import abspath, exists, dirname, join
import os, sys
import os as _os
import warnings as _warnings
from tempfile import mkdtemp
from plumbum import cli, local
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import pnlpipe_config

logger = logging.getLogger()

def logfmt(scriptname):
    return '%(asctime)s ' + scriptname + ' %(levelname)s  %(message)s'

def set_log_format(loglevel):
    logging.basicConfig(
        level=loglevel,
        format='%(asctime)s - %(levelname)5s - %(name)s:  %(message)s',
        datefmt="%Y-%m-%d %H:%M")


from plumbum.cli.switches import Predicate

def isNifti(f):
    return '.nii' in f.suffixes

def isNrrd(f):
    return '.nrrd' in f.suffixes or '.nhdr' in f.suffixes


@Predicate
def ExistingNrrdOrNifti(val):
    p = local.path(val)
    if ('.nhdr' not in p.suffixes and '.nrrd' not in p.suffixes and '.nii' not in p.suffixes) or not p.exists():
        raise ValueError("%r is not an existing nrrd or nifti file" % (val,))
    return p

@Predicate
def Nrrd(val):
    p = local.path(val)
    if ('.nhdr' not in p.suffixes and '.nrrd' not in p.suffixes):
        raise ValueError("%r must be in nrrd format, i.e. have .nhdr or .nrrd extension." % (val,))
    return p

@Predicate
def ExistingNrrd(val):
    p = local.path(val)
    if ('.nhdr' not in p.suffixes and '.nrrd' not in p.suffixes) or not p.exists():
        raise ValueError("%r is not an existing nrrd file" % (val,))
    return p

@Predicate
def NonexistentNrrd(val):
    p = local.path(val)
    if ('.nhdr' not in p.suffixes and '.nrrd' not in p.suffixes) or p.exists():
        raise ValueError("%r must be a non-existent nrrd file" % (val,))
    return p

class TemporaryDirectory(object):
    """Create and return a temporary directory.  This has the same
    behavior as mkdtemp but can be used as a context manager.  For
    example:

        with TemporaryDirectory() as tmpdir:
            ...

    Upon exiting the context, the directory and everything contained
    in it are removed.
    """

    def __init__(self, suffix="", prefix="tmp", dir=pnlpipe_config.TMPDIR):
        self._closed = False
        self.name = None # Handle mkdtemp raising an exception
        self.name = mkdtemp(suffix, prefix, dir)

    def __repr__(self):
        return "<{} {!r}>".format(self.__class__.__name__, self.name)

    def __enter__(self):
        return local.path(self.name)

    def cleanup(self, _warn=False):
        if self.name and not self._closed:
            try:
                self._rmtree(self.name)
            except (TypeError, AttributeError) as ex:
                # Issue #10188: Emit a warning on stderr
                # if the directory could not be cleaned
                # up due to missing globals
                if "None" not in str(ex):
                    raise
                print("ERROR: {!r} while cleaning up {!r}".format(ex, self,),
                      file=_sys.stderr)
                return
            self._closed = True
            if _warn:
                self._warn("Implicitly cleaning up {!r}".format(self),
                           ResourceWarning)

    def __exit__(self, exc, value, tb):
        self.cleanup()

    def __del__(self):
        # Issue a ResourceWarning if implicit cleanup needed
        self.cleanup(_warn=True)

    # XXX (ncoghlan): The following code attempts to make
    # this class tolerant of the module nulling out process
    # that happens during CPython interpreter shutdown
    # Alas, it doesn't actually manage it. See issue #10188
    _listdir = staticmethod(_os.listdir)
    _path_join = staticmethod(_os.path.join)
    _isdir = staticmethod(_os.path.isdir)
    _islink = staticmethod(_os.path.islink)
    _remove = staticmethod(_os.remove)
    _rmdir = staticmethod(_os.rmdir)
    _warn = _warnings.warn

    def _rmtree(self, path):
        # Essentially a stripped down version of shutil.rmtree.  We can't
        # use globals because they may be None'ed out at shutdown.
        for name in self._listdir(path):
            fullname = self._path_join(path, name)
            try:
                isdir = self._isdir(fullname) and not self._islink(fullname)
            except OSError:
                isdir = False
            if isdir:
                self._rmtree(fullname)
            else:
                try:
                    self._remove(fullname)
                except OSError:
                    pass
        try:
            self._rmdir(path)
        except OSError:
            pass

import sys
from types import ModuleType
class LocalModule(ModuleType):
    """The module-hack that allows us to use ``from pnlscripts.scripts import script_py``"""
    __all__ = ()  # to make help() happy
    __package__ = __name__
    def __getattr__(self, name):
        scriptname = name.replace('_', '.')
        scriptdir = abspath(join(dirname(__file__), '..'))
        filename = join(scriptdir, scriptname)
        if not exists(filename):
            logging.error(filename + ' doesn\'t exist')
            raise AttributeError(filename)
        return local[filename]
    __path__ = []
    __file__ = __file__

# scripts = LocalModule(__name__ + ".scripts", LocalModule.__doc__)
scripts = LocalModule(__name__ + ".scripts", LocalModule.__doc__)
sys.modules[scripts.__name__] = scripts
del sys
del ModuleType
del LocalModule

import sys
from types import ModuleType
class LocalModule(ModuleType):
    """The module-hack that allows us to use ``from util.antspath import script_py``"""
    __all__ = ()  # to make help() happy
    __package__ = __name__
    def __getattr__(self, name):
        antspath = os.environ.get('ANTSPATH',None)
        if not antspath:
            raise Exception("ANTSPATH is not set, make sure it is exported, e.g export ANTSPATH[=/path/to/software]")

        scriptname = name.replace('_', '.')
        filename = join(antspath, scriptname)
        if not antspath or not exists(filename):
            raise AttributeError(name)
        return local[filename]
    __path__ = []
    __file__ = __file__

antspath = LocalModule(__name__ + ".antspath", LocalModule.__doc__)
sys.modules[antspath.__name__] = antspath
del sys
del ModuleType
del LocalModule
