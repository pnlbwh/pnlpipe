from pnlpipe_lib import *
import pnlpipe_lib.dag as dag
from pnlpipe_software import BRAINSTools, trainingDataT1AHCC, FreeSurfer
import hashlib
from plumbum import local, FG
from pnlscripts import TemporaryDirectory, dwiconvert_py, alignAndCenter_py, atlas_py, eddy_py, bet_py, wmql_py
import logging
from python_log_indenter import IndentedLoggerAdapter
logger = logging.getLogger(__name__)
log = IndentedLoggerAdapter(logger, indent_char='.')

# defaults that pipelines can use
bet_threshold = 0.1
BRAINSTools_hash = '2d5eccb'
trainingDataT1AHCC_hash = 'd6e5990'
FreeSurfer_version = '5.3.0'
UKFTractography_hash = '421a7ad'
# tract_querier_hash = 'e045eab'
tract_querier_hash = 'c57d670'
ukfparams = ["--Ql", 70, "--Qm", 0.001, "--Rs", 0.015, "--numTensor", 2,
             "--recordLength", 1.7, "--seedFALimit", 0.18, "--seedsPerVoxel",
             10, "--stepLength", 0.3]


def _find_caseid(root):
        nodes = dag.preorder(root)
        caseid_nodes = [n for n in nodes if n.tag == 'caseid']
        caseids = {n.value for n in caseid_nodes}
        if len(caseids) > 1:
            raise Exception("{}: More than one caseid found in this DAG!".format(
                dag.showCompressedDAG(root)))
        if not caseid_nodes:
            raise Exception("{}: No caseid found in this DAG".format(
                dag.showCompressedDAG(node)))
        return caseid_nodes[0].value


def dag_filepath(node, ext, caseid_dir=True):
        caseid = _find_caseid(node)
        if ext and not ext.startswith('.'):
            ext = '.' + ext
        if caseid_dir:
            return local.path(config.OUTDIR) / caseid / showCompressedDAG(node) + ext
        return local.path(config.OUTDIR) / showCompressedDAG(node) + ext


def hash_filepath(node, ext, caseid_dir=True, extra_words=[]):
    def _hashstring(s):
        hasher = hashlib.md5()
        hasher.update(s)
        return hasher.hexdigest()[:10]

    caseid = _find_caseid(node)
    extras = [caseid] + extra_words if extra_words else [caseid]
    dagstr = dag.showDAG(node)
    for extra in extras:
        dagstr = dagstr.replace(extra, '')
    nodestem = '{}-{}-{}'.format(node.tag, '-'.join(extras),
                                     _hashstring(dagstr))
    if ext and not ext.startswith('.'):
        ext = '.' + ext

    if caseid_dir:
        return local.path(config.OUTDIR) / caseid / (nodestem + ext)
    return local.path(config.OUTDIR) / (nodestem + ext)


# class PNLNode(Node):
#     def write_provenance(self):
#             def isLeaf(n):
#                 if isinstance(n, dag.Leaf):
#                     return True
#                 if not n.deps:
#                     return True
#                 return False

#             allnodes = dag.preorder(self)
#             srcnodes = [n for n in allnodes
#                         if not isinstance(n, dag.Leaf) and not n.deps]
#             parameters = {"{}: {}".format(n.tag, 'None'
#                                         if not n.value else n.value)
#                         for n in allnodes if isinstance(n, dag.Leaf)}
#             nodepath = local.path(self.output())
#             outpath = nodepath + '.provenance'
#             srcpaths = {n.output() for n in srcnodes}
#             with open(outpath, 'w') as f:
#                 f.write('Compressed DAG:\n')
#                 f.write(dag.showCompressedDAG(self, isLeaf=isLeaf) + '\n\n')
#                 f.write('Source Paths:\n')
#                 f.write('\n'.join(srcpaths) + '\n\n')
#                 f.write('Parameters:\n')
#                 f.write('\n'.join(parameters) + '\n\n')
#                 f.write('Full DAG:\n')
#                 f.write(dag.showDAG(self))



@node(params=['key', 'caseid'])
class InputPathFromKey(Node):
    def output(self):
        return lookupInputKey(self.key, self.caseid)

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

    def show(self):
        return self.output()


class AutoOutput(Node):
    @abc.abstractproperty
    def ext(self):
        """Extension of output"""

    def output(self):
        return hash_filepath(self, self.ext)


class NrrdOutput(AutoOutput):
    @property
    def ext(self):
        return '.nrrd'


class NiftiOutput(AutoOutput):
    @property
    def ext(self):
        return '.nii.gz'


class DirOutput(AutoOutput):
    @property
    def ext(self):
        return ''


class CsvOutput(AutoOutput):
    @property
    def ext(self):
        return '.csv'


