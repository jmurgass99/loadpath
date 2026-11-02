import assert from "node:assert/strict";
import type { FrameComponents, SemanticGeometry } from "../data-model.ts";
import { getMesh } from "../mesh/getMesh.ts";
import { initLsolverWasm, solveFrameWasm } from "../solver/wasmSolver.ts";

const geom: SemanticGeometry = {
  points: new Map([
    [1, [0, 0, 0]],
    [2, [8, 0, 0]],
    [3, [0, 0, 4.5]],
    [4, [8, 0, 4.5]],
  ]),
  lines: new Map([
    [1, [1, 3]],
    [2, [2, 4]],
    [3, [3, 4]],
  ]),
};

const comps: FrameComponents = {
  supports: new Map([
    [1, [true, true, true]],
    [2, [true, true, true]],
  ]),
  pointLoadsKN: new Map([[3, [30, 0, 0]]]),
  distributedLoadsKNm: new Map([[3, -20]]),
  endSpringsKNmRad: new Map([[3, [15000, 15000]]]),
  E_MPa: 210000,
  A_mm2: 5380,
  I_mm4: 8.356e7,
  divisions: 5,
};

// 1. Mesh mapping
const m = getMesh(geom, 5);
assert.equal(m.nodes.length, 4 + 3 * 4);
assert.equal(m.elements.length, 15);
assert.equal(m.geometryMapping.lineToElements.get(3)?.length, 5);

// 2. Monforton fixity factor in WASM
const w = await initLsolverWasm();
const g = w.monfortonFixityFactor(15e6, 210e9, 8.356e-5, 8.0);
assert.ok(g > 0.5 && g < 1.0);

// 3. Static solve
const mesh = getMesh(geom, 5);
const res = solveFrameWasm({ geometry: geom, mesh, components: comps });
assert.ok(res.maxDisplacementMm > 0.5);

console.log(
  `LoadPath WASM test OK: gamma_fixity=${g.toFixed(3)}, max_disp=${res.maxDisplacementMm.toFixed(2)} mm`
);
