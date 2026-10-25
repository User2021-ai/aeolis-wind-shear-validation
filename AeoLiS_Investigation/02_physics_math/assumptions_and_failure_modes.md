# Assumptions and likely failure modes

| Assumption | Encoded behaviour | Likely consequence when violated | Validation axis |
|---|---|---|---|
| Neutral log law | One `z`, `z0`, no stability correction | Biased baseline `u_*` before terrain effects | stability and profile measurements |
| Low/smooth hill linearization | FFT superposition of independent modes | Under/overprediction for steep nonlinear terrain | `H/L`, slope, curvature |
| One `L` for all modes | Same boundary-layer scale for every wavelength | Scale-dependent amplitude/phase bias | multi-frequency bed |
| Quasi-steady response | Instantaneous adjustment to input wind | No hysteresis or gust response | reduced frequency `fL/U` |
| Rotated interpolation grid | Bed and stress copied twice | Smoothing, phase shift, directional artefacts | yaw and resolution |
| Circular FFT continuation | Opposite edges connect | False cliff/ringing for nonperiodic beach profiles | padding/domain sweep |
| Empirical separation envelope | Stress attenuation, no resolved wake | No reversed shear, weak wake recovery physics | brink/reattachment cases |
| Fixed slope threshold | Separation begins at `mu_b=30°` | Missed pressure-gradient separation on gentler curved slopes | slope/curvature sweep |
| Uniform crosswind theory | `kx=0` modes have zero response | Missed secondary flows from transverse terrain | oblique 3-D dunes |
| Roughness equilibrium | Local log-law use of `z0` | No internal boundary layer across roughness patches | roughness-step cases |
| Grid-independent parameters | Several indices and bounds use cell counts | results change with `dx`, `dy` | mesh refinement |
| Nonnegative along-wind stress | negative `tau_x` clipped to zero | recirculation cannot be represented | separated CFD cases |

The correct research outcome may be a regime map, not a single global error number. AeoLiS can be useful within a bounded domain of validity even if it is unsuitable in separated three-dimensional flow.

