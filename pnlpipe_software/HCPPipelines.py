import sys
from pnlpipe_software import downloadGithubArchive, getSoftDir, checkExists, TemporaryDirectory, envFromDict
import logging
from plumbum import local, FG

GITHUB_REPO = 'Washington-University/Pipelines'
DEFAULT_VERSION = '3.17.0'


def make(version=DEFAULT_VERSION):
    if checkExists(getPath(version)):
        return
    with TemporaryDirectory() as tmpdir, local.cwd(tmpdir):
        d = downloadGithubArchive(GITHUB_REPO, 'v' + version)
        d.move(getPath(version))
        logging.info("Made '{}'".format(getPath(version)))


def getPath(version=DEFAULT_VERSION):
    return getSoftDir() / ('HCPPipelines-' + version)


def envDict(version):
    repo = getPath(version)
    return {
        'PATH': repo / 'DiffusionPreprocessing',
        'HCPPIPEDIR': repo,
        'HCPPIPEDIR_dMRI': repo / 'DiffusionPreprocessing/scripts',
        'HCPPIPEDIR_Config': repo / 'global/config',
        'HCPPIPEDIR_Global': repo / 'global/scripts'
    }


def env(bthash):
    return envFromDict(envDict(bthash))
