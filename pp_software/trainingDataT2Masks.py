from pp_software import downloadGithubRepo, getCommitInfo, getSoftDir, checkExists, TemporaryDirectory
from plumbum import local
from plumbum.cmd import cmake, make, chmod
import logging

def make(commit):
    """Downloads t2 training set (has masks only). Makes '<dest>/trainingDataT2Masks"""
    from pp_software.trainingDataT1AHCC import installTraining
    installTraining('trainingDataT2Masks', commit)

def getPath(hash):
    return local.path(getSoftDir() / repo + '-' + hash)
