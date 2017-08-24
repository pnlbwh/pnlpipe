import os
from pnlpipe_software import downloadGithubRepo, getCommitInfo, getSoftDir, checkExists, TemporaryDirectory, envFromDict
from plumbum import local, FG
# from plumbum.cmd import chmod
import logging

DEFAULT_HASH = '664bb45'

NAME = 'whitematteranalysis'
REPO = 'SlicerDMRI/' + NAME

def make(commit=DEFAULT_HASH):
    """Downloads whitematteranalysis. Output is '$soft/whitematteranalysis-<commit>'."""
    dest = getSoftDir()

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
        (repo / 'tests').delete()
        (repo / '.git').delete()

        logging.info("Make '{out}'".format(**locals()))
        repo.move(out)

    # chmod('-R', 'a-w', out)
    # chmod('a-w', out)
    with open(out / 'env.sh', 'w') as f:
        f.write("export PATH={}:$PATH\n".format(out / 'bin'))
        f.write("export PYTHONPATH={}:$PYTHONPATH\n".format(out))

    # compile cython files
    with local.cwd(out):
        from plumbum.cmd import python
        python['setup.py', 'build_ext', '--inplace'] & FG

    date_symlink = get_path(date)
    date_symlink.unlink()
    out.symlink(date_symlink)


def get_path(hash=DEFAULT_HASH):
    path = getSoftDir() / '{}-{}'.format(NAME, hash)
    return path

def env_dict(hash):
    return {'PATH': get_path(hash) / 'bin'
           ,'PYTHONPATH': get_path(hash)
    }

def env(hash):
    return envFromDict(env_dict(hash))
