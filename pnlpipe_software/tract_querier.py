import os
from pnlpipe_software import downloadGithubRepo, getCommitInfo, getSoftDir, checkExists, TemporaryDirectory, envFromDict
from plumbum import local
import logging
log = logging.getLogger(__name__)

DEFAULT_HASH = 'py3k'
NAME = 'tract_querier'
REPO = 'pnlbwh/tract_querier'

def make(commit=DEFAULT_HASH):
    """Downloads a lean version of tract_querier. Output is '$soft/tract_querier-<commit>'."""

    if commit != 'master':
        out = get_path(commit)
        if checkExists(out):
            return

    with local.tempdir() as tmpdir, local.cwd(tmpdir):
        repo = downloadGithubRepo(REPO, commit)
        sha, date = getCommitInfo(repo)
        out = get_path(sha)
        if checkExists(out):
            return

        # save space
        (repo / 'doc').delete()
        (repo / '.git').delete()

        log.info("Make '{out}'".format(**locals()))
        repo.move(out)

    # chmod('-R', 'a-w', out)
    # chmod('a-w', out)
    with open(out / 'env.sh', 'w') as f:
        f.write("export PATH={}:$PATH\n".format(out / 'scripts'))
        f.write("export PYTHONPATH={}:$PYTHONPATH\n".format(out))
    date_symlink = get_path(date)
    date_symlink.unlink()
    out.symlink(date_symlink)


def get_path(hash=DEFAULT_HASH):
    return getSoftDir() / '{}-{}'.format(NAME, hash)

def env_dict(hash):
    return {'PATH': get_path(hash) / 'scripts'
           ,'PYTHONPATH': get_path(hash)
    }

def env(hash):
    return envFromDict(env_dict(hash))
