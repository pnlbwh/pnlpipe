from pipelines.pnlnodes import StrctXc, DwiXc, FsInDwiDirect, FreeSurferUsingMask, T1wMaskMabs, DwiMaskHcpBet, DwiEd, UkfDefault, Wmql, TractMeasures, T2wMaskRigid, DwiEpi, DoesNotExistException, assertInputKeys
from pipelib import Src
import pipelib

def makePipeline(caseid,
                 dwiKey,
                 t2Key,
                 t1Key,
                 t2maskKey='',
                 t1maskKey='',
                 dwimaskKey='',
                 hash_UKFTractography='421a7ad',
                 hash_tract_querier='e045eab',
                 hash_BRAINSTools='41353e8',
                 hash_trainingDataT1AHCC='d6e5990',
                ):
    """Makes the PNL's standard pipeline with EPI distortion correction. """

    pipeline = { 'name' :  "EPI correction pipeline" }
    assertInputKeys(pipeline['name'], [dwiKey, t1Key, t2Key])

    pipeline['t1'] = Src(caseid, t1Key)
    pipeline['dwi'] = Src(caseid, dwiKey)
    pipeline['t2'] = Src(caseid, 't2')

    pipeline['t1xc'] = StrctXc(caseid, pipeline['t1'], hash_BRAINSTools)
    pipeline['t2xc'] = StrctXc(caseid, pipeline['t2'], hash_BRAINSTools)
    # run DwiXc first as it's able to convert a DWI nifti to nrrd
    pipeline['dwixc'] = DwiXc(caseid, pipeline['dwi'], hash_BRAINSTools)
    pipeline['dwied'] = DwiEd(caseid, pipeline['dwixc'], hash_BRAINSTools)

    pipeline['dwimask'] = Src(
        caseid, dwimaskKey) if dwimaskKey else DwiMaskHcpBet(caseid, pipeline['dwied'], hash_BRAINSTools)

    pipeline['t1mask'] = Src(
        caseid,
        t1maskKey) if t1maskKey  else T1wMaskMabs(
            caseid, pipeline['t1xc'], hash_trainingDataT1AHCC, hash_BRAINSTools)

    pipeline['t2mask'] = Src(
        caseid,
        t2maskKey) if t2maskKey else T2wMaskRigid(
            caseid, pipeline['t2xc'], pipeline['t1xc'], pipeline['t1mask'],hash_BRAINSTools)

    pipeline['dwiepi'] = DwiEpi(caseid, pipeline['dwied'], pipeline['dwimask'],
                                pipeline['t2xc'], pipeline['t2mask'],hash_BRAINSTools)

    pipeline['fs'] = FreeSurferUsingMask(caseid, pipeline['t1xc'],
                                         pipeline['t1mask'])
    pipeline['fsindwi'] = FsInDwiDirect(caseid, pipeline['fs'],
                                        pipeline['dwiepi'], pipeline['dwimask'], hash_BRAINSTools)

    pipeline['ukf'] = UkfDefault(caseid, pipeline['dwiepi'],
                                 pipeline['dwimask'], hash_UKFTractography, hash_BRAINSTools)

    pipeline['wmql'] = Wmql(caseid, pipeline['fsindwi'], pipeline['ukf'],
                            hash_tract_querier)
    pipeline['tractmeasures'] = TractMeasures(caseid, pipeline['wmql'])

    pipeline['all'] = pipeline['tractmeasures']  # default target to build

    return pipeline


def status(paramPoints):
    import pandas as pd
    from pipelines.pnlscripts.summarizeTractMeasures import summarize

    pipelines = [makePipeline(**paramPoint) for paramPoint in paramPoints]
    csvs = [p['tractmeasures'].path() for p in pipelines if p['tractmeasures'].path().exists()]

    if csvs:
        df = pd.concat((pd.read_csv(csv) for csv in csvs))
        summarize(df)
