from pathlib import Path
import gzip
import hashlib
import json
import shutil

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
import trimesh

ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/'.local/pneumatic_review'
REV=ROOT/'models/pneumatic_cube/revisions/2026-11-10_194955_a4bccfb6'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()

before=json.loads((LOCAL/'before_sha256.json').read_text())
protected={p:v for p,v in before.items() if '/revisions/' in p or p.startswith('output/')}
for name,expected in protected.items():
    assert sha(ROOT/name)==expected,('Existing model changed',name)
manifest=json.loads((REV/'manifest.json').read_text())
assert manifest['generated_with_captured_source']
for name,expected in manifest['sha256'].items():
    assert sha(REV/name)==expected,name
    current=ROOT/('output/pneumatic_cube/'+Path(name).name if name.startswith('stl/') else Path(name).name)
    assert sha(current)==expected,('Current file differs from captured source/output',name)

serialized=[]
for path in sorted((REV/'stl').glob('*.stl')):
    raw=trimesh.load_mesh(path,process=False)
    vertices,inverse=np.unique(raw.vertices,axis=0,return_inverse=True)
    welded=trimesh.Trimesh(vertices=vertices,faces=inverse[raw.faces],process=False)
    edges=welded.edges_unique
    adjacency=coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(len(vertices),len(vertices)))
    count=connected_components(adjacency,directed=False,return_labels=False)
    assert count==1
    assert welded.euler_number==-32
    serialized.append({'file':path.name,'connected_components':int(count),'euler_characteristic':int(welded.euler_number),
                       'watertight':bool(welded.is_watertight),'volume_mm3':float(welded.volume),'sha256':sha(path)})

review=REV/'review'
review.mkdir(exist_ok=False)
provenance={}
def copy(source,target,compress=False):
    if compress and source.suffix=='.gcode':target=target.with_suffix('.gcode.gz')
    assert not target.exists(),target
    target.parent.mkdir(parents=True,exist_ok=True)
    with source.open('rb') as src,target.open('xb') as out:
        if compress and source.suffix=='.gcode':
            with gzip.GzipFile(filename='',fileobj=out,mode='wb',compresslevel=6,mtime=0) as gz:
                shutil.copyfileobj(src,gz)
        else:shutil.copyfileobj(src,out)
    if target.suffix=='.gz':
        with gzip.open(target,'rb') as check:assert hashlib.sha256(check.read()).hexdigest()==sha(source)
    else:assert sha(source)==sha(target)
    provenance[target.relative_to(review).as_posix()]={'source':source.relative_to(ROOT).as_posix(),'original_sha256':sha(source)}

for source in sorted((ROOT/'output/pneumatic_cube').iterdir()):
    if source.suffix!='.stl':copy(source,review/'selected_prints'/source.name)
for source in sorted((LOCAL/'comparison').rglob('*')):
    if source.is_file():copy(source,review/'comparison'/source.relative_to(LOCAL/'comparison'),True)
for source in sorted((LOCAL/'selected_final').rglob('*')):
    if source.is_file():copy(source,review/'final_build'/source.name,True)
for name in ('before_sha256.json','initial_mesh_checks.json','final_mesh_checks.json','comparison_summary.json'):
    copy(LOCAL/name,review/'checks'/name)
for name in ('README.md','PRUSA_XL_PLA_JUHEND.md'):
    copy(ROOT/'models/pneumatic_cube'/name,review/name)
for name in ('tools/prepare_pneumatic_print.py','tools/check_pneumatic_print.py','tools/verify_models.py',
             'tests/test_pneumatic_cube.py','pytest.ini','requirements-dev.txt','requirements-dev.lock.txt','.gitattributes'):
    copy(ROOT/name,review/'source_helpers'/name)
for name in ('compare_pneumatic_prints.py','plot_pneumatic_supports.py','archive_pneumatic_review.py'):
    copy(ROOT/'.git'/name,review/'source_helpers/investigation'/name)

status={
    'selected_revision':REV.name,'selected_orientation':'edge down, 45 degrees about X',
    'reference_adjustment_approved':'User approved aperture/layout adjustment while retaining 80 mm / R8. Reference 35 mm diameter and 35 mm pitch gives zero web.',
    'physical_test':'Not yet performed: printed finish, support removal, membrane fit, pressure and durability are unverified.',
    'selection':'Edge-down: longer initial bed contact and shorter/lower print than corner-down, at 0.78 g additional support.',
    'comparison_cases':6,'compared_orientations':['face','edge','corner'],'compared_supports':['automatic Organic','external-only Snug'],
    'rejected_face_external_reason':'Approximately 42.8 mm sampled unsupported roof bridge.',
    'rejected_automatic_support_reason':'Automatic Organic put support inside the cavity; bed-only does not prevent this.',
    'selected_support_mass_g':1.27,'selected_internal_support_samples':0,'selected_support_z_max_mm':5.8,
    'selected_max_sampled_free_bridge_mm':1.939,
    'serialized_mesh_checks':serialized,'automated_tests':{'command':'.venv/Scripts/python.exe -m pytest -q','passed':16},
    'immutable_prior_file_hashes_verified':len(protected),
    'current_source_and_output_match_manifest':True,
    'investigation_helpers':'Raw scripts assume repository root and .git placement; preserved as execution evidence. Current production tools are under tools/.',
}
(review/'trial_status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8',newline='\n')
(review/'copy_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8',newline='\n')
checks={p.relative_to(review).as_posix():sha(p) for p in sorted(review.rglob('*')) if p.is_file()}
(review/'sha256.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'review_files':len(checks),'prior_immutable_files_verified':len(protected),
                  'size_mb':round(sum(p.stat().st_size for p in review.rglob('*') if p.is_file())/1e6,2)},indent=2),flush=True)
