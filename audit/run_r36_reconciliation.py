import json,sys
from worldroot.r36_reconciliation import run
print(json.dumps(run(*sys.argv[1:4]),ensure_ascii=False))
