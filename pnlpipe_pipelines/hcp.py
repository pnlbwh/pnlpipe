from pnlpipe_pipelines._pnl import *


def make_pipeline(caseid,
                  inputT1Key='t1',
                  inputDwiPosKeys=['dwiPos1', 'dwiPos2'],
                  inputDwiNegKeys=['dwiNeg1', 'dwiNeg2'],
                  echo_spacing=0.20,
                  pe_dir=2,
                  bet_threshold=0.1,
                  HCPPipelines_version='3.21.0',
                  FreeSurfer_version='5.3.0-HCP',
                  ukfparams=ukfparams,
                  BRAINSTools_hash=BRAINSTools_hash,
                  trainingDataT1AHCC_hash=trainingDataT1AHCC_hash,
                  UKFTractography_hash=UKFTractography_hash,
                  tract_querier_hash=tract_querier_hash):

    """HCP DWI preprocessing followed by standard PNL pipeline.

    """
    params = locals()

    tags = {}

    tags['t1'] = InputPathFromKey([inputT1Key, caseid])

    pos_dwis = [InputPathFromKey([k,caseid]) for k in dwiPosPathKeys]
    neg_dwis = [InputPathFromKey([k,caseid]) for k in dwiNegPathKeys]

    tags['dwi'] = DwiHcp(params, deps=[pos_dwis, neg_dwis])

    tags['t1xc'] = StrctXc(params, deps=[tags['t1']])

    tags['dwimask'] = DwiMaskBet(params, deps=[tags['dwi']])

    tags['t1mask'] = T1wMaskMabs(params, deps=[tags['t1xc']])

    tags['fs'] = FreeSurferUsingMask(params, deps=[tags['t1xc'],
                                                   tags['t1mask']])

    tags['fsindwi'] = FsInDwiDirect(params, deps=[tags['fs'],
                                                  tags['dwi'],
                                                  tags['dwimask']])

    tags['ukf'] = Ukf(params, deps=[tags['dwi'],
                                    tags['dwimask']])

    tags['wmql'] = Wmql(params, deps=[tags['fsindwi'],
                                      tags['ukf']])

    tags['tractmeasures'] = TractMeasures(params, deps=[tags['wmql']])

    return tags


DEFAULT_TARGET = 'tractmeasures'


def summarize(extra_flags=None):
    pipename = local.path(__file__).stem
    summarize_tractmeasures(pipename, extra_flags)
