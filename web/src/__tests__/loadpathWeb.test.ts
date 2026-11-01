import { describe, expect, it } from "vitest";
import type { FrameComponents, SemanticGeometry } from "../data-model";
import { getMesh } from "../mesh/getMesh";
import { initLsolverWasm, solveFrameWasm } from "../solver/wasmSolver";

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

describe("Loadpath Web — GeometryMapping + lSolver.wasm", () => {
  it("maps semantic points and lines to subdivided finite elements", () => {
    const m = getMesh(geom, 5);
    expect(m.nodes.length).toBe(4 + 3 * 4);
    expect(m.elements.length).toBe(15);
    expect(m.geometryMapping.lineToElements.get(3)?.length).toBe(5);
  });

  it("evaluates Monforton-Wu fixity factor in WebAssembly and solves semi-rigid frame", async () => {
    const w = await initLsolverWasm();
    const g = w.monfortonFixityFactor(15e6, 210e9, 8.356e-5, 8.0);
    expect(g).toBeGreaterThan(0.5);
    expect(g).toBeLessThan(1.0);

    const mesh = getMesh(geom, 5);
    const res = solveFrameWasm({ geometry: geom, mesh, components: comps });
    expect(res.maxDisplacementMm).toBeGreaterThan(0.5);
    expect(res.connectionClasses.get(3)).toBe("semi_rigid");
  });
});
