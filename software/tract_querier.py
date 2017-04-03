import os
from software import downloadGithubRepo, getCommitInfo, getSoftDir, checkExists, TemporaryDirectory, envFromDict
from plumbum import local
from plumbum.cmd import chmod
import logging

DEFAULT_HASH = 'e045eab'
NAME = 'tract_querier'
REPO = 'demianw/tract_querier'

def make(commit=DEFAULT_HASH):
    """Downloads a lean version of tract_querier. Output is '$soft/tract_querier-<commit>'."""
    dest = getSoftDir()

    if commit != 'master':
        out = local.path(dest / '{}-{}'.format(NAME, commit))
        if checkExists(out):
            return

    with TemporaryDirectory() as tmpdir, local.cwd(tmpdir):
        repo = downloadGithubRepo(REPO, commit)
        sha, date = getCommitInfo(repo)
        out = local.path(dest / '{}-{}'.format(NAME, sha))
        if checkExists(out):
            return

        # save space
        (repo / 'doc').delete()
        (repo / '.git').delete()

        logging.info("Make '{out}'".format(**locals()))
        repo.move(out)

    chmod('-R', 'a-w', out)
    chmod('a-w', out)
    date_symlink = dest / '{}-{}'.format(NAME, date)
    out.symlink(date_symlink)


def getPath(hash=DEFAULT_HASH):
    return getSoftDir() / '{}-{}'.format(NAME, hash)

def envDict(hash):
    return {'PATH': getPath(hash) / 'scripts'
           ,'PYTHONPATH': getPath(hash)
    }

def env(bthash):
    return envFromDict(envDict(bthash))
