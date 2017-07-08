import sys
from pnlpipe_pipelines.pnlnodes import StrctXc, DwiXc, FsInDwiDirect, FreeSurferUsingMask, T1wMaskMabs, DwiMaskBet, DwiEd, UkfDefault, Wmql, TractMeasures, MaskRigid, DwiEpi, DoesNotExistException
from pnlpipe_lib import InputKey

DEFAULT_TARGET = 'tractmeasures'

def make_pipeline(caseid,
                 inputT1Key,
                 inputDwiKey,
                 inputDwimaskKey='',
                 inputT1maskKey='',
                 version_FreeSurfer='5.3.0',
                 hash_UKFTractography='421a7ad',
                 hash_tract_querier='e045eab',
                 hash_BRAINSTools='41353e8',
                 hash_trainingDataT1AHCC='d6e5990'
                 ):
    """The PNL's standard pipeline.
Pipeline node key descriptions:
    t1:            input T1w
    dwi:           input DWI
    dwixc:         axis-aligned and centered DWI
    dwied:         eddy corrected, axis-aligned, centered DWI
    t1xc:          axis-aligned and centered T1w
    dwimask:       if inputDwimaskKey is empty, then generated FSL bet mask
    t1mask:        if inputT1maskKey is empty, then generated MABS T1w mask
    fs:            FreeSurfer subject directory
    fsindwi:       FreeSurfer labelmap (wmparc) registered to dwied
    ukf:           Whole brain UKF Tractography vtk
    wmql:          directory of WMQL tracts (vtk files)
    tractmeasures: CSV of WMQL tract measures
    """

    pipeline = {'_name': "standard PNL pipeline"}
    pipeline['t1'] = InputKey(caseid, inputT1Key)
    pipeline['dwi'] = InputKey(caseid, inputDwiKey)
    pipeline['dwixc'] = DwiXc(caseid, pipeline['dwi'],
                                hash_BRAINSTools)  # works on nrrd or nii
    pipeline['dwied'] = DwiEd(caseid, pipeline['dwixc'], hash_BRAINSTools)
    pipeline['t1xc'] = StrctXc(caseid, pipeline['t1'], hash_BRAINSTools)
    pipeline['dwimask'] = InputKey(caseid,
                              inputDwimaskKey) if inputDwimaskKey else DwiMaskBet(
                                  caseid, pipeline['dwied'], 0.1, hash_BRAINSTools)
    pipeline['t1mask'] = InputKey(caseid, inputT1maskKey) if inputT1maskKey else T1wMaskMabs(
        caseid, pipeline['t1xc'], hash_trainingDataT1AHCC, hash_BRAINSTools)
    pipeline['fs'] = FreeSurferUsingMask(caseid, pipeline['t1xc'],
                                         pipeline['t1mask'], version_FreeSurfer)
    pipeline['fsindwi'] = FsInDwiDirect(caseid, pipeline['fs'],
                                        pipeline['dwied'], pipeline['dwimask'],
                                        hash_BRAINSTools)
    pipeline['ukf'] = UkfDefault(caseid, pipeline['dwied'],
                                 pipeline['dwimask'], hash_UKFTractography,
                                 hash_BRAINSTools)
    pipeline['wmql'] = Wmql(caseid, pipeline['fsindwi'], pipeline['ukf'],
                            hash_tract_querier)
    pipeline['tractmeasures'] = TractMeasures(caseid, pipeline['wmql'])
    return pipeline


def status(combos, extraFlags=[]):
    import pnlpipe_pipelines.pnlnodes
    pnlpipe_pipelines.pnlnodes.tractMeasureStatus(combos, extraFlags)
