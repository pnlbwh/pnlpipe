import sys
import os
from pnlpipe_lib import node, Node, reduce_hash, filehash, dirhash, LOG, find_tag
import pnlpipe_lib.dag as dag
from pnlpipe_software import BRAINSTools
import pnlpipe_software as soft
from plumbum import local, FG
from pnlscripts import dwiconvert_py, alignAndCenter_py, atlas_py, eddy_py, bet_py, wmql_py, epi_py, makeRigidMask_py, fs_py, fs2dwi_py
import pnlpipe_cli
import pnlpipe_cli.caseidnode as caseidnode
import itertools
import logging
from python_log_indenter import IndentedLoggerAdapter
import pandas as pd
logger = logging.getLogger(__name__)
log = IndentedLoggerAdapter(logger, indent_char='.')

# defaults that pipelines can use
bet_threshold = 0.1
BRAINSTools_hash = '81a409d'
trainingDataT1AHCC_hash = 'd6e5990'
FreeSurfer_version = '5.3.0'
UKFTractography_hash = 'ce12942'
tract_querier_hash = 'cff29a3'
ukfparams = ["--Ql", 70, "--Qm", 0.001, "--Rs", 0.015, "--numTensor", 2,
             "--recordLength", 1.7, "--seedFALimit", 0.18, "--seedsPerVoxel",
             10, "--stepLength", 0.3]



@node(params=['key', 'caseid'])
class InputPathFromKey(caseidnode.InputPathFromKey):
    def stamp(self):
        def get_associated_files(filepath):
            result = []
            if '.nii' in filepath.suffixes:
                bval = filepath.with_suffix('.bval', depth=2)
                bvec = filepath.with_suffix('.bvec', depth=2)
                result.extend([f for f in [bval, bvec] if f.exists()])
            if '.nhdr' in filepath.suffixes:
                rawgz = filepath.with_suffix('.raw.gz')
                raw = filepath.with_suffix('.raw')
                if raw.exists():
                    raise Exception(
                        "'{}' has an unzipped raw file, zip the nhdr first(e.g. unu save -e gzip -f nrrd -i nhdr -o nhdr) ")
                if rawgz.exists():
                    result.append(rawgz)
            return result

        if self.output().is_dir():
            return dirhash(self.output())

        allfiles = get_associated_files(self.output()) + [self.output()]
        if len(allfiles) > 1:
            return reduce_hash([filehash(f) for f in allfiles], 'md5')
        return filehash(self.output())


class NrrdOutput(caseidnode.AutoOutput):
    @property
    def ext(self):
        return '.nrrd'


class NiftiOutput(caseidnode.AutoOutput):
    @property
    def ext(self):
        return '.nii.gz'


class DirOutput(caseidnode.AutoOutput):
    @property
    def ext(self):
        return ''


class CsvOutput(caseidnode.AutoOutput):
    @property
    def ext(self):
        return '.csv'


class VtkOutput(caseidnode.AutoOutput):
    @property
    def ext(self):
        return '.vtk'


def convertImage(i, o, bthash):
    if i.suffixes == o.suffixes:
        i.copy(o)
    with BRAINSTools.env(bthash):
        from plumbum.cmd import ConvertBetweenFileFormats
        ConvertBetweenFileFormats(i, o)


@node(params=['BRAINSTools_hash'], deps=['dwi'])
class DwiXc(NrrdOutput):
    """ Axis align and center a DWI. Accepts nrrd or nifti. """

    def static_build(self):
        with BRAINSTools.env(self.BRAINSTools_hash), local.tempdir() as tmpdir:
            inputnrrd = tmpdir / 'inputdwi.nrrd'
            dwiconvert_py['-f', '-i', self.dwi, '-o', inputnrrd] & LOG
            alignAndCenter_py['-i', inputnrrd, '-o', self.output()] & LOG


@node(params=['BRAINSTools_hash'], deps=['dwi'])
class DwiEd(NrrdOutput):
    """ Eddy current correction. Accepts nrrd only. """

    def static_build(self):
        with BRAINSTools.env(self.BRAINSTools_hash):
            eddy_py['-i', self.dwi, '-o', self.output(), '--force'] & LOG


@node(params=['bet_threshold', 'BRAINSTools_hash'], deps=['dwi'])
class DwiMaskBet(NrrdOutput):
    def static_build(self):
        with BRAINSTools.env(self.BRAINSTools_hash), \
             local.tempdir() as tmpdir:
            bet_py('--force', '-f', self.bet_threshold, '-i', self.dwi, '-o',
                   self.output())


