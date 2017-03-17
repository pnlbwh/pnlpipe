from plumbum import local
import logging
import os
import sys

DEFAULT_VERSION = '5.3.0'

def readFreeSurferVersion():
    freesurferHome = os.environ.get('FREESURFER_HOME')

    if not freesurferHome:
        return None

    with open(local.path(freesurferHome) / "build-stamp.txt", 'r') as f:
        buildStamp = f.read()

    import re
    p = re.compile('v\d\.\d\.\d(-\w+)?$')
    try:
        version = p.search(buildStamp).group()[1:]
    except:
        raise Exception("Couldn't extract FreeSurfer version from {}/build-stamp.txt, either that file is malformed or the regex used to extract the version is incorrect.".format(freesurferHome))

    return version


def validate(version):
    currentVersion = readFreeSurferVersion()
    if not currentVersion:
        print("You need to make sure FreeSurfer version {} is installed \
and FREESURFER_HOME is set (currently unset).".format(version))
        sys.exit(1)
    if currentVersion != version:
        print("You need to make sure FreeSurfer version {} is installed \
and FREESURFER_HOME is set (currently set to version {}).".format(version,
                                                                          currentVersion))
        sys.exit(1)

    print("Correct version ({}) of FreeSurfer is set in FREESURFER_HOME.".format(version))

def make(version=DEFAULT_VERSION):
    validate(version)

def getPath(version=DEFAULT_VERSION):
    validate(version)
    return os.environ.get('FREESURFER_HOME')

