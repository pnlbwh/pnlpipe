#!/usr/bin/env python
from plumbum import local, FG, cli
from pnlscripts.util.scripts import alignAndCenter_py, convertdwi_py, atlas_py, fs2dwi_py, eddy_py
from pnlscripts.util import TemporaryDirectory
import sys
import yaml
import pickle
from pipelinelib import logfmt, Src, GeneratedNode, update, need, needDeps, OUTDIR, log

# Must be set by client code
BTHASH = None

defaultUkfParams = [("Ql", "70"), ("Qm", "0.001"), ("Rs", "0.015"),
                    ("numTensor", "2"), ("recordLength", "1.7"),
                    ("seedFALimit", "0.18"), ("seedsPerVoxel", "10"),
                    ("stepLength", "0.3")]

class DoesNotExistException(Exception):
    pass


def getSoftDir():
    import os
    environSoft = os.environ.get('soft', None)
    if 'SOFTDIR' in globals():
        return local.path(SOFTDIR)
    if environSoft:
        return local.path(environSoft)
    log.error(
        "Environment variable '$soft' must be set. This is the directory where BRAINSTools, UKFTractography, tract_querier, and the training data are installed.")
    sys.exit(1)


def getBrainsToolsPath(bthash):
    btpath = getSoftDir() / ('BRAINSTools-bin-' + bthash)
    if not btpath.exists():
        raise DoesNotExistException(
            "{} doesn\'t exist, make it first with 'pnlscripts/software.py --commit {} brainstools".format(
                btpath, bthash))
    return btpath

def getUKFTractographyPath(ukfhash):
    binary = getSoftDir() / ('UKFTractography-' + ukfhash)
    if not binary.exists():
        raise DoesNotExistException(
            '{} doesn\'t exist, make it first with \'pnlscripts/software.py --commit {} ukftractography\''.format(
                binary, ukfhash))
    return binary

def getTractQuerierPath(hash):
    path = getSoftDir() / ('tract_querier-' + hash)
    if not path.exists():
        raise DoesNotExistException(
            "{} doesn\'t exist, make it first with 'pnlscripts/software.py --commit {} tractquerier".format(
                path, hash))
    return path

def getTrainingDataT1AHCCCsv():
    csv = getSoftDir() / 'trainingDataT1AHCC/trainingDataT1AHCC-hdr.csv'
    if not csv.exists():
        raise DoesNotExistException(
            '{} doesn\'t exist, make it first with \'pnlscripts/software.py t1s\''.format(
                csv))
    return csv



def formatParams(paramsList):
    formatted = [['--' + key, val] for key, val in paramsList]
    return [item for pair in formatted for item in pair]


def brainsToolsEnv():
    if not BTHASH:
        print(
            'BTHASH not set in nodes.py, set this (import nodes; nodes.BTHASH = <hash>)')
    btpath = getBrainsToolsPath(BTHASH)
    newpath = ':'.join(str(p) for p in [btpath] + local.env.path)
    return local.env(PATH=newpath, ANTSPATH=btpath)


def convertImage(i, o):
    if i.suffixes == o.suffixes:
        i.copy(o)
    with brainsToolsEnv():
        from plumbum.cmd import ConvertBetweenFileFormats
        ConvertBetweenFileFormats(i, o)



def tractQuerierEnv(hash):
    path = getTractQuerierPath(hash)
    newPath = ':'.join(str(p) for p in [path] + local.env.path)
    import os
    pythonPath = os.environ.get('PYTHONPATH')
    newPythonPath = path if not pythonPath else '{}:{}'.format(path,
                                                               pythonPath)
    return local.env(PATH=newPath, PYTHONPATH=newPythonPath)



def dependsOnBrainsTools(node):
    if node.__class__.__bases__[0].__name__ == 'BrainsToolsNode':
        return True
    if not node.deps:
        return False
    return any(dependsOnBrainsTools(dep) for dep in node.deps)


class PNLNode(GeneratedNode):
    def path(self):
        ext = getattr(self, 'ext', '.nrrd')
        if not ext.startswith('.'):
            ext = '.' + ext
        outdir = OUTDIR / self.caseid
        return outdir / (self.show() + '-' + BTHASH + '-' + self.caseid + ext)


class BrainsToolsNode(PNLNode):
    pass


class DwiEd(BrainsToolsNode):
    """ Eddy current correction. Accepts nrrd only. """

    def __init__(self, caseid, dwi):
        self.deps = [dwi]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with brainsToolsEnv():
            eddy_py['-i', self.dwi.path(), '-o', self.path()] & FG


class DwiXc(BrainsToolsNode):
    """ Axis align and center a dWI. Accepts nrrd or nifti. """

    def __init__(self, caseid, dwi):
        self.deps = [dwi]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with brainsToolsEnv():
            convertdwi_py['-f', '-i', self.dwi.path(), '-o', self.path()] & FG
            alignAndCenter_py['-i', self.path(), '-o', self.path()] & FG


class DwiEpi(BrainsToolsNode):
    """Epi correction. """

    def __init__(self, caseid, dwi, dwimask, t2, t2mask):
        self.deps = [dwi, t2, t2mask]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with brainsToolsEnv():
            from pnlscripts.util.scripts import epi_py
            epi_py('--dwi', self.dwi.path(), '--dwimask', self.dwimask.path(),
                   '--t2', self.t2.path(), '--t2mask', self.t2mask.path(),
                   '-o', self.path())


