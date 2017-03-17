from pipelines.pnllib import StrctXc, DwiXc, FsInDwiDirect, FreeSurferUsingMask, T1wMaskMabs, DwiMaskHcpBet, DwiEd, UkfDefault, Wmql, TractMeasures, T2wMaskRigid, DwiEpi, DoesNotExistException
from pipelib import Src
import pipelib

DEFAULT_TARGET = 'tractmeasures'

def makePipeline(caseid,
                 dwiPathKey='dwi',
                 t2PathKey='t2',
                 t1PathKey='t1',
                 t2maskPathKey='',
                 t1maskPathKey='',
                 dwimaskPathKey='',
                 hash_UKFTractography='421a7ad',
                 hash_tract_querier='e045eab',
                 hash_BRAINSTools='41353e8',
                 hash_trainingDataT1AHCC='d6e5990',
                ):
    """Makes the PNL's standard pipeline with EPI distortion correction. """
    pipeline = { '_name' :  "EPI correction pipeline" }
    pipeline['t1'] = Src(caseid, t1PathKey)
    pipeline['dwi'] = Src(caseid, dwiPathKey)
    pipeline['t2'] = Src(caseid, 't2')
    pipeline['t1xc'] = StrctXc(caseid, pipeline['t1'], hash_BRAINSTools)
    pipeline['t2xc'] = StrctXc(caseid, pipeline['t2'], hash_BRAINSTools)
    pipeline['dwixc'] = DwiXc(caseid, pipeline['dwi'], hash_BRAINSTools)
    pipeline['dwied'] = DwiEd(caseid, pipeline['dwixc'], hash_BRAINSTools)
    pipeline['dwimask'] = Src(
        caseid, dwimaskPathKey) if dwimaskPathKey else DwiMaskHcpBet(caseid, pipeline['dwied'], hash_BRAINSTools)
    pipeline['t1mask'] = Src(
        caseid,
        t1maskPathKey) if t1maskPathKey  else T1wMaskMabs(
            caseid, pipeline['t1xc'], hash_trainingDataT1AHCC, hash_BRAINSTools)
    pipeline['t2mask'] = Src(
        caseid,
        t2maskPathKey) if t2maskPathKey else T2wMaskRigid(
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
    return pipeline


def status(paramPoints):
    import pipelines.pnllib
    pipelines.pnllib.tractMeasureStatus(paramPoints, makePipeline)