class VtkOutput(AutoOutput):
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
        with BRAINSTools.env(self.BRAINSTools_hash), TemporaryDirectory(
        ) as tmpdir:
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
             TemporaryDirectory() as tmpdir:
            bet_py('--force', '-f', self.bet_threshold, '-i', self.dwi, '-o',
                   self.output())


@node(params=['BRAINSTools_hash'], deps=['strct'])
class StrctXc(NrrdOutput):
    """Axis aligns and centers structural (nifti or nrrd)"""

    def static_build(self):
        with BRAINSTools.env(self.BRAINSTools_hash), \
             TemporaryDirectory() as tmpdir:
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
        with TemporaryDirectory() as tmpdir, BRAINSTools.env(
                self.BRAINSTools_hash):
            tmpdir = local.path(tmpdir)
            # antsRegistration can't handle a non-conventionally named file, so
            # we need to pass in a conventionally named one
            # TODO needed any more?
            tmpt1 = tmpdir / ('t1' + ''.join(self.t1.suffixes))
            from plumbum.cmd import ConvertBetweenFileFormats
            ConvertBetweenFileFormats[self.t1, tmpt1] & FG
            trainingCsv = trainingDataT1AHCC.get_path(
                self.trainingDataT1AHCC_hash) / 'trainingDataT1AHCC-hdr.csv'
            atlas_py['csv', '--fusion', 'avg', '-t', tmpt1, '-o', tmpdir,
                     trainingCsv] & FG
            (tmpdir / 'mask.nrrd').copy(self.output())


@node(params=['FreeSurfer_version'], deps=['t1', 't1mask'])
class FreeSurferUsingMask(DirOutput):
    """Runs FreeSurfer after masking the T1w with the given mask."""

    def stamp(self):
        return dirhash(self.output(), included_extensions=['.mgz'])

    def static_build(self):
        FreeSurfer.validate(self.FreeSurfer_version)
        fs_py['-i', self.t1, '-m', self.t1mask, '-f', '-o', self.output(
        ).dirname.dirname] & FG


@node(params=['BRAINSTools_hash'], deps=['fs', 'dwi', 'dwimask'])
class FsInDwiDirect(NiftiOutput):
    """Direct registration from FreeSurfer wmparc to DWI."""

    def static_build(self):
        fssubjdir = self.fs.dirname.dirname
        with TemporaryDirectory() as tmpdir, BRAINSTools.env(
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
        fssubjdir = self.fs.dirname.dirname
        with TemporaryDirectory() as tmpdir, BRAINSTools.env(
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
            script = local['pnlpipe_pipelines/pnlscripts/old/fs2dwi_T2.sh']
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
        with BRAINSTools.env(self.BRAINSTools_hash), TemporaryDirectory(
        ) as tmpdir:
            tmpdir = local.path(tmpdir)
            tmpdwi = tmpdir / 'dwi.nrrd'
            tmpdwimask = tmpdir / 'dwimask.nrrd'
            dwiconvert_py('-i', self.dwi, '-o', tmpdwi)
            convertImage(self.dwimask, tmpdwimask, self.bthash)
            params = ['--dwiFile', tmpdwi, '--maskFile', tmpdwimask,
                      '--seedsFile', tmpdwimask, '--recordTensors', '--tracts',
                      self.output()] + list(self.ukfparams)
            ukfpath = UKFTractography.get_path(self.UKFTractography_hash)
            log.info(' Found UKF at {}'.format(ukfpath))
            ukfbin = local[ukfpath]
            # ukfbin(*params)
            ukfbin.bound_command(*params) & FG


@node(params=['tract_querier_hash'], deps=['fsindwi', 'ukf'])
class Wmql(DirOutput):
    """White matter query language"""

    def stamp(self):
        return dirhash(self.output(), included_extensions=['.vtk'])

    def static_build(self):
        self.output().delete()
        with tract_querier.env(self.tract_querier_hash):
            wmql_py['-i', self.ukf, '--fsindwi', self.fsindwi, '-o',
                    self.output()] & FG


@node(params=['caseid'], deps=['wmql'])
class TractMeasures(CsvOutput):
    """Computes the diffusion measures of white matter tracts."""

    def static_build(self):
        measureTracts_py = local[
            'pnlpipe_pipelines/pnlscripts/measuretracts/measureTracts.py']
        vtks = self.wmql.up() // '*.vtk'
        measureTracts_py['-f', '-c', 'caseid', 'algo', '-v', self.caseid,
                         self.deps['wmql'].showCompressedDAG(
                         ), '-o', self.output(), '-i', vtks] & FG


def showCompressedDAG(node):
    def isLeaf(n):
        if isinstance(n, InputPathFromKey):
            return True
        if isinstance(n, InputFile):
            return True
        if not n.children:
            return True
        return False

    return dag.showCompressedDAG(node, isLeaf=isLeaf)