@node(params=['BRAINSTools_hash'], deps=['dwi', 'dwimask', 't2', 't2mask'])
class DwiEpi(NrrdOutput):
    """DWI EPI correction."""

    def static_build(self):
        with BRAINSTools.env(self.BRAINSTools_hash):
            epi_py('--force', '--typeCast',
                   '--dwi', self.dwi,
                   '--dwimask', self.dwimask,
                   '--t2', self.t2,
                   '--t2mask', self.t2mask,
                   '-o', self.output())


@node(params=['BRAINSTools_hash'], deps=['dwi'])
class DwiEpiMask(NrrdOutput):
    """Generates a mask from an EPI corrected DWI, which is already skullstripped."""

    def static_build(self):
        from plumbum.cmd import unu
        with BRAINSTools.env(self.BRAINSTools_hash):
            slicecmd = unu["slice", "-a", "3", "-p", 0, "-i", self.dwi]
            binarizecmd = unu["3op", "ifelse", "-", 1, 0]
            gzipcmd = unu["save", "-e", "gzip", "-f", "nrrd", "-o", self.output()]
            (slicecmd | binarizecmd | gzipcmd) & FG


#@node(params=['echo_spacing', 'pe_dir'],
#      deps=['pos_dwis', 'neg_dwis'])
class DwiHcp(NiftiOutput):
    """ Washington University HCP DWI preprocessing. """

    def __init__(self, HCPPipelines_version, echo_spacing, pe_dir, pos_dwis, neg_dwis):
        self._params = dict(zip(['echo_spacing', 'pe_dir'], [echo_spacing, pe_dir]))
        self.echo_spacing = echo_spacing
        self.pe_dir = pe_dir
        self.HCPPipelines_version = HCPPipelines_version

        for dwi in pos_dwis + neg_dwis:
            if not isinstance(dwi, Node):
                raise Exception("DwiHcp expects its dependencies to be of type basenode.Node, instead found type '{}'".format(type(dwi)))
        pos_keys = ['{}{}'.format(s,n) for (s,n) in list(itertools.izip_longest([], range(10), fillvalue='posdwi'))]
        neg_keys = ['{}{}'.format(s,n) for (s,n) in list(itertools.izip_longest([], range(10), fillvalue='negdwi'))]
        self._deps = dict(zip(pos_keys + neg_keys, pos_dwis + neg_dwis))
        self.pos_dwis = [d.output() for d in pos_dwis]
        self.neg_dwis = [d.output() for d in neg_dwis]

    @property
    def params(self):
        return self._params

    @property
    def deps(self):
        return self._deps


    def static_build(self):
        #with soft.HCPPipelines.env(self.HCPPipelines_version), local.tempdir() as tmpdir:
        with soft.HCPPipelines.env(self.HCPPipelines_version):
            tmpdir = local.path('hcp_tmp')
            tmpdir.mkdir()
            preproc = local[soft.HCPPipelines.get_path(self.HCPPipelines_version) /
                            'DiffusionPreprocessing/DiffPreprocPipeline.sh']
            caseid = pnlpipe_cli.find_caseid(self)
            dwiname = 'hcp-{}'.format(os.getpid())
            hcpdir = tmpdir / caseid / dwiname
            hcpdatadir = hcpdir / 'data'
            try:
                preproc['--path={}'.format(tmpdir), '--subject={}'.format(caseid), '--PEdir={}'.format(self.pe_dir), '--posData='
                        + '@'.join(self.pos_dwis), '--negData=' + '@'.join(
                            self.neg_dwis), '--echospacing={}'.format(
                                self.echo_spacing), '--gdcoeffs=NONE',
                        '--dwiname={}'.format(dwiname)] & FG
            except Exception as e:
                if not (hcpdatadir / 'data.nii.gz').exists():
                    print(e)
                    log.error("HCP failed to make '{}'".format(hcpdatadir /
                                                               'data.nii.gz'))
                    sys.exit(1)
            (hcpdatadir / 'data.nii.gz').move(self.output())
            (hcpdatadir / 'bvals').move(self.output().with_suffix(
                '.bval', depth=2))
            (hcpdatadir / 'bvecs').move(self.output().with_suffix(
                '.bvec', depth=2))
            tarfile = self.output()[:-7] + '-hcpfiles.tar.gz'
            from plumbum.cmd import tar
            with local.cwd(hcpdir):
                tar['czf', tarfile, '.'] & FG


@node(params=['BRAINSTools_hash'], deps=['strct'])
class StrctXc(NrrdOutput):
    """Axis aligns and centers structural (nifti or nrrd)"""

    def static_build(self):
        with BRAINSTools.env(self.BRAINSTools_hash), \
             local.tempdir() as tmpdir:
            nrrd = tmpdir / 'strct.nrrd'
            convertImage(self.strct, nrrd, self.BRAINSTools_hash)
            alignAndCenter_py['-i', nrrd, '-o', self.output()] & FG


