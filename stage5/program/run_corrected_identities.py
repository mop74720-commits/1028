"""Run shared correction tests and preserve every attempt, including failures."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import time
import unittest

import numpy
import scipy
import sympy

STAGE=Path(__file__).resolve().parents[1]
ROOT=STAGE.parent
BASE=STAGE/'results'/'corrected_identities'
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
run=BASE/'runs'/stamp
run.mkdir(parents=True,exist_ok=False)
out=io.StringIO()

class EvidenceResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.records=[]
    def addSuccess(self,test):
        super().addSuccess(test);self.records.append({'test':test.id(),'status':'executed_pass'})
    def addFailure(self,test,err):
        super().addFailure(test,err);self.records.append({'test':test.id(),'status':'executed_failure'})
    def addError(self,test,err):
        super().addError(test,err);self.records.append({'test':test.id(),'status':'executed_error'})
    def addSkip(self,test,reason):
        super().addSkip(test,reason);self.records.append({'test':test.id(),'status':'skipped','reason':reason})

files=[STAGE/'program/corrected_identities.py',STAGE/'tests/test_corrected_identities.py',
       ROOT/'stage4/audit/proof_errors_and_corrections.md',
       ROOT/'stage4/audit/source_omml/original1025_indexed.json']
hashes=lambda:{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before=hashes();start=time.perf_counter()
suite=unittest.defaultTestLoader.discover(str(STAGE/'tests'),pattern='test_corrected_identities.py')
result=unittest.TextTestRunner(stream=out,verbosity=2,resultclass=EvidenceResult).run(suite)
elapsed=time.perf_counter()-start
(run/'tests.log').write_text(out.getvalue())
report=dict(status='executed_pass' if result.wasSuccessful() else 'executed_failure',
    command=[sys.executable,str(Path(__file__).relative_to(ROOT))],cwd=str(ROOT),
    start_utc=stamp,wall_seconds=elapsed,tests_run=result.testsRun,
    tests_failed=len(result.failures),tests_errors=len(result.errors),tests_skipped=len(result.skipped),
    environment=dict(python=platform.python_version(),numpy=numpy.__version__,
                     scipy=scipy.__version__,sympy=sympy.__version__,platform=platform.platform()),
    records=result.records,source_sha256_before=before,source_sha256_after=hashes(),
    log=str((run/'tests.log').relative_to(ROOT)),
    tolerances='Per-identity exact SymPy or explicit 1e-15..2e-10 assertions in test source; no frozen thresholds changed.',
    scope='Executable identities and independent counterexamples; 24D endpoint algebra is not full 3D robot/FSI/KAM validation.')
(run/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(BASE/'latest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(out.getvalue());print(json.dumps({k:report[k] for k in ('status','tests_run','wall_seconds','log')}))
raise SystemExit(0 if result.wasSuccessful() else 1)
