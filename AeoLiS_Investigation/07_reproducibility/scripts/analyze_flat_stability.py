"""Measure flat-bed profile and wall-stress settling on the reduced grids."""
import argparse
import gzip
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from flat_reference_stability import internal
from ridge_grid_study import u10

def wall(case, time):
    text=(case/str(time)/"wallShearStress").read_text().split("    bed",1)[1]
    uniform=re.search(r"value\s+uniform\s+\(([^)]+)\)",text)
    if uniform:
        return np.array([float(uniform[1].split()[0])])
    block=text.split("}",1)[0]
    return np.array([float(v.split()[0]) for v in re.findall(r"\(([-+0-9.eE ]+)\)",block)])

p=argparse.ArgumentParser(description=__doc__)
p.add_argument("work",type=Path)
p.add_argument("equivalence",type=Path)
args=p.parse_args()
results=Path(__file__).resolve().parents[1]/"results"
records=[]
fig,axes=plt.subplots(1,3,figsize=(11,3.7),layout="constrained")
for n in (64,128,256):
 case=args.work/f"flat-{n}"
 coords=case/"30000/C"
 assert "Mesh OK." in (case/"log.check").read_text()
 assert "End" in (case/"log.calibrate").read_text()[-100:]
 series=[]
 previous=None
 for t in range(1000,40001,1000):
  speed=u10(case,coords,t)
  stress=float(abs(wall(case,t).mean()))
  profile=internal(case/f"{t}/U")[:,0]
  row=dict(iteration=t,u10_m_s=speed,kinematic_wall_stress=stress)
  if previous is not None:
   row["relative_wall_change"]=abs(stress-previous[0])/previous[0]
   row["max_velocity_profile_change_m_s"]=float(max(abs(profile-previous[1])))
  series.append(row)
  previous=stress,profile
 stable=all(s["relative_wall_change"]<.002 and s["max_velocity_profile_change_m_s"]<.01 for s in series[-2:])
 matched=abs(series[-1]["u10_m_s"]-10)<.05
 record=dict(original_nx=n,reduced_nx=2,vertical_cells=n//2,series=series,stable_last_two_windows=stable,reference_wind_within_half_percent=matched)
 record["calibration"]=json.loads((case/"calibration.json").read_text())
 records.append(record)
 np.savez(results/f"flat_reference_profile_{n}.npz",**{name:internal(case/f"40000/{name}") for name in ("U","p","k","epsilon","nut")},centres=internal(coords))
 archive=results/"flat_reference_logs"/case.name
 archive.mkdir(parents=True,exist_ok=True)
 for name in ("log.check","log.solve","log.calibrate"):
  (archive/(name+".gz")).write_bytes(gzip.compress((case/name).read_bytes(),mtime=0))
 axes[0].plot([s["iteration"]+9000 for s in series],[s["u10_m_s"] for s in series],label=f"{n//2} vertical cells")
 axes[1].semilogy([s["iteration"]+9000 for s in series[1:]],[max(s["relative_wall_change"],1e-15) for s in series[1:]])
 z=internal(coords)[:,2].reshape(2,n//2).mean(axis=0)
 velocity=internal(case/"40000/U")[:,0].reshape(2,n//2).mean(axis=0)
 axes[2].plot(velocity,z)
 print(n,"U10",series[-1]["u10_m_s"],"stable",stable,"matched",matched,"last two",series[-2:])
checks=[]
for n in (64,128,256):
 fullcase=args.equivalence/f"flat-{n}"
 assert "Mesh OK." in (fullcase/"log.check").read_text()
 assert "End" in (fullcase/"log.solve").read_text()[-100:]
 full=internal(fullcase/"1000/U").reshape(n,n//2,3).mean(axis=0)
 reduced=internal(args.work/f"flat-{n}/40000/U").reshape(2,n//2,3).mean(axis=0)
 difference=float(max(abs(full[:,0]-reduced[:,0])))
 stress_difference=float(abs(wall(fullcase,1000).mean()/wall(args.work/f"flat-{n}",40000).mean()-1))
 checks.append(dict(nx=n,max_ux_difference_m_s=difference,relative_wall_stress_difference=stress_difference))
 archive=results/"flat_reference_logs"/f"check-{n}"
 archive.mkdir(parents=True,exist_ok=True)
 for name in ("log.check","log.solve"):
  (archive/(name+".gz")).write_bytes(gzip.compress((fullcase/name).read_bytes(),mtime=0))
 print("Full-grid settled-profile check",checks[-1])
axes[0].axhline(10,color=".5",ls="--")
axes[0].set(xlabel="Cumulative iterations",ylabel="Wind speed at 10 m (m/s)")
axes[0].legend(fontsize=8)
axes[1].axhline(.002,color=".5",ls="--")
axes[1].set(xlabel="Cumulative iterations",ylabel="Relative wall-stress change / 1,000 iterations")
axes[2].set(xlabel="Final mean wind speed (m/s)",ylabel="Height (m)")
fig.savefig(results/"flat_reference_stability.png",dpi=200)
(results/"flat_reference_stability.json").write_text(json.dumps(dict(records=records,equilibrium_checks=checks),indent=2)+"\n")
