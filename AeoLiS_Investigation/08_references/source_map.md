# Source and provenance map

## Audited repository sources

- AeoLiS repository supplied by the project: `https://github.com/openearth/aeolis-python`
- Audited commit: `https://github.com/openearth/aeolis-python/commit/1fcbe86d173f964e6ee231c0ee917ca3a6cd3f5e`
- Historical friction-component/frequency fix: `https://github.com/openearth/aeolis-python/commit/506064d5ed24c3cabe91beb987bad526555e34e2`
- New model-grid spectral method: `https://github.com/openearth/aeolis-python/commit/17a99aa`
- Model-grid separation: `https://github.com/openearth/aeolis-python/commit/8257fcf`
- Multiple spectral transfer choices: `https://github.com/openearth/aeolis-python/commit/e1379ab`
- Boundary taper experiment: `https://github.com/openearth/aeolis-python/commit/43837c5`

Branch statements are labelled “repository-reported” until their benchmarks are independently reproduced.

## Foundational references already named by the repository

- Weng, W. S., Hunt, J. C. R., Carruthers, D. J., Warren, A., and Wiggs, G. F. S. (1991), *Air flow and sand transport over sand-dunes*, Acta Mechanica, 2, 1–22.
- Kroy, K., Sauermann, G., and Herrmann, H. J. (2002), *Minimal model for sand dunes*, Physical Review Letters, 88(5), 054301. DOI `10.1103/PhysRevLett.88.054301`.
- Durán, O. and Moore, L. J. (2013), *Vegetation controls on the maximum size of coastal dunes*, PNAS, 110, 17217–17222. DOI `10.1073/pnas.1307580110`.
- Fourrière, A., Claudin, P., and Andreotti, B. (2010), transfer-function work referenced by the experimental spectral branch; full bibliographic details should be verified from the primary paper.

## Literature work still required

Before publishing equations or changing the transverse transfer, perform a primary-source search for:

1. exact Weng 1991 along/cross-wind transfer equations and definitions of `L`, `l`, and `h_m`;
2. low-hill theory validity and separation thresholds;
3. CFD/field studies of shear over coastal foredunes, barchans, parabolic dunes, and blowouts;
4. RANS/LES sensitivity for rough-wall atmospheric flow over dunes;
5. physics-informed/operator-learning surrogates for terrain flow and wall shear;
6. uncertainty standards for CFD validation and field-model comparison.

The exact public query proposed for a later approved web search is:

> `AeoLiS Weng 1991 surface shear stress coastal dunes CFD field validation flow separation recirculation physics-informed machine-learning surrogate`

No workspace files, private data, or conversation history need to be sent with that query.

