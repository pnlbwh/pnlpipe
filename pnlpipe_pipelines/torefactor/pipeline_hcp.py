from pnlpipe_tagss.pnl import *


def make_tags(caseid,
                  inputT1Key='t1',
                  inputDwiPosKeys=['dwiPos1', 'dwiPos2'],
                  inputDwiNegKeys=['dwiNeg1', 'dwiNeg2'],
                  echoSpacing=0.20,
                  peDir=2,
                  version_HCPTagss='3.21.0',
                  version_FreeSurfer='5.3.0-HCP',
                  UKFTractography_hash=UKFTractography_hash,
                  tract_querier_hash=tract_querier_hash,
                  BRAINSTools_hash=BRAINSTools_hash,
                  trainingDataT1AHCC_hash=trainingDataT1AHCC_hash
):

    """HCP DWI preprocessing followed by standard PNL tags."""

    tags['t1'] = InputKey([inputT1Key, caseid])

    posDwis = [InputKey([k,caseid]) for k in dwiPosPathKeys]
    negDwis = [InputKey([k,caseid]) for k in dwiNegPathKeys]

    tags['dwi'] = DwiHcp(params=[HCPPipelines_version, echoSpacing, peDir],
                         deps=[posDwis, negDwis])

    tags['t1xc'] = StrctXc(params, deps=[tags['t1']])

    tags['dwimask'] = DwiMaskBet(params=[0.1, BRAINSTools_hash],
                                 deps=[tags['dwi']])

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

    tags['_default_target'] = tags['tractmeasures']

    return tags


def status(combos, extraFlags=[]):
    import pnlpipe_tagss.pnlnodes
    pnlpipe_tagss.pnlnodes.tractMeasureStatus(combos, extraFlags)
