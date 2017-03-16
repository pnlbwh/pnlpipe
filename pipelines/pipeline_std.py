import sys
from pipelines.pnlnodes import StrctXc, DwiXc, FsInDwiDirect, FreeSurferUsingMask, T1wMaskMabs, DwiMaskHcpBet, DwiEd, UkfDefault, Wmql, TractMeasures, T2wMaskRigid, DwiEpi, DoesNotExistException, assertInputKeys
from pipelib import Src
import pipelib

def makePipeline(caseid,
                 t1Key,
                 dwiKey='',
                 hash_UKFTractography='421a7ad',
                 hash_tract_querier='e045eab',
                 hash_BRAINSTools='41353e8',
                 hash_trainingDataT1AHCC='d6e5990',
                 dwiedKey='',  # provide if hcp or buddi used
                 dwimaskKey=''
                 ):

    """Makes the PNL's standard pipeline. """
    pipeline = { 'name' : "standard PNL pipeline" }
    assertInputKeys(pipeline['name'], [t1Key])

    pipeline['t1'] = Src(caseid, t1Key)

    # get DWI, either it's in raw form or it's already been eddy corrected (by e.g. DRBUDDI or HCP pipeline)
    if dwiKey:
        pipeline['dwi'] = Src(caseid, dwiKey)
        pipeline['dwixc'] = DwiXc(caseid, pipeline['dwi'], hash_BRAINSTools) # works on nrrd or nii
        pipeline['dwied'] = Src(caseid, dwiedKey) if pipelib.INPUT_PATHS.get(
            dwiedKey) else DwiEd(caseid, pipeline['dwixc'], hash_BRAINSTools)
    elif dwiedKey:
        pipeline['dwied'] = Src(caseid, dwiedKey)
    else:
        print("pipeline_std.py: Error: either 'dwiKey' or 'dwiedKey' must be provided in 'params.std'")
        print("Use 'dwiKey' if you have a raw DWI, otherwise use 'dwiedKey' if you have an eddy corrected/preprocessed DWI.")
        sys.exit(1)

    pipeline['t1xc'] = StrctXc(caseid, pipeline['t1'], hash_BRAINSTools)

    pipeline['dwimask'] = Src(
        caseid, dwimaskKey) if pipelib.INPUT_PATHS.get(
            dwimaskKey) else DwiMaskHcpBet(caseid, pipeline['dwied'], hash_BRAINSTools)

    pipeline['t1mask'] = Src(
        caseid,
        't1mask') if pipelib.INPUT_PATHS.get('t1mask') else T1wMaskMabs(
            caseid, pipeline['t1xc'], hash_trainingDataT1AHCC, hash_BRAINSTools)

    pipeline['fs'] = FreeSurferUsingMask(caseid, pipeline['t1xc'],
                                         pipeline['t1mask'])
    pipeline['fsindwi'] = FsInDwiDirect(caseid, pipeline['fs'],
                                        pipeline['dwied'], pipeline['dwimask']
                                        ,hash_BRAINSTools)

    pipeline['ukf'] = UkfDefault(caseid, pipeline['dwied'],
                                 pipeline['dwimask'], hash_UKFTractography, hash_BRAINSTools)

    pipeline['wmql'] = Wmql(caseid, pipeline['fsindwi'], pipeline['ukf'],
                            hash_tract_querier)

    pipeline['tractmeasures'] = TractMeasures(caseid, pipeline['wmql'])

    pipeline['all'] = pipeline['tractmeasures']  # default target to build

    return pipeline


def status(paramPoints):
    import pandas as pd
    import sys
    if sys.version_info[0] < 3:
        from StringIO import StringIO
    else:
        from io import StringIO

    pipelines = [makePipeline(**paramPoint) for paramPoint in paramPoints]
    csvs = [p['tractmeasures'].path() for p in pipelines if p['tractmeasures'].path().exists()]
    df = pd.concat((pd.read_csv(csv) for csv in csvs))
    mask = df.tract.str.lower().apply( lambda x: any([ y in x for y in ['af','uf','slf','ioff']]))
    agg = {'FA_mean': {'FAmean_mean': 'mean' ,'FAmean_sd': 'std', 'count':'count'}
           ,'num': {'num_mean':'mean', 'num_sd': 'std'}
    }
    df = df[mask].filter(items=['FA_mean','num','tract']).groupby('tract').agg(agg)
    df.columns = df.columns.droplevel()
    df = df[['FAmean_mean','FAmean_sd','num_mean','num_sd','count']]

    INTRUST=StringIO(""""tract","FAmean_mean","FAmean_sd","num_mean","num_sd","count"
af.left,714.182544932399,30.4676278440711,433.140625,257.950520516233,384
af.right,696.470852774055,34.8401036745462,441.361038961039,290.948014111773,385
ioff.left,714.685249908589,30.4187930443161,131.124675324675,105.584410539235,385
ioff.right,707.633674637833,30.0749770765204,201.296875,135.805998900886,384
slf_iii.left,666.308324741928,29.5571559220112,656.311688311688,344.504930863216,385
slf_iii.right,660.472731188003,30.0607433890063,856.412987012987,439.223181852611,385
slf_ii.left,659.341421059491,32.6647141147986,339.862337662338,257.711077039572,385
slf_ii.right,660.085906472326,30.9626825136909,356.722077922078,271.30096133385,385
slf_i.left,591.851359327127,40.0703509639063,452.316883116883,264.787696699815,385
slf_i.right,580.02563236122,39.589693983944,278.345454545455,200.974326294543,385
uf.left,589.85265447185,42.8613369562814,195.744125326371,174.371158305798,383
uf.right,565.9559476129,43.1105907847185,142.316883116883,126.637537840325,385
    """)
    dfintrust= pd.read_csv(INTRUST, sep=",",index_col=0)

    print(df)
    print("Compare to INTRuST:")
    print(dfintrust)
