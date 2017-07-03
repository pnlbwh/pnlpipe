import sys
from pp_pipelines.pnllib import StrctXc, DwiXc, FsInDwiDirect, FreeSurferUsingMask, T1wMaskMabs, DwiMaskBet, DwiEd, UkfDefault, Wmql, TractMeasures, MaskRigid, DwiEpi, DoesNotExistException
from pnlpipe import Src

DEFAULT_TARGET = 'tractmeasures'

def makePipeline(caseid,
                 t1PathKey='t1raw',
                 dwiPathKey='dwiraw',
                 dwimaskPathKey='',
                 t1maskPathKey='',
                 version_FreeSurfer='5.3.0',
                 hash_UKFTractography='421a7ad',
                 hash_tract_querier='e045eab',
                 hash_BRAINSTools='41353e8',
                 hash_trainingDataT1AHCC='d6e5990'
                 ):
    """Makes the PNL's standard pipeline. """
    pipeline = {'_name': "standard PNL pipeline"}
    pipeline['t1raw'] = Src(caseid, t1PathKey)
    pipeline['dwiraw'] = Src(caseid, dwiPathKey)
    pipeline['dwixc'] = DwiXc(caseid, pipeline['dwiraw'],
                                hash_BRAINSTools)  # works on nrrd or nii
    pipeline['dwied'] = DwiEd(caseid, pipeline['dwixc'], hash_BRAINSTools)
    pipeline['t1xc'] = StrctXc(caseid, pipeline['t1raw'], hash_BRAINSTools)
    pipeline['dwimask'] = Src(caseid,
                              dwimaskPathKey) if dwimaskPathKey else DwiMaskBet(
                                  caseid, pipeline['dwied'], 0.1, hash_BRAINSTools)
    pipeline['t1mask'] = Src(caseid, t1maskPathKey) if t1maskPathKey else T1wMaskMabs(
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


def status(combos):
    import pp_pipelines.pnllib
    pp_pipelines.pnllib.tractMeasureStatus(combos, makePipeline)