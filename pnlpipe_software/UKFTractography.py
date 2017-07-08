from pnlpipe_software import downloadGithubRepo, getCommitInfo, getSoftDir, checkExists, envFromDict
from plumbum import local, FG
from plumbum.cmd import cmake, chmod
import logging

DEFAULT_HASH = '421a7ad'

def make(commit=DEFAULT_HASH):

    dest = getSoftDir()
    if commit != 'master':
        out = local.path(dest / 'UKFTractography-' + commit)
        if checkExists(out):
            return

    blddir = dest / "UKFTractography-build"
    with local.cwd(dest):
        repo = downloadGithubRepo('pnlbwh/ukftractography', commit)
    sha, date = getCommitInfo(repo)

    out = local.path(dest / 'UKFTractography-' + sha)
    dateSymlink = dest / ('UKFTractography-'+date)

    if checkExists(out):
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
    binary.move(out)
    chmod('a-w', out)
    out.symlink(dateSymlink)
    blddir.delete()
    logging.info("Made '{}'".format(out))
    logging.info("Made '{}'".format(dateSymlink))


def get_path(ukfhash=DEFAULT_HASH):
    binary = getSoftDir() / ('UKFTractography-' + ukfhash)
    return binary
    # if not binary.exists():
    #     raise DoesNotExistException('{} doesn\'t exist')
    # return binary
