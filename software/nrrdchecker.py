import sys
import os
from software import getSoftDir, checkExists, TemporaryDirectory, downloadGithubRepo, getCommitInfo, envFromDict
import logging
from plumbum import local, FG
from plumbum.cmd import wget, tar

DEFAULT_HASH = '133ad94'

def make(hash=DEFAULT_HASH):
    if checkExists(getPath(hash)):
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
            local.path(binary).move(getPath(hash))
        getPath(hash).symlink(getPath(date))

        logging.info("Made '{}'".format(getPath(hash)))
        logging.info("Made '{}'".format(getPath(date)))

def getPath(hash=DEFAULT_HASH):
    return getSoftDir() / ('nrrdchecker-' + hash)
