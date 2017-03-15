import sys
from pipelib import Src, GeneratedNode
from pipelines.pnlscripts.util import TemporaryDirectory
import pipelib
import software

class DwiMaskSlicer(GeneratedNode):
    def __init__(self, caseid, dwi, slicerVersion, mrtrix3Version):
        self.deps = [dwi]
        self.params = [slicerVersion, mrtrix3Version]
        self.ext = '.nii.gz'
        GeneratedNode.__init__(self, locals())

    def build(self):
        needDeps(self)
        with TemporaryDirectory() as tmpdir, local.cwd(tmpdir), software.Slicer.env(self.slicerVersion), software.mrtrix3.env(self.mrtrix3Version):
            from plumbum.cmd import Slicer, maskfilter
            Slicer['--launch', 'DiffusionWeightedVolumeMasking', self.dwi.path(),
                   'b0.nrrd', 'otsumask.nrrd', '--baselineBValueThreshold', '1000', '--removeislands'] & FG
            Slicer['--launch', 'ResampleScalarVolume', 'otsumask.nrrd', 'otsumask.nii'] & FG
            maskfilter['-scale', 2, self.path(), 'clean' ,'otsumask.nii', '-force'] & FG

def makePipeline(caseid, dwiKey='dwi', version_Slicer='4.7.0', hash_mrtrix3='97e4b3b'):
    pipeline = { 'name' : "dwi masking test" }
    pipeline['dwi'] = Src(caseid, dwiKey)
    pipeline['dwimask'] = DwiMaskSlicer(caseid, pipeline['dwi'], version_Slicer, hash_mrtrix3)

# /rfanfs/pnl-zorro/projects/Lyall_R03/Slicer-build2/Slicer-build/Slicer --launch DiffusionWeightedVolumeMasking  dwi.nhdr dwi_b0.nrrd dwi_OTSUtensormask.nrrd --baselineBValueThreshold 1000 --removeislands
# /rfanfs/pnl-zorro/projects/Lyall_R03/Slicer-build2/Slicer-build/Slicer --launch  ResampleScalarVolume dwi_OTSUtensormask.nrrd dwi_OTSUtensormask.nii
# maskfilter -scale 2 dwi_OTSUtensormask_cleaned.nii clean  dwi_OTSUtensormask.nii -force
