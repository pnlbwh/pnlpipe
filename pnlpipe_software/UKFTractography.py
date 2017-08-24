from pnlpipe_software import downloadGithubRepo, getCommitInfo, getSoftDir, checkExists, envFromDict
from plumbum import local, FG
from plumbum.cmd import cmake
import logging

DEFAULT_HASH = '421a7ad'

def make(commit=DEFAULT_HASH):

    softdir = getSoftDir()

    if commit != 'master':
        if checkExists(get_path(commit)):
            return

    blddir = softdir / "UKFTractography-build"

    with local.cwd(softdir):
        repo = downloadGithubRepo('pnlbwh/ukftractography', commit)
    sha, date = getCommitInfo(repo)

    outbinary = get_path(sha)

    if checkExists(outbinary):
        return

    logging.info("Build code:")

    blddir.mkdir()
    with local.cwd(blddir):
        cmake(repo)
        import plumbum.cmd
        plumbum.cmd.make['-j', 16] & FG

    binary1 = blddir / 'ukf/bin/UKFTractography'
    binary2 = blddir / 'UKFTractography-build/ukf/bin/UKFTractography' # later commits
    binary = binary1 if binary1.exists() else binary2

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
    return getSoftDir() / ('UKFTractography-' + hash) / 'UKFTractography'


def env_dict(hash):
    return { 'PATH': get_path(hash).dirname }
