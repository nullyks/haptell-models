from pathlib import Path
import importlib.util
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('roof',ROOT/'.git/check_roof_bridges.py')
roof=importlib.util.module_from_spec(spec);spec.loader.exec_module(roof)
fig,axes=plt.subplots(1,2,figsize=(14,6.4),layout='constrained')
for ax,part,title in zip(axes,('bottom','lid'),('Põhi · Snug','Kaas · Organic')):
    mesh=trimesh.load_mesh(ROOT/f'output/rounded_cube_box/rounded_cube_{part}.stl')
    section=trimesh.intersections.mesh_plane(mesh,plane_normal=[0,1,0],plane_origin=[0,-8.8,0])
    lines=section[:,:,[0,2]]
    ax.add_collection(LineCollection(lines,colors='#293d56',linewidths=1.5,zorder=3,label='Mudeli lõige'))
    supports=[];interfaces=[]
    for feature,points,_ in roof.paths(ROOT/f'output/rounded_cube_box/rounded_cube_{part}_xl_pla.gcode'):
        if feature not in ('Support material','Support material interface'):continue
        target=interfaces if feature.endswith('interface') else supports
        target.append(points[:,[0,2]])
    ax.add_collection(LineCollection(supports,colors='#2b9c6d',linewidths=.4,alpha=.12,label='Eemaldatav tugi'))
    ax.add_collection(LineCollection(interfaces,colors='#ec9228',linewidths=.7,alpha=.3,label='Toe kontaktkihid'))
    ax.axhline(0,color='#111827',linewidth=2,label='Prindialus')
    ax.set(xlim=(-44,44),ylim=(-2,51),aspect='equal',title=title,xlabel='X (mm)',ylabel='Kõrgus prindialuselt (mm)')
    ax.grid(alpha=.15)
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.13),fontsize=9,ncol=1,frameon=False)
fig.suptitle('v07 · mõlemad avad all, ümar välispind üleval\nTugiradade eestvaade · mudeli lõige Y = −8,8 mm',fontsize=16)
fig.savefig(ROOT/'output/rounded_cube_box/prusa_v07_supports.png',dpi=170,facecolor='white',bbox_inches='tight')
