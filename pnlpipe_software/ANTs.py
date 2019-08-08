from pnlpipe_software import downloadGithubRepo, getCommitInfo, getSoftDir, checkExists, envFromDict
import psutil
from plumbum import local, FG
from plumbum.cmd import cmake, cp
import logging

DEFAULT_HASH = 'ca32228'

def make(commit=DEFAULT_HASH):

    softdir = getSoftDir()

    blddir = softdir / "ANTs-build"

    with local.cwd(softdir):
        repo = downloadGithubRepo('ANTsX/ANTs', commit)
    sha, date = getCommitInfo(repo)

    out = get_path(sha)
    # if output binary directory already exists, then return
    if checkExists(out):
        return

    logging.info("Build code:")

    blddir.mkdir()
    with local.cwd(blddir):
        cmake(repo)
        import plumbum.cmd
        plumbum.cmd.make['-j', psutil.cpu_count(logical=False)] & FG


    # copy ANTs scripts
    cp('-a', (softdir / 'ANTs' / 'Scripts').list(), blddir / 'bin')

    # move binary directory
    (blddir / 'bin').move(out)

    # write PATH and ANTSPATH
    with open(out / 'env.sh', 'w') as f:
        f.write("export PATH={}:$PATH\n".format(out))
        f.write("export ANTSPATH={}\n".format(out))


    # generate symbolink links
    symlink = get_path(date)
    print("Make symlink: {} -> {}".format(symlink, get_path(sha)))
    symlink.unlink()
    get_path(sha).symlink(symlink)

    logging.info("Made '{}'".format(out))


def get_path(hash=DEFAULT_HASH):
    return getSoftDir() / ('ANTs-bin-' + hash)

def env_dict(hash):
    return {'PATH': get_path(hash), 'ANTSPATH': get_path(hash)}

def env(bthash):
    return envFromDict(env_dict(bthash))
