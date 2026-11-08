"""Continue horizontally homogeneous flat CFD profiles on two periodic columns."""
import argparse
import json
import re
import shutil
from pathlib import Path
import numpy as np
from prepare_ridge_cfd import prepare, mesh

def internal(path):
    text = path.read_text()
    match = re.search(r"internalField\s+nonuniform\s+List<(vector|scalar)>\s+(\d+)\s*\(\s*\n(.*?)\n\)",text,re.S)
    data = np.fromstring(match[3].replace("(","").replace(")",""),sep=" ")
    return data.reshape(int(match[2]), -1)

def generate(source, work):
    for n in (64,128,256):
        old = source/f"flat-{n}"
        case = work/f"flat-{n}"
        if case.exists():
            raise FileExistsError(case)
        prepare(case,0,n)
        path=case/"system/blockMeshDict"
        path.write_text(path.read_text().split("\n")[0]+"\n"+mesh(0,2).replace("(1 1 1)",f"(1 1 {n//2})"))
        for name in ("U","p","k","epsilon","nut"):
            data=internal(old/f"9000/{name}").reshape(n,n//2,-1)
            mean=data.mean(axis=0)
            print(n,name,"maximum horizontal departure",float(np.max(abs(data-mean))))
            values=np.tile(mean,(2,1))
            body="\n".join("("+ " ".join(map(str,v))+")" if name=="U" else str(v[0]) for v in values)
            path=case/f"0/{name}"
            text=path.read_text()
            text=re.sub(r"internalField uniform [^;]+;",f"internalField nonuniform List<{'vector' if name=='U' else 'scalar'}>\n{len(values)}\n(\n{body}\n);",text)
            path.write_text(text)
        shutil.copyfile(old/"constant/fvOptions",case/"constant/fvOptions")
        (case/"0/uniform").mkdir()
        shutil.copyfile(old/"9000/uniform/driveProperties",case/"0/uniform/driveProperties")
        control=case/"system/controlDict"
        control.write_text(control.read_text().replace("endTime 3000","endTime 30000").replace("writeInterval 250","writeInterval 1000"))
        (case/"mapping.json").write_text(json.dumps(dict(original_nx=n,reduced_nx=2,vertical_cells=n//2,initial_iteration=9000)))

def calibrate(work):
    from ridge_grid_study import u10
    for n in (64,128,256):
        case=work/f"flat-{n}"
        history=case/"calibration.json"
        if history.exists():
            raise FileExistsError(history)
        speed=u10(case,case/"30000/C",30000)
        forcing=case/"constant/fvOptions"
        text=forcing.read_text()
        old=float(re.search(r"Ubar \((\S+)",text)[1])
        target=old*10/speed
        forcing.write_text(re.sub(r"Ubar \(\S+",f"Ubar ({target:.12f}",text))
        control=case/"system/controlDict"
        control.write_text(control.read_text().replace("startFrom startTime","startFrom latestTime").replace("endTime 30000","endTime 40000"))
        history.write_text(json.dumps(dict(settled_u10=speed,old_bulk=old,new_bulk=target),indent=2))
        print(n,speed,target)

def expand(work, output):
    for n in (64,128,256):
        old=work/f"flat-{n}"
        case=output/f"flat-{n}"
        if case.exists():
            raise FileExistsError(case)
        prepare(case,0,n)
        for name in ("U","p","k","epsilon","nut"):
            mean=internal(old/f"40000/{name}").reshape(2,n//2,-1).mean(axis=0)
            values=np.tile(mean,(n,1))
            body="\n".join("("+" ".join(map(str,v))+")" if name=="U" else str(v[0]) for v in values)
            path=case/f"0/{name}"
            path.write_text(re.sub(r"internalField uniform [^;]+;",f"internalField nonuniform List<{'vector' if name=='U' else 'scalar'}>\n{len(values)}\n(\n{body}\n);",path.read_text()))
        shutil.copyfile(old/"constant/fvOptions",case/"constant/fvOptions")
        (case/"0/uniform").mkdir()
        shutil.copyfile(old/"40000/uniform/driveProperties",case/"0/uniform/driveProperties")
        control=case/"system/controlDict"
        control.write_text(control.read_text().replace("endTime 3000","endTime 1000").replace("writeInterval 250","writeInterval 1000"))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("work",type=Path)
    p.add_argument("--calibrate",action="store_true")
    p.add_argument("--expand",type=Path)
    args=p.parse_args()
    if args.expand:
        expand(args.work,args.expand)
    elif args.calibrate:
        calibrate(args.work)
    else:
        generate(args.source,args.work)
