from pnlpipe_pipelines._pnl import *


def make_pipeline(caseid,
                  inputT1Key='t1',
                  inputT2Key='t2',
                  inputDwiKey='dwi',
                  inputDwiMaskKey='',
                  inputT1MaskKey='',
                  inputT2MaskKey='',
                  bet_threshold=bet_threshold,
                  ukfparams=ukfparams,
                  BRAINSTools_hash=BRAINSTools_hash,
                  trainingDataT1AHCC_hash=trainingDataT1AHCC_hash,
                  FreeSurfer_version=FreeSurfer_version,
                  UKFTractography_hash=UKFTractography_hash,
                  tract_querier_hash=tract_querier_hash):
    """Standard PNL pipeline with EPI distortion correction.

    dwi:           input DWI
    t1:            input T1w
    t2:            input T2w
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

    tags['t2'] = InputPathFromKey([inputT2Key, caseid])

    tags['dwixc'] = DwiXc(params, deps=[tags['dwi']])

    tags['t1xc'] = T1Xc(params, deps=[tags['t1']])

    tags['t2xc'] = T2Xc(params, deps=[tags['t2']])

    tags['dwied'] = DwiEd(params, deps=[tags['dwixc']])

    if inputDwiMaskKey:
        tags['dwimask'] = InputKey(params=[inputDwimaskKey, caseid])
    else:
        tags['dwimask'] = DwiMaskBet(params, deps=[tags['dwied']])

    tags['t1xc'] = T1Xc(params, deps=[tags['t1']])

    if inputT1MaskKey:
        tags['t1mask'] = InputKey(params=[inputT1maskKey, caseid])
    else:
        tags['t1mask'] = T1wMaskMabs(params, deps=[tags['t1xc']])

    if inputT2MaskKey:
        tags['t2mask'] = InputKey(params=[inputT2MaskKey, caseid])
    else:
        tags['t2mask'] = MaskRigid(params, deps={'moving': tags['t1xc'],
                                                 'moving_mask': tags['t1mask'],
                                                 'fixed': tags['t2xc'] })


    tags['dwiepi'] = DwiEpi(params, deps={'dwi': tags['dwied'],
                                          'dwimask': tags['dwimask'],
                                          't2': tags['t2xc'],
                                          't2mask': tags['t2mask']})

    tags['dwiepimask'] = DwiEpiMask(params, deps=[tags['dwiepi']])


    tags['fs'] = FreeSurferUsingMask(params, deps=[tags['t1xc'],
                                                   tags['t1mask']])

    tags['fsindwi'] = FsInDwiDirect(params, deps=[tags['fs'],
                                                  tags['dwiepi'],
                                                  tags['dwiepimask']])

    tags['ukf'] = Ukf(params, deps=[tags['dwiepi'],
                                    tags['dwiepimask']])

    tags['wmql'] = Wmql(params, deps=[tags['fsindwi'],
                                      tags['ukf']])

    tags['tractmeasures'] = TractMeasures(params, deps=[tags['wmql']])

    return tags

DEFAULT_TARGET = 'tractmeasures'


def summarize(extra_flags=None):
    pipename = local.path(__file__).stem
    summarize_tractmeasures(pipename, extra_flags)