@node(params=['BRAINSTools_hash'], deps=['strct'])
class T1Xc(StrctXc):
    pass


@node(params=['BRAINSTools_hash'], deps=['strct'])
class T2Xc(StrctXc):
    pass


@node(params=['BRAINSTools_hash', 'trainingDataT1AHCC_hash'], deps=['t1'])
class T1wMaskMabs(NrrdOutput):
    """Generates a T1w mask using multi-atlas brain segmentation."""

    def static_build(self):
        with local.tempdir() as tmpdir, BRAINSTools.env(
                self.BRAINSTools_hash):
            tmpdir = local.path(tmpdir)
            # antsRegistration can't handle a non-conventionally named file, so
            # we need to pass in a conventionally named one
            # TODO needed any more?
            tmpt1 = tmpdir / ('t1' + ''.join(self.t1.suffixes))
            from plumbum.cmd import ConvertBetweenFileFormats
            ConvertBetweenFileFormats[self.t1, tmpt1] & FG
            trainingCsv = soft.trainingDataT1AHCC.get_path(
                self.trainingDataT1AHCC_hash) / 'trainingDataT1AHCC-hdr.csv'
            atlas_py['csv', '--fusion', 'avg', '-t', tmpt1, '-o', tmpdir,
                     trainingCsv] & FG
            (tmpdir / 'mask.nrrd').copy(self.output())


@node(params=['BRAINSTools_hash'], deps=['moving', 'moving_mask', 'fixed'])
class MaskRigid(NrrdOutput):
    """Rigidly transforms a mask from one structural scan to another."""

    def static_build(self):
        with BRAINSTools.env(self.BRAINSTools_hash), local.tempdir() as tmpdir:
            moving = tmpdir / 'moving.nrrd'
            movingmask = tmpdir / 'movingmask.nrrd'
            fixed = tmpdir / 'fixed.nrrd'
            out = tmpdir / 'fixedmask.nrrd'
            convertImage(self.moving, moving, self.BRAINSTools_hash)
            convertImage(self.moving_mask, movingmask, self.BRAINSTools_hash)
            convertImage(self.fixed, fixed, self.BRAINSTools_hash)
            makeRigidMask_py('-i', moving, '--labelmap', movingmask,
                             '--target', fixed, '-o', out)
            out.move(self.output())


@node(params=['FreeSurfer_version','BRAINSTools_hash'], deps=['t1', 't1mask'])
class FreeSurferUsingMask(DirOutput):
    """Runs FreeSurfer after masking the T1w with the given mask."""

    def stamp(self):
        return dirhash(self.output(), included_extensions=['.mgz'])

    def static_build(self):
        soft.FreeSurfer.validate(self.FreeSurfer_version)
        with BRAINSTools.env(self.BRAINSTools_hash):
            fs_py['-i', self.t1, '-m', self.t1mask, '-f', '-o', self.output()] & FG


@node(params=['BRAINSTools_hash'], deps=['fs', 'dwi', 'dwimask'])
class FsInDwiDirect(NiftiOutput):
    """Direct registration from FreeSurfer wmparc to DWI."""

    def static_build(self):
        fssubjdir = self.fs
        with local.tempdir() as tmpdir, BRAINSTools.env(
                self.BRAINSTools_hash):
            tmpoutdir = tmpdir / 'fsindwi'
            tmpdwi = tmpdir / 'dwi.nrrd'
            tmpdwimask = tmpdir / 'dwimask.nrrd'
            dwiconvert_py('-i', self.dwi, '-o', tmpdwi)
            convertImage(self.dwimask, tmpdwimask, self.BRAINSTools_hash)
            fs2dwi_py['-f', fssubjdir, '-t', tmpdwi, '-m', tmpdwimask, '-o',
                      tmpoutdir, 'direct'] & FG
            local.path(tmpoutdir / 'wmparcInDwi1mm.nii.gz').copy(self.output())


@node(
    params=['BRAINSTools_hash'],
    deps=['fs', 'dwi', 'dwimask', 't1', 't1mask', 't2', 't2mask'])