class DwiMaskHcpBet(BrainsToolsNode):
    def __init__(self, caseid, dwi):
        self.deps = [dwi]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        from plumbum.cmd import bet
        with brainsToolsEnv(), TemporaryDirectory() as tmpdir:
            tmpdir = local.path(tmpdir)
            nii = tmpdir / 'dwi.nii.gz'
            convertdwi_py('-i', self.dwi.path(), '-o', nii)
            bet(nii, tmpdir / 'dwi', '-m', '-f', '0.1')
            convertImage(tmpdir / 'dwi_mask.nii.gz', self.path(), BTHASH)


class UkfDefault(BrainsToolsNode):
    def __init__(self, caseid, dwi, dwimask, ukfhash):
        self.deps = [dwi, dwimask]
        self.opts = [ukfhash]
        self.ext = 'vtk'
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with brainsToolsEnv(), TemporaryDirectory() as tmpdir:
            tmpdir = local.path(tmpdir)
            tmpdwi = tmpdir / 'dwi.nrrd'
            tmpdwimask = tmpdir / 'dwimask.nrrd'
            convertdwi_py('-i', self.dwi.path(), '-o', tmpdwi)
            convertImage(self.dwimask.path(), tmpdwimask, BTHASH)
            params = ['--dwiFile', tmpdwi, '--maskFile', tmpdwimask,
                      '--seedsFile', tmpdwimask, '--recordTensors', '--tracts',
                      self.path()] + formatParams(defaultUkfParams)
            ukfpath = getUKFTractographyPath(self.ukfhash)
            log.info(' Found UKF at {}'.format(ukfpath))
            ukfbin = local[ukfpath]
            ukfbin(*params)


class StrctXc(BrainsToolsNode):
    def __init__(self, caseid, strct):
        self.deps = [strct]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with brainsToolsEnv():
            alignAndCenter_py['-i', self.strct.path(), '-o', self.path()] & FG


class T2wMaskRigid(BrainsToolsNode):
    def __init__(self, caseid, t2, t1, t1mask):
        self.deps = [t2, t1, t1mask]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with brainsToolsEnv():
            from pnlscripts.util.scripts import makeRigidMask_py
            makeRigidMask_py('-i', self.t1.path(), '--lablemap',
                             self.t1mask.path(), '--target', self.t2.path(),
                             '-o', self.path())


class T1wMaskMabs(BrainsToolsNode):
    def __init__(self, caseid, t1):
        self.deps = [t1]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with TemporaryDirectory() as tmpdir, brainsToolsEnv():
            tmpdir = local.path(tmpdir)
            # antsRegistration can't handle a non-conventionally named file, so
            # we need to pass in a conventionally named one
            tmpt1 = tmpdir / ('t1' + ''.join(self.t1.path().suffixes))
            from plumbum.cmd import ConvertBetweenFileFormats
            ConvertBetweenFileFormats[self.t1.path(), tmpt1] & FG
            atlas_py['--mabs', '-t', tmpt1, '-o', tmpdir, 'csv',
                     getTrainingDataT1AHCCCsv()] & FG
            (tmpdir / 'mask.nrrd').copy(self.path())


class FreeSurferUsingMask(GeneratedNode):
    def __init__(self, caseid, t1, t1mask):
        self.deps = [t1, t1mask]
        GeneratedNode.__init__(self, locals())

    def path(self):
        return OUTDIR / self.caseid / self.show() / 'mri/wmparc.mgz'

    def build(self):
        needDeps(self)
        from pnlscripts.util.scripts import fs_py
        fs_py['-i', self.t1.path(), '-m', self.t1mask.path(), '-f', '-o',
              self.path().dirname.dirname] & FG


class FsInDwiDirect(BrainsToolsNode):
    def __init__(self, caseid, fs, dwi, dwimask):
        self.deps = [fs, dwi, dwimask]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        fssubjdir = self.fs.path().dirname.dirname
        with TemporaryDirectory() as tmpdir, brainsToolsEnv():
            tmpdir = local.path(tmpdir)
            tmpoutdir = tmpdir / (self.caseid + '-fsindwi')
            fs2dwi_py('-f', fssubjdir, '-t', self.dwi.path(), '-m',
                      self.dwimask.path(), '-o', tmpoutdir, 'direct')


class Wmql(GeneratedNode):
    def __init__(self, caseid, fsindwi, ukf, tqhash):
        self.deps = [fsindwi, ukf]
        self.opts = [tqhash]
        GeneratedNode.__init__(self, locals())

    def path(self):
        return OUTDIR / self.caseid / self.show() / 'cc.vtk'

    def build(self):
        needDeps(self)
        if self.path().up().exists():
            self.path().up().delete()
        with tractQuerierEnv(self.tqhash):
            from pnlscripts.util.scripts import wmql_py
            wmql_py('-i', self.ukf.path(), '--fsindwi', self.fsindwi.path(),
                    '-o', self.path().dirname)


class TractMeasures(GeneratedNode):
    def __init__(self, caseid, wmql):
        self.deps = [wmql]
        self.ext = 'csv'
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        measureTracts_py = local.path(
            'pnlscripts/measuretracts/measuresTracts.py')
        vtks = self.wmql.path().up() // '*.vtk'
        measureTracts_py('-f', '-c', 'caseid', 'algo', '-v', self.caseid,
                         self.wmql.show(), '-o', self.path(), '-i', vtks)
