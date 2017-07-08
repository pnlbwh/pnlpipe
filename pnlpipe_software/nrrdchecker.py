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
            local.path(binary).move(get_path(sha))
        symlink = get_path(date)
        print("Make symlink: {} -> {}".format(symlink, get_path(sha)))
        get_path(date).unlink()
        get_path(sha).symlink(get_path(date))

        logger.info("Made '{}'".format(get_path(sha)))
        logger.info("Made '{}'".format(get_path(date)))

def get_path(hash=DEFAULT_HASH):
    return getSoftDir() / ('nrrdchecker-' + hash)
