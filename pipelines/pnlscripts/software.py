#!/usr/bin/env python
from __future__ import print_function
import sys
try:
    from plumbum import local, FG, cli
except ImportError:
    print('Couldn\'t import plumbum')
    print('Did you forget to load python environment? (e.g. source activate pyppl)')
    sys.exit(1)
from plumbum.cmd import  git, cmake, make, chmod
import logging
from util import logfmt, TemporaryDirectory

logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))

def downloadGithubArchive(ownerrepo, commit='master'):
    """Makes 'repo-<commit>' directory."""
    url = 'https://github.com/{ownerrepo}/archive/{commit}.tar.gz'.format(**locals())
    repo = ownerrepo.split('/')[1]
    from plumbum.cmd import curl, tar
    (curl['-L', url] | tar['xz'])()
    return local.path(repo+'-'+commit)

def getCommitInfo(repo_path):
    with local.cwd(local.path(repo_path)):
        sha = git('rev-parse', '--short', 'HEAD')[:-1]
        date = git('show', '-s', '--format=%cd', '--date=short')[:-1]
    return (sha, date)

def downloadGithubRepo(ownerrepo, commit='master'):
    url = 'https://github.com/{ownerrepo}.git'.format(**locals())
    repo = ownerrepo.split('/')[1]
    if not local.path(repo).exists():
        git('clone', url)
    with local.cwd(repo):
        git('checkout', 'master')
        git('pull', 'origin')
        git('checkout', commit)
    return local.path(repo)

class MakeSoftware(cli.Application):
    """Software installer."""

    dest = cli.SwitchAttr(['-d', '--dest'], cli.ExistingDirectory, help="Root directory in which to install repo.  If omitted, will use '$soft' environment variable (if empty will default to current directory).", envname='soft')
    commit = cli.SwitchAttr(['-c', '--commit'], help='GitHub hash commit. If omitted will get latest commit from the master branch.'
                             ,mandatory=False
                             ,default="master")

    def main(self, *args):
        if args:
            print("Unknown command {0!r}".format(args[0]))
            return 1
        print("Installing to: " + self.dest)
        if not self.nested_command:
            print("No command given")
            return 1   # error exit code

