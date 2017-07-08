import sys
import os
from pnlpipe_software import getSoftDir, checkExists, TemporaryDirectory, downloadGithubRepo, getCommitInfo, envFromDict
import logging
from plumbum import local, FG
from plumbum.cmd import wget, tar

DEFAULT_HASH = '97e4b3b'

def make(hash=DEFAULT_HASH):
    if checkExists(get_path(hash)):
        return

    with TemporaryDirectory() as tmpdir, local.cwd(tmpdir):
        tmpdir = local.path(tmpdir)
        repo = downloadGithubRepo('MRtrix3/mrtrix3', hash)
        sha, date = getCommitInfo(repo)
        with local.cwd(repo):
            os.system('./configure')
            os.system('./build')
            os.system('mv ./release {}'.format(get_path(hash)))
        get_path(hash).symlink(get_path(date))

def get_path(hash=DEFAULT_HASH):
    return getSoftDir() / ('mrtrix3-' + hash)

def env_dict(hash):
    return {'PATH': get_path(hash) / 'bin' }

def env(bthash):
    return envFromDict(env_dict(bthash))
