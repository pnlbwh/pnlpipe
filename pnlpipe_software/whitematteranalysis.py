import os
from pnlpipe_software import downloadGithubRepo, getCommitInfo, getSoftDir, checkExists, TemporaryDirectory, envFromDict
from plumbum import local
from plumbum.cmd import chmod
import logging

DEFAULT_HASH = '7a93312'

NAME = 'whitematteranalysis'
REPO = 'SlicerDMRI/' + NAME

def make(commit=DEFAULT_HASH):
    """Downloads whitematteranalysis. Output is '$soft/whitematteranalysis-<commit>'."""
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
        (repo / 'tests').delete()
        (repo / '.git').delete()

        logging.info("Make '{out}'".format(**locals()))
        repo.move(out)

    chmod('-R', 'a-w', out)
    chmod('a-w', out)
    date_symlink = dest / '{}-{}'.format(NAME, date)
    out.symlink(date_symlink)


def getPath(hash=DEFAULT_HASH):
    path = getSoftDir() / '{}-{}'.format(NAME, hash)
    return path

def envDict(hash):
    return {'PATH': getPath(hash) / 'bin'
           ,'PYTHONPATH': getPath(hash)
    }

def env(bthash):
    return envFromDict(envDict(bthash))