@MakeSoftware.subcommand("brainstools")
class BrainsTools(cli.Application):
    """Downloads and compiles BRAINSTools binaries. Output is 'BRAINSTools-bin-<hash>'."""

    def main(self):
        blddir = self.parent.dest / "BRAINSTools-build"
        with local.cwd(self.parent.dest):
            repo = downloadGithubRepo('BRAINSia/BRAINSTools', self.parent.commit)
        sha, date = getCommitInfo(repo)
        out = self.parent.dest / ('BRAINSTools-bin-'+sha)
        symlink = self.parent.dest / ('BRAINSTools-bin-'+date)
        if out.exists():
            logging.warning(out + ' already exists, skipping')
            sys.exit(0)
        logging.info("Build code:")
        blddir.mkdir()
        with local.cwd(blddir):
            cmake(repo
            ,"-DBRAINSTools_INSTALL_DEVELOPMENT=OFF"
            ,"-DBRAINSTools_MAX_TEST_LEVEL=0"
            ,"-DBRAINSTools_SUPERBUILD=ON"
            ,"-DBRAINSTools_USE_QT=OFF"
            ,"-DBRAINS_DEBUG_IMAGE_WRITE=OFF"
            ,"-DBUILD_STYLE_UTILS=OFF"
            ,"-DBUILD_TESTING=OFF"
            ,"-DCMAKE_BUILD_TYPE=Release"
            ,"-DCMAKE_COLOR_MAKEFILE=ON"
            ,"-DCMAKE_EXE_LINKER_FLAGS=' '"
            ,"-DCMAKE_EXE_LINKER_FLAGS_DEBUG="
            ,"-DCMAKE_EXE_LINKER_FLAGS_MINSIZEREL="
            ,"-DCMAKE_EXE_LINKER_FLAGS_RELEASE="
            ,"-DCMAKE_EXE_LINKER_FLAGS_RELWITHDEBINFO="
            ,"-DCMAKE_EXPORT_COMPILE_COMMANDS=OFF"
            ,"-DCMAKE_INSTALL_PREFIX:PATH=/usr/local"
            ,"-DCMAKE_MODULE_LINKER_FLAGS=' '"
            ,"-DCMAKE_MODULE_LINKER_FLAGS_DEBUG="
            ,"-DCMAKE_MODULE_LINKER_FLAGS_MINSIZEREL="
            ,"-DCMAKE_MODULE_LINKER_FLAGS_RELEASE="
            ,"-DCMAKE_MODULE_LINKER_FLAGS_RELWITHDEBINFO="
            ,"-DCMAKE_PROJECT_NAME:STATIC=SuperBuild_BRAINSTools"
            ,"-DCMAKE_SHARED_LINKER_FLAGS=' '"
            ,"-DCMAKE_SHARED_LINKER_FLAGS_DEBUG="
            ,"-DCMAKE_SHARED_LINKER_FLAGS_MINSIZEREL="
            ,"-DCMAKE_SHARED_LINKER_FLAGS_RELEASE="
            ,"-DCMAKE_SHARED_LINKER_FLAGS_RELWITHDEBINFO="
            ,"-DCMAKE_SKIP_INSTALL_RPATH=NO"
            ,"-DCMAKE_SKIP_RPATH=NO"
            ,"-DCMAKE_STATIC_LINKER_FLAGS="
            ,"-DCMAKE_STATIC_LINKER_FLAGS_DEBUG="
            ,"-DCMAKE_STATIC_LINKER_FLAGS_MINSIZEREL="
            ,"-DCMAKE_STATIC_LINKER_FLAGS_RELEASE="
            ,"-DCMAKE_STATIC_LINKER_FLAGS_RELWITHDEBINFO="
            ,"-DCMAKE_USE_RELATIVE_PATHS=OFF"
            ,"-DCMAKE_VERBOSE_MAKEFILE=FALSE"
            ,"-DCOVERAGE_EXTRA_FLAGS=-l"
            ,"-DCTEST_SUBMIT_RETRY_COUNT=3"
            ,"-DCTEST_SUBMIT_RETRY_DELAY=5"
            ,"-DDART_TESTING_TIMEOUT=1500"
            ,"-DEXTERNAL_PROJECT_BUILD_TYPE=Release"
            ,"-DFORCE_EXTERNAL_BUILDS=OFF"
            ,"-DITK_VERSION_MAJOR=4"
            ,"-DSuperBuild_BRAINSTools_BUILD_DICOM_SUPPORT=ON"
            ,"-DSuperBuild_BRAINSTools_USE_CTKAPPLAUNCHER=OFF"
            ,"-DSuperBuild_BRAINSTools_USE_GIT_PROTOCOL=ON"
            ,"-DUSE_ANTS=ON"
            ,"-DUSE_AutoWorkup=OFF"
            ,"-DUSE_BRAINSABC=OFF"
            ,"-DUSE_BRAINSConstellationDetector=OFF"
            ,"-DUSE_BRAINSContinuousClass=OFF"
            ,"-DUSE_BRAINSCreateLabelMapFromProbabilityMaps=OFF"
            ,"-DUSE_BRAINSCut=OFF"
            ,"-DUSE_BRAINSDWICleanup=OFF"
            ,"-DUSE_BRAINSDemonWarp=OFF"
            ,"-DUSE_BRAINSFit=OFF"
            ,"-DUSE_BRAINSInitializedControlPoints=OFF"
            ,"-DUSE_BRAINSLabelStats=OFF"
            ,"-DUSE_BRAINSLandmarkInitializer=OFF"
            ,"-DUSE_BRAINSMultiModeSegment=OFF"
            ,"-DUSE_BRAINSMultiSTAPLE=OFF"
            ,"-DUSE_BRAINSMush=OFF"
            ,"-DUSE_BRAINSPosteriorToContinuousClass=OFF"
            ,"-DUSE_BRAINSROIAuto=OFF"
            ,"-DUSE_BRAINSResample=OFF"
            ,"-DUSE_BRAINSSnapShotWriter=OFF"
            ,"-DUSE_BRAINSStripRotation=OFF"
            ,"-DUSE_BRAINSSurfaceTools=OFF"
            ,"-DUSE_BRAINSTalairach=OFF"
            ,"-DUSE_BRAINSTransformConvert=OFF"
            ,"-DUSE_ConvertBetweenFileFormats=ON"
            ,"-DUSE_DWIConvert=ON"
            ,"-DUSE_DebugImageViewer=OFF"
            ,"-DUSE_GTRACT=OFF"
            ,"-DUSE_ICCDEF=OFF"
            ,"-DUSE_ImageCalculator=OFF"
            ,"-DUSE_ReferenceAtlas=OFF"
            ,"-DUSE_SYSTEM_DCMTK=OFF"
            ,"-DUSE_SYSTEM_ITK=OFF"
            ,"-DUSE_SYSTEM_SlicerExecutionModel=OFF"
            ,"-DUSE_SYSTEM_VTK=OFF"
            ,"-DVTK_GIT_REPOSITORY=git://vtk.org/VTK.git"
            )
            make['-j', '16'] & FG
        (blddir / 'bin').move(out)
        with open(blddir / 'ANTs/Scripts/antsRegistrationSyN.sh', 'r') as src:
            with open(out / 'antsRegistrationSyN.sh', 'w') as dest:
                for idx, line in enumerate(src):
                    if idx == 0:
                        dest.write('#!/usr/bin/env bash')
                    else:
                        dest.write(line)
        # (blddir / 'ANTs/Scripts/antsRegistrationSyN.sh').copy(out)
        chmod('a-w', out.glob('*'))
        chmod('a-w', out)
        out.symlink(symlink)
	blddir.delete()

