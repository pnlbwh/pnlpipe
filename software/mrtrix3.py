import sys
import os
from software import getSoftDir, checkExists, TemporaryDirectory, downloadGithubRepo, getCommitInfo
import logging
from plumbum import local, FG
from plumbum.cmd import wget, tar

DEFAULT_HASH = '97e4b3b'

def make(hash=DEFAULT_HASH):
    if checkExists(getPath(hash)):
        sys.exit(1)

    with TemporaryDirectory() as tmpdir, local.cwd(tmpdir):
        tmpdir = local.path(tmpdir)
        repo = downloadGithubRepo('MRtrix3/mrtrix3', hash)
        sha, date = getCommitInfo(repo)
        with local.cwd(repo):
            os.system('./configure')
            os.system('./build')
            os.system('mv ./release {}'.format(getPath(hash)))
        getPath(hash).symlink(getPath(date))

def getPath(hash=DEFAULT_HASH):
    return getSoftDir() / ('mrtrix3-' + hash)


def env(hash):
    path = getPath(hash)
    newpath = ':'.join(str(p) for p in [path] + local.env.path)
    return local.env(PATH=newpath)
