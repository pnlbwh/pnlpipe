import sys
from pnlpipe_pipelines.pnlnodes2 import DwiXc, DwiMaskBet, DwiEd
from pnlpipe_lib import InputKey

DEFAULT_TARGET = 'dwixc'

def make_pipeline(caseid,
                 inputT1Key,
                 inputDwiKey,
                 inputDwimaskKey='',
                 inputT1maskKey='',
                 version_FreeSurfer='5.3.0',
                 hash_UKFTractography='421a7ad',
                 hash_tract_querier='e045eab',
                 hash_BRAINSTools='41353e8',
                 hash_trainingDataT1AHCC='d6e5990'
                 ):

    params = locals()
    """The PNL's standard pipeline.
Pipeline node key descriptions:
    t1:            input T1w
    dwi:           input DWI
    dwixc:         axis-aligned and centered DWI
    dwied:         eddy corrected, axis-aligned, centered DWI
    t1xc:          axis-aligned and centered T1w
    dwimask:       if inputDwimaskKey is empty, then generated FSL bet mask
    t1mask:        if inputT1maskKey is empty, then generated MABS T1w mask
    fs:            FreeSurfer subject directory
    fsindwi:       FreeSurfer labelmap (wmparc) registered to dwied
    ukf:           Whole brain UKF Tractography vtk
    wmql:          directory of WMQL tracts (vtk files)
    tractmeasures: CSV of WMQL tract measures
    """

    pipeline = {'_name': "standard PNL pipeline"}
    pipeline['t1'] = InputKey(caseid, inputT1Key)
    pipeline['dwi'] = InputKey(caseid, inputDwiKey)
    pipeline['dwixc'] = DwiXc(caseid, pipeline['dwi'],
                                **params)
    return pipeline


def status(combos, extraFlags=[]):
    import pnlpipe_pipelines.pnlnodes
    pnlpipe_pipelines.pnlnodes.tractMeasureStatus(combos, extraFlags)
