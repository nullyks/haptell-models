from pathlib import Path
import sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.check_pneumatic_print import extrusion_paths

source=ROOT/'output/pneumatic_cube'
mesh=trimesh.load_mesh(source/'pneumatic_cube_print.stl',process=False)
section=trimesh.intersections.mesh_plane(mesh,[1,0,0],[0,0,0])[:,:,[1,2]]
supports=[];interfaces=[]
for feature,points,_,_ in extrusion_paths(source/'pneumatic_cube_xl_pla.gcode'):
    # Startup purge extrusion may occur above 8 mm before the object begins.
    if (supports or interfaces) and points[0,2]>8:break
    if feature.startswith('Support material'):
        target=interfaces if feature.endswith('interface') else supports
        for a,b in zip(points[:-1],points[1:]):
            if min(a[0],b[0])<=.4 and max(a[0],b[0])>=-.4:
                target.append(np.array([a,b])[:,[1,2]])
fig,axes=plt.subplots(1,2,figsize=(12,7),layout='constrained')
for ax in axes:
    ax.add_collection(LineCollection(section,colors='#233d58',linewidths=1.4,label='Kuubiku lõige X=0'))
    ax.add_collection(LineCollection(supports,colors='#24986a',linewidths=.7,alpha=.35,label='Eemaldatav väline tugi'))
    ax.add_collection(LineCollection(interfaces,colors='#e88c21',linewidths=.9,alpha=.7,label='Toe kontaktkihid'))
    ax.axhline(0,color='#1f2937',linewidth=2,label='Prindialus')
    ax.set(xlabel='Y (mm)',ylabel='Kõrgus aluselt (mm)',aspect='equal')
    ax.grid(alpha=.15)
axes[0].set(xlim=(-59,59),ylim=(-2,111),title='Prindiasend · 45° serval')
axes[0].text(0,54,'Sisemisi tugesid\nei ole',ha='center',va='center',fontsize=14,color='#233d58',bbox=dict(facecolor='white',alpha=.9,edgecolor='none'))
axes[1].set(xlim=(-13,13),ylim=(-1,10),title='Alumise serva suurendus')
axes[1].legend(loc='upper center',bbox_to_anchor=(.5,-.2),frameon=False,fontsize=10)
fig.suptitle('Pneumaatika kuubik · tegelike tugiradade lõige X = 0 ±0,4 mm\nToed ainult väljas · kokku hinnanguliselt 1,27 g',fontsize=16)
fig.savefig(source/'pneumatic_cube_supports.png',dpi=160,bbox_inches='tight',facecolor='white')
