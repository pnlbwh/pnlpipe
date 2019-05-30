from pnlpipe_software import downloadGithubRepo, getCommitInfo, getSoftDir, checkExists, prefixPATH, envFromDict
import psutil, sys
from plumbum import local, FG
from plumbum.cmd import cmake, make
import logging
log = logging.getLogger(__name__)
import os


DEFAULT_HASH = '81a409d'

ANTSPATH= os.getenv('ANTSPATH', None)
if not ANTSPATH:
    ANTSPATH= local.path(os.environ['CONDA_PREFIX']) / 'bin'

def make(commit=DEFAULT_HASH, delete=False):
    """Downloads and compiles BRAINSTools binaries. Output is '$soft/BRAINSTools-bin-<hash>'."""

    dest = getSoftDir()

    if commit != 'master':
        out = dest / ('BRAINSTools-bin-'+commit)
        if checkExists(out):
            return

    blddir = dest / "BRAINSTools-build"
    with local.cwd(dest):
        repo = downloadGithubRepo('BRAINSia/BRAINSTools', commit)
    sha, date = getCommitInfo(repo)

    out = dest / ('BRAINSTools-bin-'+sha)
    symlink = dest / ('BRAINSTools-bin-'+date)
    symlink.unlink()

    log.info("Make '{}'".format(out))
    log.info("Make '{}'".format(symlink))

    if checkExists(out):
        return

    logging.info("Build code:")
    blddir.mkdir()
    with local.cwd(blddir):
        cmake(repo
              ,"-DBRAINSTools_BUILD_DICOM_SUPPORT:BOOL=OFF"
              ,"-DBRAINSTools_MAX_TEST_LEVEL:STRING=0"
              ,"-DBRAINSTools_REQUIRES_VTK:BOOL=OFF"
              ,"-DBRAINSTools_USE_CTKAPPLAUNCHER:BOOL=OFF"
              ,"-DBUILD_TESTING:BOOL=OFF"
              ,"-DUSE_ANTS:BOOL=OFF"
              ,"-DUSE_AutoWorkup:BOOL=OFF"
              ,"-DUSE_BRAINSABC:BOOL=OFF"
              ,"-DUSE_BRAINSConstellationDetector:BOOL=OFF"
              ,"-DUSE_BRAINSDWICleanup:BOOL=OFF"
              ,"-DUSE_BRAINSFit:BOOL=OFF"
              ,"-DUSE_BRAINSInitializedControlPoints:BOOL=OFF"
              ,"-DUSE_BRAINSLabelStats:BOOL=OFF"
              ,"-DUSE_BRAINSLandmarkInitializer:BOOL=OFF"
              ,"-DUSE_BRAINSROIAuto:BOOL=OFF"
              ,"-DUSE_BRAINSResample:BOOL=OFF"
              ,"-DUSE_BRAINSSnapShotWriter:BOOL=OFF"
              ,"-DUSE_BRAINSStripRotation:BOOL=OFF"
              ,"-DUSE_BRAINSTransformConvert:BOOL=OFF"
              ,"-DUSE_DWIConvert:BOOL=OFF"
              ,"-DUSE_ImageCalculator:BOOL=OFF"
              ,"-DUSE_ReferenceAtlas:BOOL=OFF"
              ,"-DCMAKE_SKIP_INSTALL_RPATH:BOOL=ON"
              ,"-DCMAKE_SKIP_RPATH:BOOL=ON"
              )

        import plumbum.cmd
        plumbum.cmd.make['-j', psutil.cpu_count(logical=False)] & FG
    (blddir / 'bin').move(out)


    with open(out / 'env.sh', 'w') as f:
        f.write("export PATH={}:$PATH\n".format(out))
        f.write("export ANTSPATH={}\n".format(ANTSPATH))
    symlink.unlink()
    out.symlink(symlink)

    log.info("Made '{}'".format(get_path(sha)))
    log.info("Made '{}'".format(symlink))


def get_path(bthash=DEFAULT_HASH):
    btpath = getSoftDir() / ('BRAINSTools-bin-' + bthash)
    return btpath

def env_dict(bthash):
    btpath = get_path(bthash)
    return { 'PATH': btpath, 'ANTSPATH': ANTSPATH}

def env(bthash):
    return envFromDict(env_dict(bthash))
