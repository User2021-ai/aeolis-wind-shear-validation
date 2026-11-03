"""Compare periodic ridge RANS stresses using paired flat-wall sign and scale."""
import re
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

work = Path(sys.argv[1])
results = Path(__file__).resolve().parents[1] / "results"
aeolis = np.genfromtxt(results/"ridge_pair_full.csv", delimiter=",", names=True)
aeolis = aeolis[aeolis["H_over_lambda"] == .04]
fig, ax = plt.subplots(layout="constrained")
for field, label in [("raw_normalized","AeoLiS raw"), ("full_normalized","AeoLiS full")]:
    ax.plot(aeolis["x_over_lambda"], aeolis[field], label=label)

def bed_centres(case):
    mesh = case/"constant/polyMesh"
    boundary = (mesh/"boundary").read_text()
    bed = re.search(r"\bbed\s*\{([^}]+)", boundary)[1]
    start = int(re.search(r"startFace\s+(\d+)", bed)[1])
    count = int(re.search(r"nFaces\s+(\d+)", bed)[1])
    points = np.array([float(v.split()[0]) for v in
                       re.findall(r"^\(([-+0-9.eE ]+)\)$", (mesh/"points").read_text(), re.M)])
    faces = re.findall(r"^4\(([0-9 ]+)\)$", (mesh/"faces").read_text(), re.M)
    return np.array([points[list(map(int, f.split()))].mean()
                     for f in faces[start:start+count]])

def values(case, time):
    text = (case/str(time)/"wallShearStress").read_text()
    block = re.search(r"\bbed\s*\{([^}]+)",text).group(1)
    uniform = re.search(r"value\s+uniform\s+\(([^)]+)\)",block)
    if uniform:
        return np.array([float(uniform[1].split()[0])])
    return np.array([float(v.split()[0]) for v in re.findall(r"\(([-+0-9.eE ]+)\)",block)])

rows = []
for n in (64,128,256):
    flat, steep = [work/f"{name}-{n}" for name in ("flat","steep")]
    if not all((p/"3000/wallShearStress").exists() for p in (flat,steep)):
        raise SystemExit(f"Missing final CFD output on grid {n}")
    x = bed_centres(steep)/32
    np.testing.assert_allclose(x, (np.arange(n)+.5)/n-.5, atol=1e-7)
    def profile(t):
        return values(steep,t)/values(flat,t).mean()
    for case in (flat, steep):
        if "Mesh OK." not in (case/"log.check").read_text():
            raise ValueError(f"Mesh check missing or failed in {case}")
    tau = profile(3000)
    assert tau.size == n and np.isfinite(tau).all()
    change = np.max(np.abs(tau-profile(2750)))
    print(n, "min/max",tau.min(),tau.max(),"peak x (m)",32*x[tau.argmax()],"negative cells",sum(tau<0),"last interval max change",change)
    rows.extend(zip(np.full(n,n),x,tau))
    ax.plot(x,tau,label=f"RANS {n} × {n//2}")
if not rows:
    raise SystemExit("No finished matched cases")
np.savetxt(results/"ridge_cfd_profiles.csv",rows,delimiter=",",header="nx,x_over_lambda,tau_x_over_flat",comments="")
ax.set(xlabel="Crest-relative distance / wavelength",ylabel="Signed streamwise stress / flat-bed stress", title="Periodic ridge, H/λ = 0.04")
ax.axhline(0,color=".6",lw=.8)
ax.legend()
fig.savefig(results/"ridge_cfd_comparison.png",dpi=200)
