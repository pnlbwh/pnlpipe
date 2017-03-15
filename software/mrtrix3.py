import sys
import os
from software import getSoftDir, checkExists, TemporaryDirectory, downloadGithubRepo
import logging
from plumbum import local, FG
from plumbum.cmd import wget, tar

DEFAULT_VERSION = '97e4b3b'

def make(version=DEFAULT_VERSION):
    if checkExists(getPath(version)):
        sys.exit(1)
    with TemporaryDirectory() as tmpdir, local.cwd(tmpdir):
        tmpdir = local.path(tmpdir)
        repo = downloadGithubRepo('MRtrix3/mrtrix3', version)
        with local.cwd(repo):
            os.system('./configure')
            os.system('./build')
            os.system('mv ./release {}'.format(getPath(version)))

def getPath(version=DEFAULT_VERSION):
    return getSoftDir() / ('mrtrix3-' + version)
