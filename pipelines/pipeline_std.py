import sys
from pipelines.pnlnodes import StrctXc, DwiXc, FsInDwiDirect, FreeSurferUsingMask, T1wMaskMabs, DwiMaskHcpBet, DwiEd, UkfDefault, Wmql, TractMeasures, T2wMaskRigid, DwiEpi, DoesNotExistException, assertInputKeys
from pipelib import Src
import pipelib

def makePipeline(caseid,
                 t1Key,
                 dwiKey='',
                 hash_UKFTractography='421a7ad',
                 hash_tract_querier='e045eab',
                 hash_BRAINSTools='41353e8',
                 hash_trainingDataT1AHCC='d6e5990',
                 dwiedKey='',  # provide if hcp or buddi used
                 dwimaskKey=''
                 ):

    """Makes the PNL's standard pipeline. """
    pipeline = { 'name' : "standard PNL pipeline" }
    assertInputKeys(pipeline['name'], [t1Key])

    pipeline['t1'] = Src(caseid, t1Key)

    # get DWI
    if dwiKey:
        pipeline['dwi'] = Src(caseid, dwiKey)
        pipeline['dwixc'] = DwiXc(caseid, pipeline['dwi'], hash_BRAINSTools) # works on nrrd or nii
        pipeline['dwied'] = Src(caseid, dwiedKey) if pipelib.INPUT_PATHS.get(
            dwiedKey) else DwiEd(caseid, pipeline['dwixc'], hash_BRAINSTools)
    elif dwiedKey:
        pipeline['dwied'] = Src(caseid, dwiedKey)
    else:
        print("pipeline_std.py: Error: either 'dwiKey' or 'dwiedKey' must be provided in 'params.std'")
        sys.exit(1)

    pipeline['t1xc'] = StrctXc(caseid, pipeline['t1'], hash_BRAINSTools)

    pipeline['dwimask'] = Src(
        caseid, dwimaskKey) if pipelib.INPUT_PATHS.get(
            dwimaskKey) else DwiMaskHcpBet(caseid, pipeline['dwied'], hash_BRAINSTools)

    pipeline['t1mask'] = Src(
        caseid,
        't1mask') if pipelib.INPUT_PATHS.get('t1mask') else T1wMaskMabs(
            caseid, pipeline['t1xc'], hash_trainingDataT1AHCC, hash_BRAINSTools)

    pipeline['fs'] = FreeSurferUsingMask(caseid, pipeline['t1xc'],
                                         pipeline['t1mask'])
    pipeline['fsindwi'] = FsInDwiDirect(caseid, pipeline['fs'],
                                        pipeline['dwied'], pipeline['dwimask']
                                        ,hash_BRAINSTools)

    pipeline['ukf'] = UkfDefault(caseid, pipeline['dwied'],
                                 pipeline['dwimask'], hash_UKFTractography, hash_BRAINSTools)

    pipeline['wmql'] = Wmql(caseid, pipeline['fsindwi'], pipeline['ukf'],
                            hash_tract_querier)

    pipeline['tractmeasures'] = TractMeasures(caseid, pipeline['wmql'])

    pipeline['all'] = pipeline['tractmeasures']  # default target to build

    return pipeline
