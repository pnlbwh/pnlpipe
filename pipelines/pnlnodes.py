#!/usr/bin/env python
from plumbum import local, FG, cli
from pnlscripts.util.scripts import alignAndCenter_py, convertdwi_py, atlas_py, fs2dwi_py, eddy_py
from pnlscripts.util import TemporaryDirectory
import sys
from pipelib import Src, GeneratedNode, need, needDeps, OUTDIR, log
from software import BRAINSTools, tract_querier, UKFTractography, trainingDataT1AHCC

defaultUkfParams = [("Ql", "70"), ("Qm", "0.001"), ("Rs", "0.015"),
                    ("numTensor", "2"), ("recordLength", "1.7"),
                    ("seedFALimit", "0.18"), ("seedsPerVoxel", "10"),
                    ("stepLength", "0.3")]

class DoesNotExistException(Exception):
    pass

def assertInputKeys(pipelineName, keys):
    import pipelib
    absentKeys = [k for k in keys if not pipelib.INPUT_PATHS.get(k)]
    if absentKeys:
        for key in absentKeys:
            print("{} requires '{}' set in inputPaths.yml".format(
                pipelineName, key))
        sys.exit(1)


def convertImage(i, o, bthash):
    if i.suffixes == o.suffixes:
        i.copy(o)
    with BRAINSTools.env(bthash):
        from plumbum.cmd import ConvertBetweenFileFormats
        ConvertBetweenFileFormats(i, o)


def formatParams(paramsList):
    formatted = [['--' + key, val] for key, val in paramsList]
    return [item for pair in formatted for item in pair]


def validateFreeSurfer(versionRequired):
    freesurferHome = os.environ.get('FREESURFER_HOME')
    if not freesurferHome:
        log.error("'FREESURFER_HOME' not set, set that first (need version {}) then run again".format(version))
        sys.exit(1)
    with open(local.path(freesurferHome) / "build-stamp.txt", 'r') as f:
        buildStamp = f.read()
    import re
    p = re.compile('v\d\.\d\.\d(-\w+)?$')
    try:
        version = p.search(buildStamp).group()
    except:
        log.error("Couldn't extract FreeSurfer version from {}/build-stamp.txt, either that file is malformed or the regex used to extract the version is incorrect.".format(freesurferHome))

        sys.exit(1)
    if version == versionRequired:
        log.info("Required FreeSurfer version {} is on path".format(version))
    else:
        log.error("FreeSurfer version {} at {} does not match the required version of {}, either change FREESURFER_HOME or change the version you require".format(version, freesurferHome, versionRequired))
        sys.exit(1)


class DwiEd(GeneratedNode):
    """ Eddy current correction. Accepts nrrd only. """

    def __init__(self, caseid, dwi, bthash):
        self.deps = [dwi]
        self.params = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with BRAINSTools.env(self.bthash):
            eddy_py['-i', self.dwi.path(), '-o', self.path(), '--force'] & FG


class DwiXc(GeneratedNode):
    """ Axis align and center a dWI. Accepts nrrd or nifti. """

    def __init__(self, caseid, dwi, bthash):
        self.deps = [dwi]
        self.params = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with BRAINSTools.env(self.bthash):
            convertdwi_py['-f', '-i', self.dwi.path(), '-o', self.path()] & FG
            alignAndCenter_py['-i', self.path(), '-o', self.path()] & FG


class DwiEpi(GeneratedNode):
    """Epi correction. """

    def __init__(self, caseid, dwi, dwimask, t2, t2mask, bthash):
        self.deps = [dwi, t2, t2mask]
        self.params = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with BRAINSTools.env(self.bthash):
            from pnlscripts.util.scripts import epi_py
            epi_py('--dwi', self.dwi.path(), '--dwimask', self.dwimask.path(),
                   '--t2', self.t2.path(), '--t2mask', self.t2mask.path(),
                   '-o', self.path())


class DwiMaskHcpBet(GeneratedNode):
    def __init__(self, caseid, dwi, bthash):
        self.deps = [dwi]
        self.params = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        from plumbum.cmd import bet
        with BRAINSTools.env(self.bthash), TemporaryDirectory() as tmpdir:
            tmpdir = local.path(tmpdir)
            nii = tmpdir / 'dwi.nii.gz'
            convertdwi_py('-i', self.dwi.path(), '-o', nii)
            bet(nii, tmpdir / 'dwi', '-m', '-f', '0.1')
            convertImage(tmpdir / 'dwi_mask.nii.gz', self.path(), self.bthash)


