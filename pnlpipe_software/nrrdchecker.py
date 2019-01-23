import sys
import os
from pnlpipe_software import getSoftDir, checkExists, TemporaryDirectory, downloadGithubRepo, getCommitInfo, envFromDict
import logging
logger = logging.getLogger(__name__)
from plumbum import local, FG
from plumbum.cmd import wget, tar

DEFAULT_HASH = 'ffc358f'

def on_partners_cluster():
    import socket
    if 'research.partners' in socket.gethostname():
        return True
    return False

def make(hash=DEFAULT_HASH):
    if hash != 'master':
        if checkExists(get_path(hash)):
            return

    with local.tempdir() as tmpdir, local.cwd(tmpdir):
        repo = downloadGithubRepo('reckbo/nrrdchecker', hash)
        sha, date = getCommitInfo(repo)
        with local.cwd(repo):
            if on_partners_cluster():
                import os
                os.system('module load stack')
            from plumbum.cmd import stack
            stack['setup'] & FG
            stack['build'] & FG
            binary = stack('exec', 'which', 'nrrdchecker')[:-1]
            get_path(sha).dirname.mkdir()
            local.path(binary).move(get_path(sha))

        symlink = get_path(date).dirname
        print("Make symlink: {} -> {}".format(symlink, get_path(sha).dirname))
        symlink.unlink()
        get_path(sha).dirname.symlink(symlink)

        logger.info("Made '{}'".format(get_path(sha)))
        logger.info("Made '{}'".format(symlink))

def get_path(hash=DEFAULT_HASH):
    return getSoftDir() / ('nrrdchecker-' + hash) / 'nrrdchecker'


def env_dict(hash):
    return { 'PATH': get_path(hash)}
