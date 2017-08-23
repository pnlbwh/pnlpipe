import sys
from pnlpipe_software import downloadGithubArchive, getSoftDir, checkExists, TemporaryDirectory, envFromDict
import logging
log = logging.getLogger(__name__)
from plumbum import local, FG

GITHUB_REPO = 'Washington-University/Pipelines'
DEFAULT_VERSION = '3.17.0'


def make(version=DEFAULT_VERSION):
    if checkExists(get_path(version)):
        return
    with TemporaryDirectory() as tmpdir, local.cwd(tmpdir):
        d = downloadGithubArchive(GITHUB_REPO, 'v' + version)
        d.move(get_path(version))
        log.info("Made '{}'".format(get_path(version)))


def get_path(version=DEFAULT_VERSION):
    return getSoftDir() / ('HCPPipelines-' + version)


def env_dict(version):
    repo = get_path(version)
    return {
        'PATH': repo / 'DiffusionPreprocessing',
        'HCPPIPEDIR': repo,
        'HCPPIPEDIR_dMRI': repo / 'DiffusionPreprocessing/scripts',
        'HCPPIPEDIR_Config': repo / 'global/config',
        'HCPPIPEDIR_Global': repo / 'global/scripts'
    }


def env(hash):
    return envFromDict(env_dict(hash))