class UkfDefault(GeneratedNode):
    def __init__(self, caseid, dwi, dwimask, ukfhash, bthash):
        self.deps = [dwi, dwimask]
        self.params = [ukfhash, bthash]
        self.ext = 'vtk'
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with BRAINSTools.env(self.bthash), TemporaryDirectory() as tmpdir:
            tmpdir = local.path(tmpdir)
            tmpdwi = tmpdir / 'dwi.nrrd'
            tmpdwimask = tmpdir / 'dwimask.nrrd'
            convertdwi_py('-i', self.dwi.path(), '-o', tmpdwi)
            convertImage(self.dwimask.path(), tmpdwimask, self.bthash)
            params = ['--dwiFile', tmpdwi, '--maskFile', tmpdwimask,
                      '--seedsFile', tmpdwimask, '--recordTensors', '--tracts',
                      self.path()] + formatParams(defaultUkfParams)
            ukfpath = UKFTractography.getPath(self.ukfhash)
            log.info(' Found UKF at {}'.format(ukfpath))
            ukfbin = local[ukfpath]
            ukfbin(*params)


class StrctXc(GeneratedNode):
    def __init__(self, caseid, strct, bthash):
        self.deps = [strct]
        self.params = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with BRAINSTools.env(self.bthash):
            alignAndCenter_py['-i', self.strct.path(), '-o', self.path()] & FG


class T2wMaskRigid(GeneratedNode):
    def __init__(self, caseid, t2, t1, t1mask, bthash):
        self.deps = [t2, t1, t1mask]
        self.params = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with BRAINSTools.env(self.bthash):
            from pnlscripts.util.scripts import makeRigidMask_py
            makeRigidMask_py('-i', self.t1.path(), '--lablemap',
                             self.t1mask.path(), '--target', self.t2.path(),
                             '-o', self.path())


class T1wMaskMabs(GeneratedNode):
    def __init__(self, caseid, t1, trainingDataT1AHCC, bthash):
        self.deps = [t1]
        self.params = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with TemporaryDirectory() as tmpdir, BRAINSTools.env(self.bthash):
            tmpdir = local.path(tmpdir)
            # antsRegistration can't handle a non-conventionally named file, so
            # we need to pass in a conventionally named one
            tmpt1 = tmpdir / ('t1' + ''.join(self.t1.path().suffixes))
            from plumbum.cmd import ConvertBetweenFileFormats
            ConvertBetweenFileFormats[self.t1.path(), tmpt1] & FG
            trainingCsv = trainingDataT1AHCC.getPath(self.trainingDataT1AHCC) / 'trainingDataT1AHCC-hdr.csv'
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
        self.params = [bthash]
        self.ext = 'nii.gz'
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        fssubjdir = self.fs.path().dirname.dirname
        with TemporaryDirectory() as tmpdir, BRAINSTools.env(self.bthash):
            tmpoutdir = tmpdir / (self.caseid + '-fsindwi')
            tmpdwi = tmpdir / 'dwi.nrrd'
            tmpdwimask = tmpdir / 'dwimask.nrrd'
            convertdwi_py('-i', self.dwi.path(), '-o', tmpdwi)
            convertImage(self.dwimask.path(), tmpdwimask, self.bthash)
            fs2dwi_py['-f', fssubjdir, '-t', tmpdwi, '-m',
                      tmpdwimask, '-o', tmpoutdir, 'direct'] & FG
	    local.path(tmpoutdir / 'wmparcInDwi1mm.nii.gz').copy(self.path())


class Wmql(GeneratedNode):
    def __init__(self, caseid, fsindwi, ukf, tqhash):
        self.deps = [fsindwi, ukf]
        self.params = [tqhash]
        GeneratedNode.__init__(self, locals())

    def path(self):
        return OUTDIR / self.caseid / self.showShortened() / 'cc.vtk'

    def build(self):
        needDeps(self)
        if self.path().up().exists():
            self.path().up().delete()
        with tract_querier.env(self.tqhash):
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
        measureTracts_py = local['pipelines/pnlscripts/measuretracts/measureTracts.py']
        vtks = self.wmql.path().up() // '*.vtk'
        measureTracts_py['-f', '-c', 'caseid', 'algo', '-v', self.caseid,
                         self.wmql.showShortened(), '-o', self.path(), '-i', vtks] & FG
