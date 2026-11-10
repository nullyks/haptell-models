from pathlib import Path
import hashlib,importlib.util,json,shutil,sys,xml.etree.ElementTree as ET,zipfile
import numpy as np
from scipy.spatial import cKDTree
import trimesh

ROOT=Path(__file__).resolve().parents[1]
def load(name,filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/'.git'/filename)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
m=load('comparison','compare_v07_printing.py'); bridge=load('roof_checks','check_roof_bridges.py')
base=ROOT/(sys.argv[1] if len(sys.argv)>1 else '.local/v07_review/final_prints'); report=json.loads((base/'prusa_slicer_validation.json').read_text())
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
checks=[]
for part in ('bottom','lid'):
    gcode=base/f'rounded_cube_{part}_xl_pla.gcode'
    row=m.statistics(gcode,'down',part)
    assert abs(sum(row['feature_mass_g'].values())-float(row['statistics']['filament used [g]']))<.2
    assert row['visible_exterior_interface_filament_mm']==0
    roof=bridge.inspect(part,report['parts'][part]['support_style'],gcode)
    assert roof['max_sampled_free_roof_bridge_mm']<18,roof
    check={'part':part,'roof_bridge_check':roof}
    source=trimesh.load_mesh(ROOT/f'output/rounded_cube_box/rounded_cube_{part}.stl',process=False)
    with zipfile.ZipFile(base/f'rounded_cube_{part}_xl_pla.3mf') as z:
        model=ET.fromstring(z.read('3D/3dmodel.model'))
        config=ET.fromstring(z.read('Metadata/Slic3r_PE_model.config'))
        vertices=np.array([[float(v.get(k)) for k in ('x','y','z')] for v in model.findall('m:resources/m:object/m:mesh/m:vertices/m:vertex',ns)])
        first=config.find('object/volume'); count=int(first.get('lastid'))+1
        faces=model.findall('m:resources/m:object/m:mesh/m:triangles/m:triangle',ns)[:count]
        indices=np.unique([[int(f.get(k)) for k in ('v1','v2','v3')] for f in faces])
        placement=[float(v) for v in model.find('m:build/m:item',ns).get('transform').split()]
        main=vertices[indices]+[placement[-3]-180,placement[-2]-180,placement[-1]]
        maximum=max(cKDTree(source.vertices).query(main)[0].max(),cKDTree(main).query(source.vertices)[0].max())
        assert maximum<.0001,(part,maximum)
        assert len(faces)==len(source.faces)
        check['project_mesh_max_vertex_error_mm']=float(maximum)
        check['one_printable_model_volume']=sum(v.find("metadata[@key='volume_type']").get('value')=='ModelPart' for v in config.findall('object/volume'))==1
        assert check['one_printable_model_volume']
    points=[p for feature,p,_ in bridge.paths(gcode) if feature=='Support material interface']
    points=np.concatenate(points)
    if part=='bottom':
        contacts={}
        for sign in (-1,1):
            for name,size,center in (
                ('cheek',(3.4,16),(sign*26.95,-.7,9.8)),
                ('screw_ear',(10.6,4.6),(sign*20,-8.8,21.6)),
                ('seat',(6.2,16),(sign*23,-.7,31.8))):
                mask=(np.abs(points[:,0]-center[0])<=size[0]/2+.3)&(np.abs(points[:,1]-center[1])<=size[1]/2+.3)&(points[:,2]>center[2]-1)&(points[:,2]<center[2]+.1)
                contacts[f'{name}_{sign:+}']=int(mask.sum());assert mask.any(),(name,sign)
        check['fan_first_overhang_interface_samples']=contacts
    report['parts'][part].update(row)
    checks.append(check)
baseline=json.loads((m.DEST/'comparison.json').read_text())
normal=sum(baseline[f'{part}_down_snug']['support_mass_g'] for part in ('bottom','lid'))
selected=sum(report['parts'][part]['support_mass_g'] for part in ('bottom','lid'))
report.update({'comparison_jobs':len(baseline),'selected_support_mass_g':round(selected,3),
               'automatic_snug_same_orientation_support_mass_g':normal,
               'support_reduction_vs_automatic_snug_percent':round(100*(1-selected/normal),1),
               'toolpath_checks':checks,'scope':'Nominal geometry and sliced toolpaths only; physical print, snap force, fan fit and thermal performance need testing.'})
(base/'prusa_slicer_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'selected_support_mass_g':report['selected_support_mass_g'],'support_reduction_percent':report['support_reduction_vs_automatic_snug_percent'],'all_final_checks':'passed'},indent=2))
