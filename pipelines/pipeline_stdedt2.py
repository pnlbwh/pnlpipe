import sys
from pipelines.pnllib import StrctXc, DwiXc, FsInDwiUsingT2, FreeSurferUsingMask, T1wMaskMabs, DwiMaskBet, DwiEd, UkfDefault, Wmql, TractMeasures, MaskRigid, DwiEpi, DoesNotExistException
from pipelib import Src
import pipelib

DEFAULT_TARGET = 'tractmeasures'

def makePipeline(caseid,
                 dwiPathKey,
                 t1PathKey,
                 t2PathKey,
                 dwimaskPathKey='',
                 version_FreeSurfer='5.3.0',
                 hash_UKFTractography='421a7ad',
                 hash_tract_querier='e045eab',
                 hash_BRAINSTools='41353e8',
                 hash_trainingDataT1AHCC='d6e5990'):
    """Makes the PNL's standard pipeline, given an eddy corrected DWI
    (For example, a DRBUDDI processed DWI.). Same as 'std' except eddy
    current correction is not performed."""
    pipeline = {'_name': "standard PNL pipeline with no eddy correction"}
    pipeline['t1'] = Src(caseid, t1PathKey)
    pipeline['t2'] = Src(caseid, t2PathKey)
    pipeline['dwi'] = Src(caseid, dwiPathKey)
    pipeline['t1xc'] = StrctXc(caseid, pipeline['t1'], hash_BRAINSTools)
    pipeline['t2xc'] = StrctXc(caseid, pipeline['t2'], hash_BRAINSTools)
    pipeline['dwimask'] = Src(caseid,
                              dwimaskPathKey) if dwimaskPathKey else DwiMaskBet(caseid, pipeline['dwi'], 0.1, hash_BRAINSTools)
    pipeline['t1mask'] = T1wMaskMabs(caseid, pipeline['t1xc'],
                                     hash_trainingDataT1AHCC, hash_BRAINSTools)
    pipeline['t2mask'] = MaskRigid(caseid
                                   , pipeline['t2xc']
                                   , pipeline['t1xc']
                                   , pipeline['t1mask']
                                   , hash_BRAINSTools)
    pipeline['fs'] = FreeSurferUsingMask(caseid, pipeline['t1xc'],
                                         pipeline['t1mask'], version_FreeSurfer)
    pipeline['fsindwi'] = FsInDwiUsingT2(caseid
                                         , pipeline['fs']
                                         , pipeline['t1xc']
                                         , pipeline['t1mask']
                                         , pipeline['t2xc']
                                         , pipeline['t2mask']
                                         , pipeline['dwi']
                                         , pipeline['dwimask']
                                         , hash_BRAINSTools)
    pipeline['ukf'] = UkfDefault(caseid, pipeline['dwi'], pipeline['dwimask'],
                                 hash_UKFTractography, hash_BRAINSTools)
    pipeline['wmql'] = Wmql(caseid, pipeline['fsindwi'], pipeline['ukf'],
                            hash_tract_querier)
    pipeline['tractmeasures'] = TractMeasures(caseid, pipeline['wmql'])
    return pipeline


def status(combos, extraFlags=[]):
    import pipelines.pnllib
    pipelines.pnllib.tractMeasureStatus(combos, extraFlags)
