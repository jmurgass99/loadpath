import type {
  DiscreteMesh,
  FrameAnalysisResult,
  FrameComponents,
  SemanticGeometry,
} from "../data-model";

const LSOLVER_WASM_BASE64 =
  "AGFzbQEAAAABEAJgBHx8fHwBfGADfHx8AXwDAwIAAQcxAhVtb25mb3J0b25GaXhpdHlGYWN0b3IAABViZWFtRmxleHVyYWxTdGlmZm5lc3MAAQpIAisARAAAAAAAAPA/RAAAAAAAAPA/RAAAAAAAAAhAIAGiIAKiIAAgA6KjoKMLGgBEAAAAAAAAKEAgAKIgAaIgAiACoiACoqML";

export interface LsolverWasmExports {
  monfortonFixityFactor: (Sj: number, E: number, I: number, L: number) => number;
  beamFlexuralStiffness: (E: number, I: number, L: number) => number;
}

let cachedExports: LsolverWasmExports | null = null;

function decodeBase64(b64: string): Uint8Array {
  if (typeof Buffer !== "undefined") {
    return new Uint8Array(Buffer.from(b64, "base64"));
  }
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

export async function initLsolverWasm(): Promise<LsolverWasmExports> {
  if (cachedExports) return cachedExports;
  const bytes = decodeBase64(LSOLVER_WASM_BASE64);
  const { instance } = await WebAssembly.instantiate(bytes.buffer as ArrayBuffer);
  cachedExports = instance.exports as unknown as LsolverWasmExports;
  return cachedExports;
}

export function getLsolverWasmSync(): LsolverWasmExports {
  if (cachedExports) return cachedExports;
  const bytes = decodeBase64(LSOLVER_WASM_BASE64);
  const mod = new WebAssembly.Module(bytes.buffer as ArrayBuffer);
  const instance = new WebAssembly.Instance(mod);
  cachedExports = instance.exports as unknown as LsolverWasmExports;
  return cachedExports;
}

export function classifyConnectionEC3(
  Sj_Nmm_rad: number,
  E_MPa: number,
  I_mm4: number,
  L_mm: number,
): string {
  const eiL = (E_MPa * I_mm4) / Math.max(L_mm, 1.0);
  if (Sj_Nmm_rad < 0.5 * eiL) return "pinned";
  if (Sj_Nmm_rad >= 8.0 * eiL) return "rigid";
  return "semi_rigid";
}

function solveGaussian(A: number[][], b: number[]): number[] {
  const n = b.length;
  const M = A.map((row, i) => [...row, b[i]]);
  for (let col = 0; col < n; col++) {
    let pivot = col;
    for (let row = col + 1; row < n; row++) {
      if (Math.abs(M[row][col]) > Math.abs(M[pivot][col])) pivot = row;
    }
    if (pivot !== col) {
      const tmp = M[col];
      M[col] = M[pivot];
      M[pivot] = tmp;
    }
    const diag = M[col][col];
    if (Math.abs(diag) < 1e-14) continue;
    for (let row = col + 1; row < n; row++) {
      const f = M[row][col] / diag;
      for (let j = col; j <= n; j++) M[row][j] -= f * M[col][j];
    }
  }
  const x = new Array<number>(n).fill(0);
  for (let i = n - 1; i >= 0; i--) {
    let s = M[i][n];
    for (let j = i + 1; j < n; j++) s -= M[i][j] * x[j];
    x[i] = Math.abs(M[i][i]) > 1e-14 ? s / M[i][i] : 0;
  }
  return x;
}

export function solveFrameWasm({
  geometry,
  mesh,
  components,
}: {
  geometry: SemanticGeometry;
  mesh: DiscreteMesh;
  components: FrameComponents;
}): FrameAnalysisResult {
  const wasm = getLsolverWasmSync();
  const { nodes, elements, geometryMapping } = mesh;
  const nNodes = nodes.length;
  const nDof = 3 * nNodes;

  const E = components.E_MPa * 1e6; // Pa
  const A = components.A_mm2 * 1e-6; // m^2
  const I = components.I_mm4 * 1e-12; // m^4

  const K: number[][] = Array.from({ length: nDof }, () =>
    new Array<number>(nDof).fill(0),
  );
  const F = new Array<number>(nDof).fill(0);

  for (const [ptId, [fx, fz, my]] of components.pointLoadsKN.entries()) {
    const ni = geometryMapping.pointToNodes.get(ptId);
    if (ni !== undefined) {
      F[3 * ni] += fx * 1e3;
      F[3 * ni + 1] += fz * 1e3;
      F[3 * ni + 2] += my * 1e3;
    }
  }

  const connectionClasses = new Map<number, string>();
  let sampleGamma = 1.0;

  interface ElemRecord {
    lineId: number;
    dofs: number[];
    kLoc: number[][];
    T: number[][];
    fEq: number[];
  }
  const records: ElemRecord[] = [];

  for (const [lineId, elemIndices] of geometryMapping.lineToElements.entries()) {
    const [p1, p2] = geometry.lines.get(lineId)!;
    const cStart = nodes[geometryMapping.pointToNodes.get(p1)!];
    const cEnd = nodes[geometryMapping.pointToNodes.get(p2)!];
    const L_line = Math.hypot(cEnd[0] - cStart[0], cEnd[2] - cStart[2]) || 1.0;

    const [sjkNmI, sjkNmJ] = components.endSpringsKNmRad.get(lineId) ?? [1e9, 1e9];
    const sjI_Nm = sjkNmI * 1e3;
    const sjJ_Nm = sjkNmJ * 1e3;

    connectionClasses.set(
      lineId,
      classifyConnectionEC3(
        Math.min(sjkNmI, sjkNmJ) * 1e6,
        components.E_MPa,
        components.I_mm4,
        L_line * 1e3,
      ),
    );
    if (sjkNmI < 1e8) {
      sampleGamma = wasm.monfortonFixityFactor(sjI_Nm, E, I, L_line);
    }

    const q_Nm = (components.distributedLoadsKNm.get(lineId) ?? 0) * 1e3;
    const nEl = elemIndices.length;

    elemIndices.forEach((eIdx, posIdx) => {
      const [na, nb] = elements[eIdx];
      const ca = nodes[na];
      const cb = nodes[nb];
      const dx = cb[0] - ca[0];
      const dz = cb[2] - ca[2];
      const L = Math.hypot(dx, dz) || 1.0;
      const c = dx / L;
      const s = dz / L;

      const gI = posIdx === 0 ? wasm.monfortonFixityFactor(sjI_Nm, E, I, L) : 1.0;
      const gJ = posIdx === nEl - 1 ? wasm.monfortonFixityFactor(sjJ_Nm, E, I, L) : 1.0;
      const denom = Math.max(4 - gI * gJ, 1e-9);

      const alphaII = (3 * gI * (2 - gJ)) / denom;
      const alphaJJ = (3 * gJ * (2 - gI)) / denom;
      const alphaIJ = (3 * gI * gJ) / denom;

      const eiL = (E * I) / L;
      const k22 = 4 * eiL * alphaII;
      const k25 = 2 * eiL * alphaIJ;
      const k55 = 4 * eiL * alphaJJ;
      const k12 = (k22 + k25) / L;
      const k15 = (k25 + k55) / L;
      const k11 = (k12 + k15) / L;
      const eaL = (E * A) / L;

      const kLoc = [
        [eaL, 0, 0, -eaL, 0, 0],
        [0, k11, k12, 0, -k11, k15],
        [0, k12, k22, 0, -k12, k25],
        [-eaL, 0, 0, eaL, 0, 0],
        [0, -k11, -k12, 0, k11, -k15],
        [0, k15, k25, 0, -k15, k55],
      ];

      const T = [
        [c, s, 0, 0, 0, 0],
        [-s, c, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 0, c, s, 0],
        [0, 0, 0, -s, c, 0],
        [0, 0, 0, 0, 0, 1],
      ];

      const dofs = [3 * na, 3 * na + 1, 3 * na + 2, 3 * nb, 3 * nb + 1, 3 * nb + 2];
      for (let i = 0; i < 6; i++) {
        for (let j = 0; j < 6; j++) {
          let sum = 0;
          for (let p = 0; p < 6; p++) {
            for (let q = 0; q < 6; q++) {
              sum += T[p][i] * kLoc[p][q] * T[q][j];
            }
          }
          K[dofs[i]][dofs[j]] += sum;
        }
      }

      const fEq = [
        0,
        0.5 * q_Nm * L,
        (q_Nm * L * L) / 12.0,
        0,
        0.5 * q_Nm * L,
        -(q_Nm * L * L) / 12.0,
      ];
      for (let i = 0; i < 6; i++) {
        for (let p = 0; p < 6; p++) {
          F[dofs[i]] += T[p][i] * fEq[p];
        }
      }

      records.push({ lineId, dofs, kLoc, T, fEq });
    });
  }

  const fixed = new Set<number>();
  for (const [ptId, flags] of components.supports.entries()) {
    const ni = geometryMapping.pointToNodes.get(ptId);
    if (ni !== undefined) {
      if (flags[0]) fixed.add(3 * ni);
      if (flags[1]) fixed.add(3 * ni + 1);
      if (flags[2]) fixed.add(3 * ni + 2);
    }
  }

  const free: number[] = [];
  for (let i = 0; i < nDof; i++) {
    if (!fixed.has(i)) free.push(i);
  }

  const K_ff = free.map((gi) => free.map((gj) => K[gi][gj]));
  const F_f = free.map((gi) => F[gi]);
  const u_f = solveGaussian(K_ff, F_f);

  const u = new Array<number>(nDof).fill(0);
  free.forEach((gi, idx) => (u[gi] = u_f[idx]));

  const deformedPositions: number[] = [];
  let maxDispM = 0;
  for (let i = 0; i < nNodes; i++) {
    const ux = u[3 * i];
    const uz = u[3 * i + 1];
    maxDispM = Math.max(maxDispM, Math.hypot(ux, uz));
    deformedPositions.push(nodes[i][0] + ux, nodes[i][1], nodes[i][2] + uz);
  }

  const lineMaxMomentKNm = new Map<number, number>();
  const lineMaxShearKN = new Map<number, number>();

  for (const rec of records) {
    const uLoc = new Array<number>(6).fill(0);
    for (let i = 0; i < 6; i++) {
      for (let j = 0; j < 6; j++) {
        uLoc[i] += rec.T[i][j] * u[rec.dofs[j]];
      }
    }
    const fInt = new Array<number>(6).fill(0);
    for (let i = 0; i < 6; i++) {
      let s = -rec.fEq[i];
      for (let j = 0; j < 6; j++) s += rec.kLoc[i][j] * uLoc[j];
      fInt[i] = s;
    }
    const vMax = Math.max(Math.abs(fInt[1]), Math.abs(fInt[4])) / 1e3;
    const mMax = Math.max(Math.abs(fInt[2]), Math.abs(fInt[5])) / 1e3;
    lineMaxShearKN.set(rec.lineId, Math.max(lineMaxShearKN.get(rec.lineId) ?? 0, vMax));
    lineMaxMomentKNm.set(
      rec.lineId,
      Math.max(lineMaxMomentKNm.get(rec.lineId) ?? 0, mMax),
    );
  }

  return {
    engine: "wasm-local",
    deformedPositions,
    maxDisplacementMm: Number((maxDispM * 1e3).toFixed(3)),
    lineMaxMomentKNm,
    lineMaxShearKN,
    connectionClasses,
    fixityFactorGamma: Number(sampleGamma.toFixed(4)),
  };
}
