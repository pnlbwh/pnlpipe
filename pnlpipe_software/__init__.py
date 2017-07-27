#!/usr/bin/env python
from __future__ import print_function
import sys
import os
from os.path import dirname, basename, isfile
import glob
from tempfile import mkdtemp
# modules = glob.glob(dirname(__file__) + "/*.py")
# __all__ = [basename(f)[:-3] for f in modules
#            if isfile(f) and not f.startswith('_')]
from plumbum import local, FG, cli
from plumbum.cmd import git, cmake, make, chmod
import logging
logger = logging.getLogger(__name__)


def modules():
    import pkgutil
    import pnlpipe_software
    from os.path import isfile
    for importer, modname, ispkg in pkgutil.iter_modules(
            pnlpipe_software.__path__):
        if not modname.startswith('_') and not modname.endswith('.sh'):
            yield modname, importer.find_module(modname).load_module(modname)


def import_module(name):
    import importlib
    moduleFile = local.path('pnlpipe_software') / (name + '.py')
    if not moduleFile.exists():
        raise Exception(
            "{} does not exist, is there a typo (e.g. in the params file?)".format(
                moduleFile))
    return importlib.import_module('pnlpipe_software.' + name)


def module_file(name):
    return local.path('pnlpipe_software/{}.py'.format(name))


def composeEnvDicts(env_dicts):
    result = {'PATH': [], 'PYTHONPATH': []}
    for d in env_dicts:
        for var, val in d.items():
            if var == 'PATH':
                result['PATH'].insert(0, val)
            elif var == 'PYTHONPATH':
                result['PYTHONPATH'].insert(0, val)
            else:
                result[var] = val
    if result.get('PATH'):
        result['PATH'] = ':'.join(result['PATH'] + local.env.path)
    if result.get('PYTHONPATH'):
        result['PYTHONPATH'] = ':'.join(result['PYTHONPATH']) + os.environ.get(
            'PYTHONPATH', '')

    return result


def envFromDict(env_dict):
    d = composeEnvDicts([env_dict])
    return local.env(**d)


def prefixPATH(paths):
    return ':'.join(str(p) for p in paths + local.env.path)


def prefixPYTHONPATH(paths):
    PYTHONPATH = os.environ.get('PYTHONPATH', '').split(':')
    return ':'.join(str(p) for p in paths + PYTHONPATH)


def checkExists(target):
    if target.exists():
        logging.info('{} already exists, skipping.'.format(target))
        return True
    return False


def downloadGithubArchive(ownerrepo, version='master'):
    """Makes 'repo-xxxx' directory."""
    url = 'https://github.com/{ownerrepo}/archive/{version}.tar.gz'.format(
        **locals())
    repo = ownerrepo.split('/')[1]
    from plumbum.cmd import curl, tar
    import os.path
    (curl['-L', url] | tar['xz']) & FG
    from glob import glob
    repos = glob(repo + '*')
    repos.sort(key=os.path.getmtime)
    return local.path(repos[0])


def getCommitInfo(repo_path):
    with local.cwd(local.path(repo_path)):
        sha = git('rev-parse', '--short', 'HEAD').strip()
        date = git('show', '-s', '--format=%cd', '--date=short').strip()
    return (sha, date)


def downloadGithubRepo(ownerrepo, commit='master'):
    url = 'https://github.com/{ownerrepo}.git'.format(**locals())
    repo = ownerrepo.split('/')[1]

    if not local.path(repo).exists():
        git['clone', url] & FG

    with local.cwd(repo):
        git['checkout', 'master'] & FG
        git['pull', 'origin'] & FG
        git['checkout', commit] & FG
    return local.path(repo)


def getSoftDir():
    import os
    environSoft = os.environ.get('soft', None)
    if 'SOFTDIR' in globals():
        return local.path(SOFTDIR)
    if environSoft:
        return local.path(environSoft)
    log.error(
        "Environment variable '$soft' must be set. This is the directory where e.g. BRAINSTools, UKFTractography, tract_querier, and the training data are installed.")
    sys.exit(1)


class TemporaryDirectory(object):
    """Create and return a temporary directory.  This has the same
    behavior as mkdtemp but can be used as a context manager.  For
    example:

        with TemporaryDirectory() as tmpdir:
            ...

    Upon exiting the context, the directory and everything contained
    in it are removed.
    """

    def __init__(self, suffix="", prefix="tmp", dir=None):
        self._closed = False
        self.name = None  # Handle mkdtemp raising an exception
        self.name = mkdtemp(suffix, prefix, dir)

    def __repr__(self):
        return "<{} {!r}>".format(self.__class__.__name__, self.name)

    def __enter__(self):
        return self.name

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
                print(
                    "ERROR: {!r} while cleaning up {!r}".format(ex,
                                                                self, ),
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
    import os as _os
    import warnings as _warnings
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
