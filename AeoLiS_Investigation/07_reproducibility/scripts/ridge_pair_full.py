"""Compare central ridge profiles after one AeoLiS update with the periodic FFT."""
from pathlib import Path
import os
import numpy as np
from canonical_sinusoid_benchmark import run_case, plt
from aeolis.model import AeoLiS

root = Path(__file__).resolve().parents[1]
work = Path("tmp/ridge-pair").resolve()
work.mkdir(parents=True, exist_ok=True)
os.chdir(work)
x, y = np.meshgrid(np.arange(257.) / 2, np.arange(33.) / 2)
for name, data in [("x", x), ("y", y), ("wind", [[0, 10, 270], [10, 10, 270]])]:
    np.savetxt(work / (name + ".txt"), data)

def profile(height):
    np.savetxt(work / "bed.txt", 2 + height * np.cos(2*np.pi*x/32))
    options = dict(dx=.5, dy=.5, dt=.1, tstop=1, output_times=.1, k=.001,
                   method_roughness="constant", process_shear="T", method_shear="fft",
                   process_separation="F", visualization="F", L=100)
    for key, name in [("xgrid_file","x"), ("ygrid_file","y"), ("wind_file","wind"), ("bed_file","bed")]:
        options[key] = name + ".txt"
    config = work / "aeolis.txt"
    config.write_text("\n".join(f"{k} = {v}" for k,v in options.items())+"\n")
    model = AeoLiS(str(config))
    model.initialize()
    model.update(.1)
    return model.s["taus"][16,96:161].copy()

flat = profile(0)
assert np.all(flat > 0), "Check wind orientation"
phase = (x[16,96:161]-64)/32
fig, axes = plt.subplots(1,2,sharey=True,figsize=(9,4),layout="constrained")
rows = []
for ratio, ax in zip((.02,.04),axes):
    full = profile(32*ratio)/flat
    _, (_,_,delta) = run_case(ratio,32,64,.001,100)
    raw = 1+delta[96:161]
    rows.extend(zip(np.full(65,ratio),phase,raw,full))
    print(ratio, full.min(), full.max(), 32*phase[np.argmax(full)])
    ax.plot(phase,raw,label="Periodic raw FFT")
    ax.plot(phase,full,"--",label="Full model")
    ax.axhline(0,color="0.6",lw=.7)
    ax.set(xlabel="Crest-relative distance / wavelength",title=f"H/λ = {ratio}")
axes[0].set_ylabel("Signed along-wind stress / flat-bed stress")
axes[0].legend()
fig.savefig(root/"results/ridge_pair_full.png",dpi=200)
np.savetxt(root/"results/ridge_pair_full.csv",rows,delimiter=",",header="H_over_lambda,x_over_lambda,raw_normalized,full_normalized",comments="")
