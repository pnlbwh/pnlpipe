import sys
from pnlpipe_lib import InputKey, GeneratedNode, needDeps
from pnlpipe_pipelines.pnlscripts.util import TemporaryDirectory
import pnlpipe_software
import plumbum
from plumbum import local, FG

DEFAULT_TARGET = 'dice'


class DwiMaskSlicer(GeneratedNode):
    def __init__(self, caseid, dwi, version_Slicer, hash_mrtrix3):
        self.deps = [dwi]
        self.params = [version_Slicer, hash_mrtrix3]
        self.ext = '.nii.gz'
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with TemporaryDirectory() as tmpdir, local.cwd(
                tmpdir), pnlpipe_software.mrtrix3.env(self.hash_mrtrix3):
            from plumbum.cmd import maskfilter
            slicerDir = pnlpipe_software.Slicer.getPath(self.version_Slicer).dirname
            Slicer = local[slicerDir / 'Slicer']
            Slicer['--launch', slicerDir / 'DiffusionWeightedVolumeMasking', self.dwi.path(),
                   'b0.nrrd', 'otsumask.nrrd', '--baselineBValueThreshold', '1000', '--removeislands'] & FG
            Slicer['--launch', 'ResampleScalarVolume', 'otsumask.nrrd', 'otsumask.nii'] & FG
            maskfilter['-scale', 2, 'otsumask.nii', 'clean', self.output(),
                       '-force'] & FG

class DiceCoefficient(GeneratedNode):
    def __init__(self, caseid, maskManual, mask, hash_BRAINSTools):
        self.deps = [maskManual, mask]
        self.params = [hash_BRAINSTools]
        self.ext = '.txt'
        GeneratedNode.__init__(self, locals())

    def build(self):
        from plumbum.cmd import ImageMath
        needDeps(self)
        with TemporaryDirectory() as tmpdir, pnlpipe_software.BRAINSTools.env(self.hash_BRAINSTools):
            tmptxt = tmpdir / 'dice.txt'
            ImageMath[3, tmptxt, "DiceAndMinDistSum", self.maskManual.path(), self.mask.path()] & FG
            with open(tmptxt, 'r') as f:
                coeff = f.read().split(' ')[-1]
            with open(self.output(), 'w') as f:
                f.write(coeff)


def makePipeline(caseid,
                 dwiPathKey='dwi',
                 dwimaskManualPathKey='dwimaskManual',
                 version_Slicer='4.7.0',
                 hash_BRAINSTools='41353e8',
                 hash_mrtrix3='97e4b3b'):
    pipeline = {'_name': "dwi masking test"}
    pipeline['dwi'] = InputKey(caseid, dwiPathKey)
    pipeline['dwimaskManual'] = InputKey(caseid, dwimaskManualPathKey)
    pipeline['dwimask'] = DwiMaskSlicer(caseid, pipeline['dwi'],
                                        version_Slicer, hash_mrtrix3)
    pipeline['dice'] = DiceCoefficient(caseid, pipeline['dwimaskManual'], pipeline['dwimask'], hash_BRAINSTools)
    return pipeline


def status(combos):
    pps = sorted(combos, key = lambda x: x['caseid'])
    pnlpipe_pipelines = [makePipeline(**paramPoint) for paramPoint in pps]
    coeff_paths = [p['dice'].path() for p in pnlpipe_pipelines
            if p['dice'].path().exists()]
    coeffs = map(lambda f: float(open(f,'r').read()), coeff_paths)
    if coeffs:
        for f, coeff in zip(coeff_paths, coeffs):
            print("{}|{}".format(coeff, f - local.cwd))
        avg = sum(coeffs) / len(coeffs)
        print("Average dice coefficient: {}".format(avg))
    else:
        print("No dice coefficients computed yet.")

# /rfanfs/pnl-zorro/projects/Lyall_R03/Slicer-build2/Slicer-build/Slicer --launch DiffusionWeightedVolumeMasking  dwi.nhdr dwi_b0.nrrd dwi_OTSUtensormask.nrrd --baselineBValueThreshold 1000 --removeislands
# /rfanfs/pnl-zorro/projects/Lyall_R03/Slicer-build2/Slicer-build/Slicer --launch  ResampleScalarVolume dwi_OTSUtensormask.nrrd dwi_OTSUtensormask.nii
# maskfilter -scale 2 dwi_OTSUtensormask_cleaned.nii clean  dwi_OTSUtensormask.nii -force