class FsInDwiUsingT2(NiftiOutput):
    """Registration from FreeSurfer wmparc to DWI using intermediate
    t1 and t2 registrations."""

    def static_build(self):
        fssubjdir = self.fs
        with local.tempdir() as tmpdir, BRAINSTools.env(
                self.BRAINSTools_hash):
            tmpoutdir = tmpdir / 'fsindwi'
            dwi = tmpdir / 'dwi.nrrd'
            dwimask = tmpdir / 'dwimask.nrrd'
            fs = tmpdir / 'fs'
            t2 = tmpdir / 't2.nrrd'
            t1 = tmpdir / 't1.nrrd'
            t1mask = tmpdir / 't1mask.nrrd'
            t2mask = tmpdir / 't2mask.nrrd'
            fssubjdir.copy(fs)
            dwiconvert_py('-i', self.dwi, '-o', dwi)
            convertImage(self.dwimask, dwimask, self.BRAINSTools_hash)
            convertImage(self.t2, t2, self.BRAINSTools_hash)
            convertImage(self.t1, t1, self.BRAINSTools_hash)
            convertImage(self.t2mask, t2mask, self.BRAINSTools_hash)
            convertImage(self.t1mask, t1mask, self.BRAINSTools_hash)
            script = local['pnlscripts/old/fs2dwi_T2.sh']
            script['--fsdir', fs, '--dwi', dwi, '--dwimask', dwimask, '--t2',
                   t2, '--t2mask', t2mask, '--t1', t1, '--t1mask', t1mask,
                   '-o', tmpoutdir] & FG
            convertImage(tmpoutdir / 'wmparc-in-bse.nrrd', self.output(),
                         self.BRAINSTools_hash)


@node(
    params=['ukfparams', 'UKFTractography_hash', 'BRAINSTools_hash'],
    deps=['dwi', 'dwimask'])
class Ukf(VtkOutput):
    """UKF Tractography"""

    def static_build(self):
        with BRAINSTools.env(self.BRAINSTools_hash), local.tempdir() as tmpdir:
            tmpdir = local.path(tmpdir)
            tmpdwi = tmpdir / 'dwi.nrrd'
            tmpdwimask = tmpdir / 'dwimask.nrrd'
            dwiconvert_py('-i', self.dwi, '-o', tmpdwi)
            convertImage(self.dwimask, tmpdwimask, self.BRAINSTools_hash)
            params = ['--dwiFile', tmpdwi, '--maskFile', tmpdwimask,
                      '--seedsFile', tmpdwimask, '--recordTensors', '--tracts',
                      self.output()] + list(self.ukfparams)
            ukfpath = soft.UKFTractography.get_path(self.UKFTractography_hash)
            log.info(' Found UKF at {}'.format(ukfpath))
            ukfbin = local[ukfpath]
            # ukfbin(*params)
            ukfbin.bound_command(*params) & FG


@node(params=['tract_querier_hash','BRAINSTools_hash'], deps=['fsindwi', 'ukf'])
class Wmql(DirOutput):
    """White matter query language"""

    def stamp(self):
        return dirhash(self.output(), included_extensions=['.vtk'])

    def static_build(self):
        self.output().delete()
        with soft.tract_querier.env(self.tract_querier_hash), BRAINSTools.env(self.BRAINSTools_hash):
            wmql_py['-i', self.ukf, '--fsindwi', self.fsindwi, '-o',
                    self.output()] & FG


@node(params=['caseid'], deps=['wmql'])
class TractMeasures(CsvOutput):
    """Computes the diffusion measures of white matter tracts."""

    def static_build(self):
        measureTracts_py = local[
            'pnlscripts/measuretracts/measureTracts.py']
        vtks = self.wmql // '*.vtk'
        measureTracts_py['-f', '-c', 'caseid', 'algo', '-v', self.caseid,
                         dag.showCompressedDAG(self.deps['wmql']), '-o', self.output(), '-i', vtks] & FG

def summarize_tractmeasures(pipename, extra_flags=None):
    from pnlpipe_lib import OUTDIR
    from pnlpipe_cli import read_grouped_combos, make_pipeline
    log.info("Combine all csvs into one")
    dfs = []
    for paramid, combo, caseids in read_grouped_combos(pipename):
        pipelines = [make_pipeline(pipename, combo, caseid) for caseid in caseids]
        csvs = ([pipeline['tractmeasures'].output().__str__() for pipeline in pipelines if \
                     pipeline['tractmeasures'].output().exists()])
        if csvs:
            df = pd.concat(filter(lambda x: x is not None, (pd.read_csv(csv) for csv in csvs)))
            df['pipelineId'] = paramid
            dfs.append(df)
    if dfs:
        from pnlscripts.summarizeTractMeasures import summarize
        df = pd.concat(dfs)
        df_summary = summarize(df)
        #if 'csv' in extraFlags:
        outcsv = OUTDIR / (pipename + '-tractmeasures.csv')
        df.to_csv(outcsv.__str__(), header=True, index=False)
        log.info("Made '{}'".format(outcsv))
        outcsv_summary = OUTDIR / (pipename + '-tractmeasures-summary.csv')
        #df_summary.to_csv(outcsv_summary.__str__(), header=True, index=False)
        df_summary.to_csv(outcsv_summary.__str__(), header=True)
        log.info("Made '{}'".format(outcsv_summary))
    else:
        log.info("No csvs found yet.")
