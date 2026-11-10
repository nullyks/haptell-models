from pathlib import Path
import gzip
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/'.local/v07_review'
REV=ROOT/'models/rounded_cube_box/revisions/2026-11-10_185836_23d24978'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

# Verify preservation before adding review files. Never alter archived models.
before=json.loads((LOCAL/'before_sha256.json').read_text())
protected={name:sha for name,sha in before.items()
           if '\\revisions\\' in name or (name.startswith('output\\') and not name.startswith('output\\rounded_cube_box\\'))}
for name,sha in protected.items():
    assert digest(ROOT/name)==sha,name
manifest=json.loads((REV/'manifest.json').read_text())
assert manifest['generated_with_captured_source']
for name,sha in manifest['sha256'].items():
    assert digest(REV/name)==sha,name
    current=ROOT/('output/rounded_cube_box/'+Path(name).name if name.startswith('stl/') else Path(name).name)
    assert digest(current)==sha,('source/output correspondence',name)

review=REV/'review'
review.mkdir(exist_ok=False)
copy_log={}
def copy(source,target):
    assert not target.exists(),target
    target.parent.mkdir(parents=True,exist_ok=True)
    if source.suffix=='.gcode' and 'selected_prints' not in target.parts:
        target=target.with_suffix(target.suffix+'.gz')
        assert not target.exists()
        with source.open('rb') as src,target.open('xb') as out:
            with gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0) as gz:
                shutil.copyfileobj(src,gz)
        with gzip.open(target,'rb') as check:
            assert hashlib.sha256(check.read()).hexdigest()==digest(source)
    else:
        with source.open('rb') as src,target.open('xb') as out:
            shutil.copyfileobj(src,out)
        assert digest(target)==digest(source)
    copy_log[target.relative_to(review).as_posix()]={
        'source':source.relative_to(ROOT).as_posix(),'original_sha256':digest(source)}

source=ROOT/'output/rounded_cube_box'
for path in sorted(source.iterdir()):
    if path.suffix in ('.3mf','.gcode','.ini') or path.name=='prusa_slicer_validation.json':
        copy(path,review/'selected_prints'/path.name)
    elif path.name in ('rounded_cube_overview.png','rounded_cube_v07_closed.png','prusa_v07_supports.png','validation.json'):
        copy(path,review/path.name)
for path in sorted((LOCAL/'print_comparison').rglob('*')):
    if path.is_file():copy(path,review/'print_comparison'/path.relative_to(LOCAL/'print_comparison'))
for directory in ('final_prints','final_prints_dense_tips','final_prints_reliable','final_prints_corrected'):
    for path in sorted((LOCAL/directory).rglob('*')):
        if path.is_file():copy(path,review/'final_attempts'/directory/path.relative_to(LOCAL/directory))
for name in ('mesh_checks_final.json','before_sha256.json'):
    copy(LOCAL/name,review/'checks'/name)
for name in ('README.md','PRUSA_XL_PLA_JUHEND.md'):
    copy(ROOT/'models/rounded_cube_box'/name,review/name)
for name in ('tools/prepare_cube_prints.py','tools/slice_models.py','tools/verify_models.py',
             'tests/test_rounded_cube_v07.py','requirements-dev.txt','requirements-dev.lock.txt'):
    copy(ROOT/name,review/'source_helpers'/name)
for name in ('compare_v07_printing.py','compare_banded_supports.py','check_roof_bridges.py',
             'validate_final_prints.py','plot_v07_supports.py','archive_v07_review.py'):
    copy(ROOT/'.git'/name,review/'source_helpers/investigation'/name)

ledger={
    'scope':'All estimates and analytical screens; no physical print or measured snap force.',
    'comparison_cases':32,
    'comparison_warning':'Trials include rejected settings. Enforcers in early fan cases had assembly Y instead of rotated print Y; use only selected_prints for printing.',
    'final_attempts':{
        'final_prints':'Rejected bottom Organic: sampled free roof span 25.54 mm near thermal pad edge.',
        'final_prints_dense_tips':'Rejected bottom Organic: denser tips still left 25.54 mm span.',
        'final_prints_reliable':'Snug bottom roof passed, but fan screw-ear support was on wrong Y side; rejected.',
        'final_prints_corrected':'Selected: corrected fan support Y; bottom Snug / lid dense Organic. All final checks passed.'},
    'selected_source_revision':REV.name,
    'selected_checks':'selected_prints/prusa_slicer_validation.json',
    'tests':{'command':'.venv/Scripts/python.exe -m pytest -q','passed':11},
    'prior_protected_file_hashes_verified':len(protected),
    'source_and_all_current_STL_hashes_match_generated_archive':True,
    'investigation_helpers':'Raw scripts expect repository root and siblings in .git; preserved for inspection. Production entry point is tools/slice_models.py.',
}
(review/'trial_status.json').write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8',newline='\n')
(review/'copy_provenance.json').write_text(json.dumps(copy_log,indent=2)+'\n',encoding='utf-8',newline='\n')
checks={p.relative_to(review).as_posix():digest(p) for p in sorted(review.rglob('*')) if p.is_file()}
(review/'sha256.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'review_files':len(checks),'immutable_prior_files_verified':len(protected),
                  'review_size_mb':round(sum(p.stat().st_size for p in review.rglob('*') if p.is_file())/1e6,2)},indent=2))
