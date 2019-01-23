from pnlpipe_pipelines._pnl import *


def make_pipeline(caseid,
                  inputT1Key='t1',
                  inputDwiKey='dwi',
                  inputDwimaskKey='',
                  inputT1maskKey='',
                  bet_threshold=bet_threshold,
                  ukfparams=ukfparams,
                  BRAINSTools_hash=BRAINSTools_hash,
                  trainingDataT1AHCC_hash=trainingDataT1AHCC_hash,
                  FreeSurfer_version=FreeSurfer_version,
                  UKFTractography_hash=UKFTractography_hash,
                  tract_querier_hash=tract_querier_hash):
    """Standard PNL pipeline.

    dwi:           input DWI
    t1:            input T1w
    t1xc:          Aligined, centered T1w
    dwixc:         Aligned, centered DWI
    dwied:         Eddy current corrected DWI
    dwimask:       input mask, otherwise uses FSL bet
    fs:            FreeSurfer output directory
    fsindwi:       FreeSurfer wmparc in DWI space
    ukf:           UKF Tractograpy vtk file
    wmql:          directory of WMQL vtk tracts
    tractmeasures: csv of wmql tract measures

    """
    params = locals()

    tags = {}

    tags['dwi'] = InputPathFromKey([inputDwiKey, caseid])

    tags['t1'] = InputPathFromKey([inputT1Key, caseid])

    tags['dwixc'] = DwiXc(params, deps=[tags['dwi']])

    tags['dwied'] = DwiEd(params, deps=[tags['dwixc']])

    if inputDwimaskKey:
        tags['dwimask'] = InputPathFromKey(params=[inputDwimaskKey, caseid])
    else:
        tags['dwimask'] = DwiMaskBet(params, deps=[tags['dwied']])

    tags['t1xc'] = T1Xc(params, deps=[tags['t1']])

    if inputT1maskKey:
        tags['t1mask'] = InputKey(params=[inputT1maskKey, caseid])
    else:
        tags['t1mask'] = T1wMaskMabs(params, deps=[tags['t1xc']])

    tags['fs'] = FreeSurferUsingMask(params, deps=[tags['t1xc'],
                                                   tags['t1mask']])

    tags['fsindwi'] = FsInDwiDirect(params, deps=[tags['fs'],
                                                  tags['dwied'],
                                                  tags['dwimask']])

    tags['ukf'] = Ukf(params, deps=[tags['dwied'],
                                    tags['dwimask']])

    tags['wmql'] = Wmql(params, deps=[tags['fsindwi'],
                                      tags['ukf']])

    tags['tractmeasures'] = TractMeasures(params, deps=[tags['wmql']])

    return tags

DEFAULT_TARGET = 'tractmeasures'


def summarize(extra_flags=None):
    pipename = local.path(__file__).stem
    summarize_tractmeasures(pipename, extra_flags)
