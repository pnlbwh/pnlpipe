import sys
from software import downloadGithubArchive
from software import getSoftDir, checkExists, TemporaryDirectory
import logging
from plumbum import local, FG

GITHUB_REPO = 'Washington-University/Pipelines'
DEFAULT_VERSION = '3.21.0'

def make(version=DEFAULT_VERSION):
    if checkExists(getPath(version)):
        return
    with TemporaryDirectory() as tmpdir, local.cwd(tmpdir):
        d = downloadGithubArchive(GITHUB_REPO, 'v' + version)
        d.move(getPath(version))
        logging.info("Made '{}'".format(getPath(version)))

def getPath(version=DEFAULT_VERSION):
    return getSoftDir() / ('HCPPipelines-' + version)

def env(version):
    repo = getPath(version)
    return local.env(
        HCPPIPEDIR = repo,
        HCPPIPEDIR_dMRI = repo/'DiffusionPreprocessing/scripts',
        HCPPIPEDIR_Config = repo/'global/config',
        HCPPIPEDIR_Global = repo/'global/scripts'
        )
