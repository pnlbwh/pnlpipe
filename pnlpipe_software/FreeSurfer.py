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
        raise Exception("You need to make sure FreeSurfer version >= {} is installed \
and FREESURFER_HOME is set (currently unset).".format(version))
    if currentVersion < version:       
        raise Exception("You need to make sure FreeSurfer version >= {} is installed \
and FREESURFER_HOME is set (currently set to version {}).".format(version,
                                                                          currentVersion))

    print("Version ({}) of FreeSurfer is set in FREESURFER_HOME.".format(version))

def make(version=DEFAULT_VERSION):
    try:
        validate(version)
    except Exception as e:
        print('')
        print('**WARNING**')
        print(e)
        print('')

def get_path(version=DEFAULT_VERSION):
    return os.environ.get('FREESURFER_HOME', '(FREESURFER_HOME not set)')
