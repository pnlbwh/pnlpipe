from software_recipes.__lib import downloadGithubRepo, getCommitInfo, getSoftDir, checkExists
from plumbum import local
from plumbum.cmd import cmake, make, chmod
import logging

def make(commit):
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

    if checkExists(out):
        return

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
