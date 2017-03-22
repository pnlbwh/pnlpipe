import sys
from pipelines.pnllib import StrctXc, DwiXc, FsInDwiDirect, FreeSurferUsingMask, T1wMaskMabs, DwiMaskBet, DwiEd, UkfDefault, Wmql, TractMeasures, T2wMaskRigid, DwiEpi, DoesNotExistException, DwiHcp
from pipelib import Src
import pipelib

DEFAULT_TARGET = 'tractmeasures'

def makePipeline(caseid,
                 t1PathKey='t1',
                 dwiPosPathKeys=['dwiPos1', 'dwiPos2'],
                 dwiNegPathKeys=['dwiNeg1', 'dwiNeg2'],
                 echoSpacing=0.20,
                 peDir=2,
                 version_HCPPipelines='3.21.0',
                 version_FreeSurfer='5.3.0-HCP',
                 hash_UKFTractography='421a7ad',
                 hash_tract_querier='e045eab',
                 hash_BRAINSTools='41353e8',
                 hash_trainingDataT1AHCC='d6e5990'
):

    """HCP DWI preprocessing followed by standard PNL pipeline."""

    pipeline = {'_name': "standard PNL pipeline with no eddy correction"}
    pipeline['t1'] = Src(caseid, t1PathKey)
    posDwis = [Src(caseid,k) for k in dwiPosPathKeys]
    negDwis = [Src(caseid,k) for k in dwiNegPathKeys]
    pipeline['dwi'] = DwiHcp(caseid, posDwis, negDwis, echoSpacing, peDir, version_HCPPipelines)
    pipeline['t1xc'] = StrctXc(caseid, pipeline['t1'], hash_BRAINSTools)
    pipeline['dwimask'] = DwiMaskBet(caseid, pipeline['dwi'], 0.1, hash_BRAINSTools)
    pipeline['t1mask'] = T1wMaskMabs(caseid, pipeline['t1xc'],
                                     hash_trainingDataT1AHCC, hash_BRAINSTools)
    pipeline['fs'] = FreeSurferUsingMask(caseid, pipeline['t1xc'],
                                         pipeline['t1mask'])
    pipeline['fsindwi'] = FsInDwiDirect(caseid, pipeline['fs'],
                                        pipeline['dwi'], pipeline['dwimask'],
                                        hash_BRAINSTools)
    pipeline['ukf'] = UkfDefault(caseid, pipeline['dwi'], pipeline['dwimask'],
                                 hash_UKFTractography, hash_BRAINSTools)
    pipeline['wmql'] = Wmql(caseid, pipeline['fsindwi'], pipeline['ukf'],
                            hash_tract_querier)
    pipeline['tractmeasures'] = TractMeasures(caseid, pipeline['wmql'])
    return pipeline


def status(paramPoints):
    import pipelines.pnllib
    pipelines.pnllib.tractMeasureStatus(paramPoints, makePipeline)
