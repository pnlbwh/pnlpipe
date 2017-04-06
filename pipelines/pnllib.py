#!/usr/bin/env python
from plumbum import local, FG, cli, ProcessExecutionError
from pnlscripts.util.scripts import dwiconvert_py, atlas_py, fs2dwi_py, eddy_py, alignAndCenter_py, bet_py
from pnlscripts.util import TemporaryDirectory
import sys
from pipelib import Src, GeneratedNode, need, needDeps, OUTDIR, log
from software import BRAINSTools, tract_querier, UKFTractography, trainingDataT1AHCC, HCPPipelines
import software.FreeSurfer

defaultUkfParams = ["--Ql", 70, "--Qm", 0.001, "--Rs", 0.015,
                    "--numTensor", 2, "--recordLength", 1.7,
                    "--seedFALimit", 0.18, "--seedsPerVoxel", 10,
                    "--stepLength", 0.3]

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

def tractMeasureStatus(combos, makePipelineFn):
    import pandas as pd
    dfs = []
    for combo in combos:
        pipelines = [makePipelineFn(**paramPoint) for paramPoint in combo['paramPoints']]
        csvs = [p['tractmeasures'].path() for p in pipelines
            if p['tractmeasures'].path().exists()]
        if csvs:
            df = pd.concat((pd.read_csv(csv) for csv in csvs))
            df['algo'] = combo['id']
            dfs.append(df)
    if dfs:
        from pipelines.pnlscripts.summarizeTractMeasures import summarize
        summarize(pd.concat(dfs))


def convertImage(i, o, bthash):
    if i.suffixes == o.suffixes:
        i.copy(o)
    with BRAINSTools.env(bthash):
        from plumbum.cmd import ConvertBetweenFileFormats
        ConvertBetweenFileFormats(i, o)


def formatParams(l):
    formatted = [['--' + key, val] for key, val in dic.items()]
    return [item for pair in formatted for item in pair if item]


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


class DwiHcp(GeneratedNode):
    """ Washington University HCP DWI preprocessing. """

    def __init__(self, caseid, posDwis, negDwis, echoSpacing, peDir, version_HCPPipelines):
        self.deps = posDwis + negDwis
        self.params = [version_HCPPipelines]
        self.ext = '.nii.gz'
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with HCPPipelines.env(self.version_HCPPipelines), TemporaryDirectory() as tmpdir:
            preproc = local[HCPPipelines.getPath(self.version_HCPPipelines) /
                             'DiffusionPreprocessing/DiffPreprocPipeline.sh']
            posPaths = [n.path() for n in self.posDwis]
            negPaths = [n.path() for n in self.negDwis]
            datadir = tmpdir / 'hcp/data'
            from os import getpid
            hcpdir = OUTDIR / self.caseid / 'hcp-{}'.format(getpid())
            datadir = hcpdir / 'data'
            try:
                preproc['--path={}'.format(OUTDIR)
                        ,'--subject={}'.format(self.caseid)
                        ,'--PEdir={}'.format(self.peDir)
                        ,'--posData='+'@'.join(posPaths)
                        ,'--negData='+'@'.join(negPaths)
                        ,'--echospacing={}'.format(self.echoSpacing)
                        ,'--gdcoeffs=NONE'
                        ,'--dwiname=hcp-{}'.format(getpid())] & FG
            except ProcessExecutionError as e:
                if not (datadir/'data.nii.gz').exists():
                    print(e)
                    log.error("HCP failed to make '{}'".format(datadir/'data.nii.gz'))
                    (OUTDIR / self.caseid / 'T1w').delete()
                    sys.exit(1)
            (OUTDIR / self.caseid / 'T1w').delete()
            (datadir / 'data.nii.gz').move(self.path())
            (datadir / 'bvals').move(self.path().with_suffix('.bval', depth=2))
            (datadir / 'bvecs').move(self.path().with_suffix('.bvec', depth=2))


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
    """ Axis align and center a DWI. Accepts nrrd or nifti. """

    def __init__(self, caseid, dwi, bthash):
        self.deps = [dwi]
        self.params = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with BRAINSTools.env(self.bthash), TemporaryDirectory() as tmpdir:
            tmpdwi = tmpdir / (self.caseid + '-dwi.nrrd')
            dwiconvert_py['-f', '-i', self.dwi.path(), '-o', tmpdwi] & FG
            alignAndCenter_py['-i', tmpdwi, '-o', self.path()] & FG


class DwiEpi(GeneratedNode):
    """Epi correction. """

    def __init__(self, caseid, dwi, dwimask, t2, t2mask, bthash):
        self.deps = [dwi, dwimask, t2, t2mask]
        self.params = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with BRAINSTools.env(self.bthash):
            from pnlscripts.util.scripts import epi_py
            epi_py('--force', '--dwi', self.dwi.path(), '--dwimask', self.dwimask.path(),
                   '--t2', self.t2.path(), '--t2mask', self.t2mask.path(),
                   '-o', self.path())


