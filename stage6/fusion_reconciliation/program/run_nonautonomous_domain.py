"""Preserve actual local-chart success/failure as the fixed-origin window grows."""
import argparse,json,sys,time
import numpy as np
import torch
from nonautonomous_transport import ROOT,TimeGainCoilTransport,inherit_second_order_cache,MoserChart
from run_transport_experiments import clean


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='time_gain_domain');args=parser.parse_args()
    out=ROOT/'stage6/fusion_reconciliation/results/algorithms'/f'{args.run_id}.json'
    if out.exists():raise FileExistsError('Choose a new run-id; failures are evidence')
    torch.set_num_threads(1);native=TimeGainCoilTransport();cache,_=inherit_second_order_cache(native)
    rows=[]
    for t in [.0005,.005,.05,.5,2.]:
        before=time.perf_counter();chart=MoserChart(cache,2)
        row=dict(time=t,bounds=cache.ball_bounds(t,2,.002))
        try:
            row.update(status='completed',diagnostics=chart.diagnostics(cache.center,t))
        except (ValueError,RuntimeError,np.linalg.LinAlgError) as exc:
            row.update(status='failed',error=repr(exc))
        row['seconds']=time.perf_counter()-before;rows.append(row)
        out.write_text(json.dumps(dict(command=[sys.executable,*sys.argv],metadata=native.metadata(),rows=rows,
            scope='Fixed-origin finite cached polynomial only. Local chart failure is not physical instability; long-window time-series accuracy is not certified.'),indent=2,default=clean)+'\n')
        print(t,row['status'],flush=True)


if __name__=='__main__':main()