@MakeSoftware.subcommand("ukftractography")
class Ukf(cli.Application):
    """Downloads and compiles UKFTractography binary. Output is '<dest>/UKFTractography-<commit>'."""
    def main(self):
        blddir = self.parent.dest / "UKFTractography-build"
        with local.cwd(self.parent.dest):
            repo = downloadGithubRepo('pnlbwh/ukftractography', self.parent.commit)
        sha, date = getCommitInfo(repo)
        out = local.path(self.parent.dest / 'UKFTractography-' + sha)
        dateSymlink = self.parent.dest / ('UKFTractography-'+date)
        if out.exists():
            logging.warning(out + ' already exists, skipping')
            sys.exit(0)
        logging.info("Build code:")
        blddir.mkdir()
        with local.cwd(blddir):
            cmake(repo)
            make['-j', '16'] & FG
        binary1 = blddir / 'ukf/bin/UKFTractography'
        binary2 = blddir / 'UKFTractography-build/ukf/bin/UKFTractography' # later commits
        binary = binary1 if binary1.exists() else binary2
        binary.move(out)
        chmod('a-w', out)
        out.symlink(dateSymlink)
        blddir.delete()
        logging.info("Made '{}'".format(out))
        logging.info("Made '{}'".format(dateSymlink))

@MakeSoftware.subcommand("tractquerier")
class TractQuerier(cli.Application):
    """Downloads a lean version of tract_querier. Output is '<dest>/tract_querier-<commit>'."""
    def main(self):
        with TemporaryDirectory() as tmpdir, local.cwd(tmpdir):
            repo = downloadGithubRepo('demianw/tract_querier', self.parent.commit)
            sha, date = getCommitInfo(repo)
            # save space
            (repo / 'doc').delete()
            (repo / '.git').delete()
            out = local.path(self.parent.dest / 'tract_querier-' + sha)
            if out.exists():
                logging.warning(out + ' already exists, quitting.')
                sys.exit(0)
            logging.info("Make '{out}'".format(**locals()))
            repo.move(out)
        chmod('-R', 'a-w', out)
        chmod('a-w', out)
        date_symlink = self.parent.dest / 'tract_querier-' + date
        out.symlink(date_symlink)

def installTraining(repo, commit, dest):
    out = dest/repo
    if out.exists():
        logging.warning(out + ' already exists, skipping')
        return
    archive = downloadGithubArchive('pnlbwh/'+repo, commit)
    archive.move(out)
    with local.cwd(out):
        from plumbum.cmd import bash
        bash('./mktrainingcsv.sh', '.')
        chmod('a-w', local.cwd.glob('*'))

@MakeSoftware.subcommand("trainingt2s")
class T2s(cli.Application):
    """Downloads t2 training set (has masks only). Makes '<dest>/trainingDataT2Masks"""
    def main(self):
        installTraining('trainingDataT2Masks', self.parent.commit, self.parent.dest)

@MakeSoftware.subcommand("trainingt1s")
class T1s(cli.Application):
    """Downloads t1 training set. Has masks, amygdala-hippocampus (left/right), and cingulate (left/right). Makes '<dest>/trainingDataT1AHCC'"""
    def main(self):
        installTraining('trainingDataT1AHCC', self.parent.commit, self.parent.dest)


if __name__ == '__main__':
    MakeSoftware.run()
