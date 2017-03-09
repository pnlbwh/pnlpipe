#!/usr/bin/env python
from plumbum import local, FG, cli
from pnlscripts.util.scripts import alignAndCenter_py, convertdwi_py, atlas_py, fs2dwi_py, eddy_py
from pnlscripts.util import TemporaryDirectory
import sys
from pipelib import Src, GeneratedNode, need, needDeps, OUTDIR, log
from software import getSoftDir
import software.BRAINSTools
import software.tract_querier
import software.UKFTractography
import software.trainingDataT1AHCC

defaultUkfParams = [("Ql", "70"), ("Qm", "0.001"), ("Rs", "0.015"),
                    ("numTensor", "2"), ("recordLength", "1.7"),
                    ("seedFALimit", "0.18"), ("seedsPerVoxel", "10"),
                    ("stepLength", "0.3")]


def assertInputKeys(pipelineName, keys):
    import pipelib
    absentKeys = [k for k in keys if not pipelib.INPUT_PATHS.get(k)]
    if absentKeys:
        for key in absentKeys:
            print("{} requires '{}' set in _inputPaths.yml".format(
                pipelineName, key))
        sys.exit(1)


class DoesNotExistException(Exception):
    pass


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


def brainsToolsEnv(bthash):
    btpath = software.BRAINSTools.getPath(bthash)
    newpath = ':'.join(str(p) for p in [btpath] + local.env.path)
    return local.env(PATH=newpath, ANTSPATH=btpath)


def convertImage(i, o):
    if i.suffixes == o.suffixes:
        i.copy(o)
    with brainsToolsEnv():
        from plumbum.cmd import ConvertBetweenFileFormats
        ConvertBetweenFileFormats(i, o)


def tractQuerierEnv(hash):
    path = software.tract_querier.getPath(hash)
    newPath = ':'.join(str(p) for p in [path] + local.env.path)
    import os
    pythonPath = os.environ.get('PYTHONPATH')
    newPythonPath = path if not pythonPath else '{}:{}'.format(path,
                                                               pythonPath)
    return local.env(PATH=newPath, PYTHONPATH=newPythonPath)


def add(d, key, val):
    if not key in d.keys():
        d[key] = val
        return
    for i in range(5):
        newkey = key + str(i)
        if newKey in d.keys():
            d[newKey] = val
            return
    raise Exception('Too many matches')


# class PNLNode(GeneratedNode):
#     def path(self):
#         ext = getattr(self, 'ext', '.nrrd')
#         if not ext.startswith('.'):
#             ext = '.' + ext
#         outdir = OUTDIR / self.caseid
#         return outdir / (self.showShortened() + '-' + BTHASH + '-' + self.caseid + ext)


class DwiEd(GeneratedNode):
    """ Eddy current correction. Accepts nrrd only. """

    def __init__(self, caseid, dwi, bthash):
        self.deps = [dwi]
        self.opts = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with brainsToolsEnv(self.bthash):
            eddy_py['-i', self.dwi.path(), '-o', self.path()] & FG


class DwiXc(GeneratedNode):
    """ Axis align and center a dWI. Accepts nrrd or nifti. """

    def __init__(self, caseid, dwi, bthash):
        self.deps = [dwi]
        self.opts = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with brainsToolsEnv(self.bthash):
            convertdwi_py['-f', '-i', self.dwi.path(), '-o', self.path()] & FG
            alignAndCenter_py['-i', self.path(), '-o', self.path()] & FG


class DwiEpi(GeneratedNode):
    """Epi correction. """

    def __init__(self, caseid, dwi, dwimask, t2, t2mask, bthash):
        self.deps = [dwi, t2, t2mask]
        self.opts = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with brainsToolsEnv(self.bthash):
            from pnlscripts.util.scripts import epi_py
            epi_py('--dwi', self.dwi.path(), '--dwimask', self.dwimask.path(),
                   '--t2', self.t2.path(), '--t2mask', self.t2mask.path(),
                   '-o', self.path())