class DwiMaskBet(GeneratedNode):
    def __init__(self, caseid, dwi, threshold, bthash):
        self.deps = [dwi]
        self.params = [threshold, bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with BRAINSTools.env(self.bthash), TemporaryDirectory() as tmpdir:
            bet_py('--force', '-f', self.threshold, '-i', self.dwi.path(), '-o', self.path())


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
            dwiconvert_py('-i', self.dwi.path(), '-o', tmpdwi)
            convertImage(self.dwimask.path(), tmpdwimask, self.bthash)
            params = ['--dwiFile', tmpdwi, '--maskFile', tmpdwimask,
                      '--seedsFile', tmpdwimask, '--recordTensors', '--tracts',
                      self.path()] + defaultUkfParams
            ukfpath = UKFTractography.getPath(self.ukfhash)
            log.info(' Found UKF at {}'.format(ukfpath))
            ukfbin = local[ukfpath]
            ukfbin(*params)

class Ukf(GeneratedNode):
    def __init__(self, caseid, dwi, dwimask, ukfparams, ukfhash, bthash):
        self.deps = [dwi, dwimask]
        self.params = [ukfhash, bthash, ukfparams]
        self.ext = '.vtk'
        GeneratedNode.__init__(self, locals())
    def build(self):
        needDeps(self)
        with BRAINSTools.env(self.bthash), TemporaryDirectory() as tmpdir:
            tmpdir = local.path(tmpdir)
            tmpdwi = tmpdir / 'dwi.nrrd'
            tmpdwimask = tmpdir / 'dwimask.nrrd'
            dwiconvert_py('-i', self.dwi.path(), '-o', tmpdwi)
            convertImage(self.dwimask.path(), tmpdwimask, self.bthash)
            params = ['--dwiFile', tmpdwi, '--maskFile', tmpdwimask,
                      '--seedsFile', tmpdwimask, '--recordTensors', '--tracts',
                      self.path()] + self.ukfparams
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
        with BRAINSTools.env(self.bthash), TemporaryDirectory() as tmpdir:
            nrrd = tmpdir / 'strct.nrrd'
            convertImage(self.strct.path(), nrrd, self.bthash)
            alignAndCenter_py['-i', nrrd, '-o', self.path()] & FG


class MaskRigid(GeneratedNode):
    def __init__(self, caseid, fixedStrct, movingStrct, movingStrctMask, bthash):
        self.deps = [fixedStrct, movingStrct, movingStrctMask]
        self.params = [bthash]
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with BRAINSTools.env(self.bthash), TemporaryDirectory() as tmpdir:
            from pnlscripts.util.scripts import makeRigidMask_py
            moving = tmpdir / 'moving.nrrd'
            movingmask = tmpdir / 'movingmask.nrrd'
            fixed = tmpdir / 'fixed.nrrd'
            out = tmpdir / 'fixedmask.nrrd'
            convertImage(self.movingStrct.path(), moving, self.bthash)
            convertImage(self.movingStrctMask.path(), movingmask, self.bthash)
            convertImage(self.fixedStrct.path(), fixed, self.bthash)
            makeRigidMask_py('-i', t1, '--labelmap',
                             movingmask, '--target', fixed,
                             '-o', out)
            out.move(self.path())


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
    def __init__(self, caseid, t1, t1mask, version_FreeSurfer):
        self.deps = [t1, t1mask]
        self.params = [version_FreeSurfer]
        GeneratedNode.__init__(self, locals())

    def path(self):
        return OUTDIR / self.caseid / self.show() / 'mri/wmparc.mgz'

    def build(self):
        needDeps(self)
        # make sure FREESURFER_HOME is set to right version
        software.FreeSurfer.validate(self.version_FreeSurfer)
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
            dwiconvert_py('-i', self.dwi.path(), '-o', tmpdwi)
            convertImage(self.dwimask.path(), tmpdwimask, self.bthash)
            fs2dwi_py['-f', fssubjdir, '-t', tmpdwi, '-m',
                      tmpdwimask, '-o', tmpoutdir, 'direct'] & FG
	    local.path(tmpoutdir / 'wmparcInDwi1mm.nii.gz').copy(self.path())

class FsInDwiUsingT2(GeneratedNode):
    def __init__(self, caseid, fs, t1, t1mask, t2, t2mask, dwi, dwimask, bthash):
        self.deps = [fs, t1, t2, dwi, dwimask]
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
            dwiconvert_py('-i', self.dwi.path(), '-o', tmpdwi)
            convertImage(self.dwimask.path(), tmpdwimask, self.bthash)
            t2 = self.t2.path()
            t1 = self.t1.path()
            t1mask = self.t1mask.path()
            t2mask = self.t2mask.path()
            cmd = 'pipelines/pnlscripts/old/fs2dwi_T2.sh --fsdir {fssubjdir} \
            --dwi {tmpdwi} \
            --dwimask {tmpdwimask} \
            --t2 {t2} \
            --t2mask {t2mask} \
            --t1 {t1} \
            --t1mask {t1mask} \
            -o {tmpoutdir}'.format(locals())
            import os
            os.system(cmd)
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
            wmql_py['-i', self.ukf.path(), '--fsindwi', self.fsindwi.path(),
                    '-o', self.path().dirname] & FG

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
