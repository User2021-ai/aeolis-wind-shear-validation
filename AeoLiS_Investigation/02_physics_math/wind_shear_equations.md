# Wind and surface-shear mathematics

## 1. Flat-bed conversion from wind speed to friction velocity

For reference wind speed `U(z)` at height `z`, AeoLiS uses the neutral logarithmic law

```math
u_* = \frac{\kappa U(z)}{\ln(z/z_0)},
```

where `kappa = 0.41` and `z0` is aerodynamic roughness length. Component-wise,

```math
u_{*,s}=\frac{\kappa U_s}{\ln(z/z_0)}, \qquad
u_{*,n}=\frac{\kappa U_n}{\ln(z/z_0)}.
```

Surface-stress magnitude and direction are then

```math
|\boldsymbol{\tau}_0| = \rho_a u_*^2, \qquad
\boldsymbol{\tau}_0=|\boldsymbol{\tau}_0|\frac{(u_{*,s},u_{*,n})}{u_*}.
```

Assumptions:

- horizontally homogeneous neutral surface layer;
- one measurement height and one roughness representation;
- no displacement height;
- no stability correction;
- no internal boundary-layer adjustment after roughness transitions.

These assumptions can dominate the error even before topographic perturbation is applied.

## 2. Roughness alternatives

The code supports constant and grain-size-dependent choices. A major configuration hazard is that `method_roughness = constant` interprets `k` directly as `z0`, whereas `constant_nikuradse` uses `z0 = k/30`. The same numeric `k` therefore changes the log-law roughness by a factor of 30 between these methods.

Because

```math
\frac{\partial \ln u_*}{\partial \ln z_0}
= \frac{1}{\ln(z/z_0)},
```

roughness uncertainty propagates nonlinearly into stress, with approximately twice the relative effect on `tau` because `tau` is proportional to `u_*^2`.

## 3. Linear topographic perturbation

On a wind-aligned computational grid, the bed `h(x,y)` is Fourier transformed to `h_hat(kx,ky)`. Define

```math
k=\sqrt{k_x^2+k_y^2}, \qquad
\sigma=\sqrt{i L' k_x z_0/l}, \qquad L'=L/4.
```

The code iterates approximations for inner-layer height `l` and middle-layer height `h_m`:

```math
l \leftarrow \frac{2\kappa^2 L'}{\ln(l/z_0)}, \qquad
h_m \leftarrow \frac{L'}{\sqrt{\ln(h_m/z_0)}},
```

and defines

```math
u_l=\frac{\ln(l/z_0)}{\ln(h_m/z_0)}.
```

For valid modes (`k != 0` and `kx != 0`), the implemented along-wind transfer is

```math
\widehat{\delta\tau_x}
= \hat h\,\frac{2 k_x^2}{k u_l^2}
\left[
-1+\left(2\ln\frac{l}{z_0}+\frac{k^2}{k_x^2}\right)
\sigma\frac{K_1(2\sigma)}{K_0(2\sigma)}
\right].
```

The implemented transverse transfer is

```math
\widehat{\delta\tau_y}
= \hat h\,\frac{2k_xk_y}{ku_l^2}
\left[2\sqrt{2}\,\sigma K_1(2\sqrt{2}\,\sigma)\right].
```

The absence of a `K0` denominator in the transverse expression was briefly changed and then deliberately reverted in repository history. Its correctness should be checked against the primary derivation before altering it.

The physical stress is constructed as

```math
\tau_x=|\tau_0|\left(e_{0x}+\delta\tau_x\right), \qquad
\tau_y=|\tau_0|\left(e_{0y}+\delta\tau_y\right),
```

where `e0` is the unit vector of the reference stress on the wind-aligned grid.

## 4. Separation-envelope model

The implementation identifies lee slopes steeper than `mu_b` (default 30°), constructs a cubic envelope from a detected brink, and estimates a separation length

```math
l_s=\operatorname{clip}\left[
\frac{3z_b}{2c}\left(1+\frac{a}{4}+\frac{a^2}{8}\right),
0.1,200
\right],
```

with `a=(dz/dx)/c` and `c=0.2` by default. Beneath the envelope, stress is multiplied by

```math
f_{sep}=\operatorname{clip}\left(1-\frac{h_{sep}}{s\,\tau_{sep}},0,1\right),
```

using `s=0.2` and `tau_sep=0.5`. Numerically this is `clip(1 - 10 h_sep, 0, 1)` when `h_sep` is in metres. Thus stress becomes zero once the envelope is 0.1 m above the bed, independent of dune height or boundary-layer scale. The dimensional basis of this relation should be clarified and tested.

## 5. Conditions under which linear theory is expected to work

Most defensible regime:

- low `H/L` and gentle maximum slope;
- smooth terrain with resolved wavelengths;
- attached, quasi-steady, neutral flow;
- weak roughness transitions;
- sufficient distance from open boundaries;
- topography dominated by scales consistent with configured `L`;
- uniform rectilinear cells after transformation.

Expected failure regime:

- sharp brinks, steep lee slopes, and separated wakes;
- dunes interacting at short spacing;
- strongly three-dimensional blowouts, horns, and saddles;
- oblique flow with strong cross-slope pressure gradients;
- non-neutral stratification or rapidly varying gusts;
- heterogeneous vegetation and spatially variable roughness;
- unresolved microtopography near the grid scale;
- truncated topography or strong mean beach slope at an FFT boundary.

## 6. Dimensionless variables for analysis

Use these to organize CFD and field cases:

```math
H/L,\quad \max|\nabla z|,\quad z_0/H,\quad \delta/H,\quad
Re_H=U_H H/\nu,\quad u_*/U_{ref},\quad \theta_{yaw},\quad
TI,\quad H/L_{MO}.
```

Here `delta` is boundary-layer thickness, `TI` is turbulence intensity, and `L_MO` is Monin–Obukhov length. The final term can be omitted only when neutral conditions are demonstrated, not assumed from convenience.

## 7. Error propagation to sediment transport

Many equilibrium transport relations scale roughly as a cubic excess velocity, for example

```math
q_{sat}\propto (u_*-u_{*t})^3.
```

For `u_* > u_*t`, local first-order error propagation gives

```math
\frac{\delta q_{sat}}{q_{sat}}
\approx \frac{3\,\delta u_*}{u_*-u_{*t}}.
```

Near threshold, a modest shear-velocity error can therefore create a very large relative transport error or switch transport on/off entirely. This is why validating only final bed change can conceal the wind-model error structure.

