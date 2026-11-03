"""Generate flat and sinusoidal periodic RANS cases for OpenCFD OpenFOAM v2312."""
import argparse
import math
from pathlib import Path


def write(case, name, body, cls="dictionary"):
    path = case / name
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"FoamFile {{ version 2.0; format ascii; class {cls}; object {path.name}; }}"
    path.write_text(header + "\n" + body + "\n", encoding="ascii")


def mesh(height, n):
    vertices, blocks, bed, lid, sides = [], [], [], [], []
    def face(indices):
        return "(" + " ".join(map(str, indices)) + ")"
    for i in range(n + 1):
        x = -16 + 32*i/n
        z = height*math.cos(2*math.pi*x/32)
        for y, level in [(0,z),(1,z),(0,32),(1,32)]:
            vertices.append(f"({x:.12g} {y} {level:.12g})")
    for i in range(n):
        a = 4*i
        v = [a,a+4,a+5,a+1,a+2,a+6,a+7,a+3]
        blocks.append(f"hex {face(v)} (1 1 {n//2}) simpleGrading (1 1 16)")
        for target, order in [(bed,[0,3,2,1]),(lid,[4,5,6,7]),(sides,[0,1,5,4]),(sides,[3,7,6,2])]:
            target.append(face([v[j] for j in order]))
    patches = []
    for name, kind, faces in [
        ("bed","wall",bed),("lid","symmetryPlane",lid),("sides","empty",sides),
        ("west","cyclic; neighbourPatch east",[face([0,2,3,1])]),
        ("east","cyclic; neighbourPatch west",[face([4*n+j for j in (0,1,3,2)])])]:
        patches.append(f"{name} {{ type {kind}; faces ({' '.join(faces)}); }}")
    return f"scale 1; vertices ({' '.join(vertices)}); blocks ({' '.join(blocks)}); boundary ({' '.join(patches)});"


def prepare(case, height, n):
    write(case,"system/blockMeshDict",mesh(height,n))
    write(case,"system/controlDict",'''application simpleFoam;
startFrom startTime; startTime 0; stopAt endTime; endTime 3000; deltaT 1;
writeControl timeStep; writeInterval 250; writePrecision 10;
libs ("libatmosphericModels.so");
functions { bedStress { type wallShearStress; libs (fieldFunctionObjects);
patches (bed); writeControl writeTime; } }''')
    write(case,"system/fvSchemes",'''ddtSchemes { default steadyState; }
gradSchemes { default Gauss linear; }
divSchemes { default none; div(phi,U) bounded Gauss linearUpwind grad(U);
div(phi,k) bounded Gauss upwind; div(phi,epsilon) bounded Gauss upwind;
div((nuEff*dev2(T(grad(U))))) Gauss linear; }
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; } snGradSchemes { default corrected; }
wallDist { method meshWave; }''')
    write(case,"system/fvSolution",'''solvers { p { solver GAMG; smoother GaussSeidel; tolerance 1e-9; relTol 0.01; }
"(U|k|epsilon)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-9; relTol 0.01; } }
SIMPLE { nNonOrthogonalCorrectors 1; pRefCell 0; pRefValue 0; }
relaxationFactors { fields { p 0.3; } equations { U 0.7; k 0.6; epsilon 0.6; } }''')
    write(case,"constant/transportProperties","transportModel Newtonian; nu [0 2 -1 0 0 0 0] 1.5e-5;")
    write(case,"constant/turbulenceProperties","simulationType RAS; RAS { RASModel kEpsilon; turbulence on; printCoeffs on; }")
    write(case,"constant/fvOptions","drive { type meanVelocityForce; selectionMode all; fields (U); Ubar (10 0 0); }")
    for field, dims, initial, wall in [
        ("U","0 1 -1","(10 0 0)","type noSlip;"),("p","0 2 -2","0","type zeroGradient;"),
        ("k","0 2 -2","0.3","type kqRWallFunction; value uniform 0.3;"),
        ("epsilon","0 2 -3","0.01","type epsilonWallFunction; value uniform 0.01;"),
        ("nut","0 2 -1","0.001","type atmNutkWallFunction; z0 uniform 0.001; value uniform 0;")]:
        write(case,"0/"+field,f"dimensions [{dims} 0 0 0 0]; internalField uniform {initial};\n"
              f"boundaryField {{ bed {{ {wall} }} lid {{ type symmetryPlane; }} sides {{ type empty; }} "
              "west { type cyclic; } east { type cyclic; } }","volVectorField" if field=="U" else "volScalarField")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    for n in (64,128,256):
        for label, height in [("flat",0),("steep",1.28)]:
            prepare(args.output/f"{label}-{n}",height,n)