class DwiMaskHcpBet(GeneratedNode):
    def __init__(self, caseid, dwi, bthash):
        self.deps = [dwi]
        self.opts = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        from plumbum.cmd import bet
        with brainsToolsEnv(self.bthash), TemporaryDirectory() as tmpdir:
            tmpdir = local.path(tmpdir)
            nii = tmpdir / 'dwi.nii.gz'
            convertdwi_py('-i', self.dwi.path(), '-o', nii)
            bet(nii, tmpdir / 'dwi', '-m', '-f', '0.1')
            convertImage(tmpdir / 'dwi_mask.nii.gz', self.path(), self.bthash)


class UkfDefault(GeneratedNode):
    def __init__(self, caseid, dwi, dwimask, ukfhash, bthash):
        self.deps = [dwi, dwimask]
        self.opts = [ukfhash, bthash]
        self.ext = 'vtk'
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with brainsToolsEnv(bthash), TemporaryDirectory() as tmpdir:
            tmpdir = local.path(tmpdir)
            tmpdwi = tmpdir / 'dwi.nrrd'
            tmpdwimask = tmpdir / 'dwimask.nrrd'
            convertdwi_py('-i', self.dwi.path(), '-o', tmpdwi)
            convertImage(self.dwimask.path(), tmpdwimask, self.bthash)
            params = ['--dwiFile', tmpdwi, '--maskFile', tmpdwimask,
                      '--seedsFile', tmpdwimask, '--recordTensors', '--tracts',
                      self.path()] + formatParams(defaultUkfParams)
            ukfpath = software.UKFTractography.getPath(self.ukfhash)
            log.info(' Found UKF at {}'.format(ukfpath))
            ukfbin = local[ukfpath]
            ukfbin(*params)


class StrctXc(GeneratedNode):
    def __init__(self, caseid, strct, bthash):
        self.deps = [strct]
        self.opts = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with brainsToolsEnv(self.bthash):
            alignAndCenter_py['-i', self.strct.path(), '-o', self.path()] & FG


class T2wMaskRigid(GeneratedNode):
    def __init__(self, caseid, t2, t1, t1mask, bthash):
        self.deps = [t2, t1, t1mask]
        self.opts = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with brainsToolsEnv(self.bthash):
            from pnlscripts.util.scripts import makeRigidMask_py
            makeRigidMask_py('-i', self.t1.path(), '--lablemap',
                             self.t1mask.path(), '--target', self.t2.path(),
                             '-o', self.path())


class T1wMaskMabs(GeneratedNode):
    def __init__(self, caseid, t1, trainingDataT1AHCC, bthash):
        self.deps = [t1]
        self.opts = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with TemporaryDirectory() as tmpdir, brainsToolsEnv(self.bthash):
            tmpdir = local.path(tmpdir)
            # antsRegistration can't handle a non-conventionally named file, so
            # we need to pass in a conventionally named one
            tmpt1 = tmpdir / ('t1' + ''.join(self.t1.path().suffixes))
            from plumbum.cmd import ConvertBetweenFileFormats
            ConvertBetweenFileFormats[self.t1.path(), tmpt1] & FG
            trainingCsv = software.trainingDataT1AHCC.getPath(self.trainingDataT1AHCC) / 'trainingDataT1AHCC-hdr.csv'
            atlas_py['--mabs', '-t', tmpt1, '-o', tmpdir, 'csv',
                     trainingCsv ] & FG
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


class FsInDwiDirect(GeneratedNode):
    def __init__(self, caseid, fs, dwi, dwimask, bthash):
        self.deps = [fs, dwi, dwimask]
        self.opts = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        fssubjdir = self.fs.path().dirname.dirname
        with TemporaryDirectory() as tmpdir, brainsToolsEnv(self.bthash):
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
        return OUTDIR / self.caseid / self.showShortened() / 'cc.vtk'

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
