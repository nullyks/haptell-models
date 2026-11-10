from pathlib import Path
import json,math,os,re,subprocess,sys,zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.slice_models import find_slicer

DEST=ROOT/'.local/v07_review/print_comparison'
DEST.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'output/rounded_cube_box'
SLICER=find_slicer()
NUMBER=re.compile(r'([XYZEIJ])([-+]?(?:\d+(?:\.\d*)?|\.\d+))')

def read_profile(path):
    values={}
    for line in path.read_text(encoding='utf-8').splitlines():
        if ' = ' in line and not line.startswith('#'):
            key,value=line.split(' = ',1); values[key]=value
    return values

def statistics(path,orientation,part):
    feature='Custom'; relative=False; pos={'X':0.,'Y':0.,'Z':0.,'E':0.}
    totals={}; metadata={}; outside_interface=0.; longest_bridge=0.
    for line in path.read_text(encoding='utf-8',errors='replace').splitlines():
        if line.startswith(';TYPE:'):feature=line[6:].strip()
        if line.startswith('; ') and ' = ' in line:
            key,value=line[2:].split(' = ',1)
            if key.startswith(('filament used','estimated printing time')):metadata[key]=value
        command=line.split(';',1)[0].strip()
        if command=='M83':relative=True
        elif command=='M82':relative=False
        if not command.startswith(('G0 ','G1 ','G2 ','G3 ','G92 ')):continue
        vals={key:float(value) for key,value in NUMBER.findall(command)}
        if command.startswith('G92 '):pos.update(vals);continue
        dx=vals.get('X',pos['X'])-pos['X'];dy=vals.get('Y',pos['Y'])-pos['Y']
        distance=math.hypot(dx,dy)
        midx=(pos['X']+vals.get('X',pos['X']))/2
        midy=(pos['Y']+vals.get('Y',pos['Y']))/2
        if command.startswith(('G2 ','G3 ')) and ('I' in vals or 'J' in vals):
            cx=pos['X']+vals.get('I',0.);cy=pos['Y']+vals.get('J',0.)
            radius=math.hypot(pos['X']-cx,pos['Y']-cy)
            start=math.atan2(pos['Y']-cy,pos['X']-cx)
            end=math.atan2(vals.get('Y',pos['Y'])-cy,vals.get('X',pos['X'])-cx)
            angle=(end-start)%(2*math.pi) if command.startswith('G3 ') else -((start-end)%(2*math.pi))
            if abs(angle)<1e-9:angle=2*math.pi
            distance=radius*abs(angle)
            midx=cx+radius*math.cos(start+angle/2);midy=cy+radius*math.sin(start+angle/2)
        extrusion=vals.get('E',0.) if relative else vals.get('E',pos['E'])-pos['E']
        if extrusion>0 and distance>1e-5:
            totals[feature]=totals.get(feature,0.)+extrusion
            if feature=='Bridge infill':longest_bridge=max(longest_bridge,distance)
            if feature=='Support material interface':
                x=midx-180
                y=midy-180
                z=vals.get('Z',pos['Z'])
                if orientation=='up':
                    outside=0.2<z<8 and max(abs(x),abs(y))>32
                else:
                    outside=z>(8.8 if part=='bottom' else 2) and max(abs(x),abs(y))>37.1
                if outside:outside_interface+=extrusion
        for axis in ('X','Y','Z'):
            if axis in vals:pos[axis]=vals[axis]
        if 'E' in vals:pos['E']=pos['E']+vals['E'] if relative else vals['E']
    mass=lambda length:round(length*math.pi*(1.75/2)**2*1.24/1000,3)
    return {'statistics':metadata,'feature_mass_g':{key:mass(value) for key,value in totals.items()},
            'support_mass_g':mass(sum(v for k,v in totals.items() if k.startswith('Support material'))),
            'visible_exterior_interface_filament_mm':round(outside_interface,3),
            'longest_bridge_segment_mm':round(longest_bridge,3)}

def main():
    cases=[('up_snug','up','snug',False),('up_organic','up','organic',False),
           ('down_snug','down','snug',False),('down_organic','down','organic',False),
           ('down_organic_bridges','down','organic',True),
           ('down_snug_bridges','down','snug',True),
           ('down_organic_sparse','down','organic',True),
           ('down_snug_sparse','down','snug',True)]
    if sys.argv[1:]:cases=[case for case in cases if case[0] in sys.argv[1:]]
    results=json.loads((DEST/'comparison.json').read_text()) if (DEST/'comparison.json').exists() else {}
    for part in ('bottom','lid'):
        for name,orientation,style,bridges in cases:
            stem=f'{part}_{name}'
            folder=DEST/stem;folder.mkdir(exist_ok=True)
            profile=read_profile(SOURCE/'prusa_xl_04_pla_bottom.ini')
            profile.update({'support_material_style':style,'support_material_buildplate_only':'1' if orientation=='down' else '0',
                'support_material_contact_distance':'0.25','support_material_bottom_contact_distance':'0.25',
                'support_material_interface_layers':'2','support_material_bottom_interface_layers':'2',
                'support_material_xy_spacing':'0.5','support_material_interface_spacing':'0.3',
                'support_material_spacing':'3','support_material_threshold':'40',
                'dont_support_bridges':'1' if bridges else '0','external_perimeter_speed':'30','bridge_speed':'25',
                'support_tree_branch_distance':'2','support_tree_tip_diameter':'0.8'})
            if name=='down_organic_sparse':
                profile.update({'support_tree_branch_distance':'4','support_tree_top_rate':'20%'})
            if name=='down_snug_sparse':
                profile['support_material_spacing']='5'
            ini=folder/'profile.ini';ini.write_text('\n'.join(f'{k} = {v}' for k,v in sorted(profile.items()))+'\n',encoding='utf-8')
            common=[str(SLICER),'--load',str(ini),'--center','180,180']
            if orientation=='down':common+=['--rotate-x','180']
            model=SOURCE/f'rounded_cube_{part}.stl'
            gcode=folder/'print.gcode'
            if not gcode.exists():
                done=subprocess.run(common+['--export-gcode','--output',str(gcode),str(model)],capture_output=True,text=True,errors='replace')
                (folder/'slice.log').write_text(done.stdout+done.stderr,encoding='utf-8')
                if done.returncode:raise RuntimeError(f'{stem}: {done.stderr}')
            project=folder/'print.3mf'
            if not project.exists():
                subprocess.run(common+['--export-3mf','--output',str(project),str(model)],capture_output=True,check=True)
            result=statistics(gcode,orientation,part)
            result.update({'part':part,'orientation':orientation,'style':style,'dont_support_bridges':bridges})
            results[stem]=result
            print(json.dumps({stem:result}),flush=True)
            (DEST/'comparison.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
