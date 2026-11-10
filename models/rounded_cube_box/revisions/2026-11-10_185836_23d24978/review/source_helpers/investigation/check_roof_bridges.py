from pathlib import Path
import importlib.util,json,math
import numpy as np
from scipy.spatial import cKDTree
import trimesh

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('comparison',ROOT/'.git/compare_v07_printing.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def paths(file):
    p=np.zeros(3);feature='';relative=True;e=0.
    for line in file.read_text().splitlines():
        if line.startswith(';TYPE:'):feature=line[6:].strip()
        command=line.split(';',1)[0].strip()
        if command=='M83':relative=True
        if command=='M82':relative=False
        if not command.startswith(('G0 ','G1 ','G2 ','G3 ','G92 ')):continue
        vals={k:float(v) for k,v in m.NUMBER.findall(command)}
        if command.startswith('G92 '):e=vals.get('E',e);continue
        q=np.array([vals.get(key,p[i]) for i,key in enumerate('XYZ')])
        de=vals.get('E',0.) if relative else vals.get('E',e)-e
        if 'E' in vals:e=e+vals['E'] if relative else vals['E']
        if de>0 and feature in ('Support material','Support material interface','Bridge infill') and (np.linalg.norm(q[:2]-p[:2])>1e-6 or command.startswith(('G2 ','G3 '))):
            length=float(np.linalg.norm(q[:2]-p[:2]));points=None
            if command.startswith(('G2 ','G3 ')) and ('I' in vals or 'J' in vals):
                center=p[:2]+[vals.get('I',0.),vals.get('J',0.)]
                radius=np.linalg.norm(p[:2]-center)
                a=math.atan2(p[1]-center[1],p[0]-center[0]);b=math.atan2(q[1]-center[1],q[0]-center[0])
                angle=(b-a)%(2*math.pi) if command.startswith('G3 ') else -((a-b)%(2*math.pi))
                if abs(angle)<1e-9:angle=2*math.pi
                length=radius*abs(angle)
                ts=np.linspace(0,1,max(2,int(math.ceil(length/.4))+1))
                points=np.column_stack((center[0]+radius*np.cos(a+ts*angle),center[1]+radius*np.sin(a+ts*angle),p[2]+ts*(q[2]-p[2])))
            if points is None:points=np.linspace(p,q,max(2,int(math.ceil(length/.4))+1))
            points[:,:2]-=180
            yield feature,points,length
        p=q

def inspect(part,style,gcode=None):
    height=46.8 if part=='bottom' else 40.
    name=f'{part}_down_grid_fan_{style}';support=[];bridges=[]
    for feature,points,length in paths(gcode or m.DEST/name/'print.gcode'):
        if feature=='Support material interface':support.append(points)
        elif feature=='Bridge infill' and height-3.5<=points[0,2]<=height-.8:bridges.append((points,length))
    support=np.concatenate(support)
    def previous_material(points):
        p=points.copy();p[:,2]-=.3
        if part=='bottom':p[:,2]=6.8-p[:,2]
        p=np.abs(p)
        q=p-32
        rounding=np.linalg.norm(np.maximum(q,0),axis=1)+np.minimum(np.max(q,axis=1),0)
        inside_outer=rounding<=8
        inside_inner=rounding<=4.8
        padq=p[:,:2]-18.5
        pad=(np.linalg.norm(np.maximum(padq,0),axis=1)+np.minimum(np.max(padq,axis=1),0))<=4
        inside_inner|=pad&(p[:,2]<=38.8)
        return inside_outer&~inside_inner
    maximum=0.;worst=None;cached={}
    for points,length in bridges:
        z=round(points[0,2],3)
        if z not in cached:
            nearby=support[(support[:,2]>=z-.85)&(support[:,2]<=z-.1)]
            cached[z]=cKDTree(nearby[:,:2]) if len(nearby) else None
        tree=cached[z]
        supported=previous_material(points)
        if tree is not None:supported |= tree.query(points[:,:2])[0]<=.6
        run=0;longest=0
        for yes in supported:
            run=0 if yes else run+1;longest=max(longest,run)
        span=min(length,longest*length/(len(points)-1))
        if span>maximum:maximum=span;worst={'z':z,'start':points[0].round(2).tolist(),'end':points[-1].round(2).tolist()}
    result={'job':name,'roof_bridge_paths':len(bridges),'max_sampled_free_roof_bridge_mm':round(maximum,2),
            'support_interface_z_max':float(support[:,2].max()),'sampling_step_mm':.4,
            'model_probe_below_nozzle_mm':.3,'support_anchor_tolerance_mm':.6,'worst_path':worst,
            'scope':'Sampled analytic rounded-shell/thermal-pad and interface-path estimate; ignores extra fan material conservatively. Not a physical print test.'}
    print(json.dumps(result),flush=True)
    return result

if __name__=='__main__':
    results=[inspect(part,style) for part in ('bottom','lid') for style in ('snug','organic')]
    (m.DEST/'roof_bridge_checks_grid.json').write_text(json.dumps(results,indent=2)+'\n')
