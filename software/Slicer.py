import sys
from software import getSoftDir, checkExists, TemporaryDirectory
import logging
from plumbum import local, FG
from plumbum.cmd import wget, tar

DEFAULT_VERSION = '4.7.0'

URL= { '4.7.0': 'http://download.slicer.org/bitstream/608873' ,
        '4.5.0-1': ''
        }

def make(version=DEFAULT_VERSION):
    if not URL.get(version):
        logging.error("No download link set for '{}' in software/Slicer.py")
        sys.exit(1)
    if checkExists(getPath(version)):
        return
    with TemporaryDirectory() as tmpdir, local.cwd(tmpdir):
        tmpdir = local.path(tmpdir)
        wget[URL.get(version), '-O', 'slicer.tar.gz'] & FG
        tar['zxvf', 'slicer.tar.gz'] & FG
        (tmpdir // 'Slicer-*')[0].move(getDir(version))
        logging.info("Made '{}'".format(getPath(version)))

def getDir(version=DEFAULT_VERSION):
    return getSoftDir() / ('Slicer-' + version + '-linux-amd64')

def getPath(version=DEFAULT_VERSION):
    return getDir(version) / 'Slicer'
