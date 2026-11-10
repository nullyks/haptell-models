from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.prepare_pneumatic_print import prepare

def job(case):
    orientation,support=case
    return prepare(ROOT/f'.local/pneumatic_review/comparison/{orientation}_{support}',orientation,support)

if __name__=='__main__':
    cases=[(orientation,support) for orientation in ('face','edge','corner') for support in ('auto','external')]
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(job,cases))
