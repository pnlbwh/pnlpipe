from pipelines.pnllib import StrctXc, DwiXc, FsInDwiDirect, FreeSurferUsingMask, T1wMaskMabs, DwiMaskBet, DwiEd, UkfDefault, Wmql, TractMeasures, MaskRigid, DwiEpi, DoesNotExistException
from pipelib import Src
import pipelib

DEFAULT_TARGET = 'tractmeasures'

def makePipeline(caseid,
                 dwiPathKey='dwiraw',
                 t2PathKey='t2raw',
                 t1PathKey='t1raw',
                 t2maskPathKey='',
                 t1maskPathKey='',
                 dwimaskPathKey='',
                 betThreshold=0.1,
                 version_FreeSurfer='5.3.0',
                 hash_UKFTractography='421a7ad',
                 hash_tract_querier='e045eab',
                 hash_BRAINSTools='41353e8',
                 hash_trainingDataT1AHCC='d6e5990',
                ):
    """Makes the PNL's standard pipeline with EPI distortion correction. """
    pipeline = { '_name' :  "EPI correction pipeline" }
    pipeline['t1raw'] = Src(caseid, t1PathKey)
    pipeline['dwiraw'] = Src(caseid, dwiPathKey)
    pipeline['t2raw'] = Src(caseid, 't2raw')
    pipeline['t1xc'] = StrctXc(caseid, pipeline['t1raw'], hash_BRAINSTools)
    pipeline['t2xc'] = StrctXc(caseid, pipeline['t2raw'], hash_BRAINSTools)
    pipeline['dwixc'] = DwiXc(caseid, pipeline['dwiraw'], hash_BRAINSTools)
    pipeline['dwied'] = DwiEd(caseid, pipeline['dwixc'], hash_BRAINSTools)
    pipeline['dwimask'] = Src(
        caseid, dwimaskPathKey) if dwimaskPathKey else DwiMaskBet(caseid, pipeline['dwied'], betThreshold, hash_BRAINSTools)
    pipeline['t1mask'] = Src(
        caseid,
        t1maskPathKey) if t1maskPathKey  else T1wMaskMabs(
            caseid, pipeline['t1xc'], hash_trainingDataT1AHCC, hash_BRAINSTools)
    pipeline['t2mask'] = Src(
        caseid,
        t2maskPathKey) if t2maskPathKey else MaskRigid(
            caseid
            , pipeline['t2xc']
            , pipeline['t1xc']
            , pipeline['t1mask']
            , hash_BRAINSTools)
    pipeline['dwiepi'] = DwiEpi(caseid, pipeline['dwied'], pipeline['dwimask'],
                                pipeline['t2xc'], pipeline['t2mask'],hash_BRAINSTools)
    pipeline['fs'] = FreeSurferUsingMask(caseid, pipeline['t1xc'],
                                         pipeline['t1mask'], version_FreeSurfer)
    pipeline['fsindwi'] = FsInDwiDirect(caseid, pipeline['fs'],
                                        pipeline['dwiepi'], pipeline['dwimask'], hash_BRAINSTools)
    pipeline['ukf'] = UkfDefault(caseid, pipeline['dwiepi'],
                                 pipeline['dwimask'], hash_UKFTractography, hash_BRAINSTools)
    pipeline['wmql'] = Wmql(caseid, pipeline['fsindwi'], pipeline['ukf'],
                            hash_tract_querier)
    pipeline['tractmeasures'] = TractMeasures(caseid, pipeline['wmql'])
    return pipeline


def status(combos):
    import pipelines.pnllib
    pipelines.pnllib.tractMeasureStatus(combos, makePipeline)
