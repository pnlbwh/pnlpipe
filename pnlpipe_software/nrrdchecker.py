import sys
import os
from pnlpipe_software import getSoftDir, checkExists, TemporaryDirectory, downloadGithubRepo, getCommitInfo, envFromDict
import logging
logger = logging.getLogger(__name__)
from plumbum import local, FG
from plumbum.cmd import wget, tar

DEFAULT_HASH = 'ffc358f'

def make(hash=DEFAULT_HASH):
    if hash != 'master':
        if checkExists(get_path(hash)):
            return

    with TemporaryDirectory() as tmpdir, local.cwd(tmpdir):
        tmpdir = local.path(tmpdir)
        repo = downloadGithubRepo('reckbo/nrrdchecker', hash)
        sha, date = getCommitInfo(repo)
        with local.cwd(repo):
            from plumbum.cmd import stack
            stack['setup'] & FG
            stack['build'] & FG
            binary = stack('exec', 'which', 'nrrdchecker')[:-1]
            get_path(sha).mkdir()
            local.path(binary).move(get_path(sha) / 'nrrdchecker')

        symlink = get_path(date).dirname
        print("Make symlink: {} -> {}".format(symlink, get_path(sha).dirname))
        get_path(date).unlink()
        get_path(sha).dirname.symlink(symlink)

        logger.info("Made '{}'".format(get_path(sha)))
        logger.info("Made '{}'".format(symlink))

def get_path(hash=DEFAULT_HASH):
    return getSoftDir() / ('nrrdchecker-' + hash)


def env_dict(hash):
    return { 'PATH': get_path(hash)}
