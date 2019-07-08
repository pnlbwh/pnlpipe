from pnlpipe_software import downloadGithubRepo, getCommitInfo, getSoftDir, checkExists, envFromDict
import psutil
from plumbum import local, FG
from plumbum.cmd import cmake
import logging

DEFAULT_HASH = '54cfd51'

def make(commit=DEFAULT_HASH):

    softdir = getSoftDir()

    if commit != 'master':
        if checkExists(get_path(commit)):
            return

    blddir = softdir / "dcm2niix-build"

    with local.cwd(softdir):
        repo = downloadGithubRepo('rordenlab/dcm2niix', commit)
    sha, date = getCommitInfo(repo)

    outbinary = get_path(sha)

    if checkExists(outbinary):
        return

    logging.info("Build code:")

    blddir.mkdir()
    with local.cwd(blddir):
        cmake(repo)
        import plumbum.cmd
        plumbum.cmd.make['-j', psutil.cpu_count(logical=False)] & FG

    binary = blddir / 'bin/dcm2niix'

    outbinary.dirname.mkdir()

    binary.move(outbinary)
    # chmod('a-w', outbinary)

    with open(outbinary.dirname / 'env.sh', 'w') as f:
        f.write("export PATH={}:$PATH".format(outbinary.dirname))

    symlink = get_path(date).dirname
    print("Make symlink: {} -> {}".format(symlink, get_path(sha).dirname))
    symlink.unlink()
    get_path(sha).dirname.symlink(symlink)

    blddir.delete()

    logging.info("Made '{}'".format(outbinary))
    logging.info("Made '{}'".format(get_path(date)))


def get_path(hash=DEFAULT_HASH):
    return getSoftDir() / ('dcm2niix-' + hash) / 'dcm2niix'


def env_dict(hash):
    return { 'PATH': get_path(hash).dirname }


def env(bthash):
    return envFromDict(env_dict(bthash))
