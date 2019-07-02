from pnlpipe_software import downloadGithubRepo, downloadGithubArchive, getCommitInfo, getSoftDir, checkExists, TemporaryDirectory
from plumbum import local
from plumbum.cmd import cmake, make
import logging

DEFAULT_HASH = '8141805'

def make(commit= DEFAULT_HASH):
    """Downloads t1 training set. Has masks, amygdala-hippocampus (left/right), and cingulate (left/right). Makes '<dest>/trainingDataT1AHCC'"""
    installTraining('trainingDataT1AHCC', commit)

def get_path(hash= DEFAULT_HASH):
    return local.path(getSoftDir() / 'trainingDataT1AHCC-' + hash)


def installTraining(repo, commit):
    dest = getSoftDir()
    if commit == 'master':
        logging.error(
            'installing master not implemented yet for training repos, specify github hash')
        import sys
        sys.exit(1)

    out = local.path(dest / repo + '-' + commit)
    if checkExists(out):
        return

    archive = downloadGithubArchive('pnlbwh/' + repo, commit)
    archive.move(out)

    with local.cwd(out):
        from plumbum.cmd import bash
        bash('./mktrainingcsv.sh', '.')
