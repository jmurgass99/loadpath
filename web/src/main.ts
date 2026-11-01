import van from "vanjs-core";
import type {
  DiscreteMesh,
  FrameComponents,
  SemanticGeometry,
} from "./data-model";
import { getMesh } from "./mesh/getMesh";
import { runHybridFrameAnalysis } from "./solver/apiClient";
import { initLsolverWasm } from "./solver/wasmSolver";
import { getDiagrams } from "./ui/getDiagrams";
import { getViewer3D } from "./viewer/getViewer3D";

const { div, h2, h3, input, label, option, select, span } = van.tags;

await initLsolverWasm();

const geometry = van.state<SemanticGeometry>({
  points: new Map([
    [1, [0, 0, 0]],
    [2, [8, 0, 0]],
    [3, [0, 0, 4.5]],
    [4, [8, 0, 4.5]],
  ]),
  lines: new Map([
    [1, [1, 3]], // Left column
    [2, [2, 4]], // Right column
    [3, [3, 4]], // Girder with rotational end springs
  ]),
});

const divisions = van.state(6);
const springStiffnessKNmRad = van.state(18000);
const distributedLoadKNm = van.state(-24);
const lateralLoadKN = van.state(35);
const deformationScale = van.state(40);
const solverMode = van.state<"wasm-local" | "fastapi-python">("wasm-local");

const components = van.state<FrameComponents>({
  supports: new Map([
    [1, [true, true, true]],
    [2, [true, true, true]],
  ]),
  pointLoadsKN: new Map([[3, [35, 0, 0]]]),
  distributedLoadsKNm: new Map([[3, -24]]),
  endSpringsKNmRad: new Map([[3, [18000, 18000]]]),
  E_MPa: 210000,
  A_mm2: 5380,
  I_mm4: 8.356e7,
  divisions: 6,
});

const mesh = van.state<DiscreteMesh>(getMesh(geometry.val, divisions.val));
const deformedPositions = van.state<number[]>([]);
const maxDispMm = van.state(0);
const lineMaxMomentKNm = van.state<Map<number, number>>(new Map());
const lineMaxShearKN = van.state<Map<number, number>>(new Map());
const connectionClass = van.state("semi_rigid");
const fixityFactorGamma = van.state(0.75);

van.derive(() => {
  const nDiv = divisions.val;
  const sj = springStiffnessKNmRad.val;
  const q = distributedLoadKNm.val;
  const fx = lateralLoadKN.val;

  components.val = {
    ...components.val,
    divisions: nDiv,
    pointLoadsKN: new Map([[3, [fx, 0, 0]]]),
    distributedLoadsKNm: new Map([[3, q]]),
    endSpringsKNmRad: new Map([[3, [sj, sj]]]),
  };
  mesh.val = getMesh(geometry.val, nDiv);
});

van.derive(() => {
  runHybridFrameAnalysis({
    mode: solverMode.val,
    apiUrl: "http://127.0.0.1:8000",
    geometry: geometry.val,
    mesh: mesh.val,
    components: components.val,
  }).then((res) => {
    deformedPositions.val = res.deformedPositions;
    maxDispMm.val = res.maxDisplacementMm;
    lineMaxMomentKNm.val = res.lineMaxMomentKNm;
    lineMaxShearKN.val = res.lineMaxShearKN;
    connectionClass.val = res.connectionClasses.get(3) ?? "semi_rigid";
    fixityFactorGamma.val = res.fixityFactorGamma;
  });
});

const leftPanel = div(
  { class: "lp-panel" },
  h2({ style: "font-size: 1.05rem;" }, "Loadpath — Pórtico Semirrígido 3D"),
  div(
    { class: "lp-card" },
    h3("Malla Semántica (GeometryMapping)"),
    div(
      { class: "lp-row" },
      label("Divisiones por barra:"),
      input({
        type: "number",
        min: "1",
        max: "12",
        value: () => String(divisions.val),
        oninput: (e: Event) =>
          (divisions.val = Math.max(1, Number((e.target as HTMLInputElement).value) || 1)),
      }),
    ),
    div(
      { class: "lp-row" },
      label("Nudos / Elementos:"),
      span(() => `${mesh.val.nodes.length} / ${mesh.val.elements.length}`),
    ),
  ),
  div(
    { class: "lp-card" },
    h3("Uniones Semirrígidas (EN 1993-1-8)"),
    div(
      { class: "lp-row" },
      label("Sj,ini [kN·m/rad]:"),
      input({
        type: "number",
        step: "2000",
        min: "100",
        value: () => String(springStiffnessKNmRad.val),
        oninput: (e: Event) =>
          (springStiffnessKNmRad.val = Math.max(100, Number((e.target as HTMLInputElement).value) || 1000)),
      }),
    ),
    div(
      { class: "lp-row" },
      label("Clase EC3:"),
      span({ class: "lp-badge" }, () => connectionClass.val.toUpperCase()),
    ),
    div(
      { class: "lp-row" },
      label("Carga q viga [kN/m]:"),
      input({
        type: "number",
        step: "2",
        value: () => String(distributedLoadKNm.val),
        oninput: (e: Event) =>
          (distributedLoadKNm.val = Number((e.target as HTMLInputElement).value) || 0),
      }),
    ),
    div(
      { class: "lp-row" },
      label("Carga H nudo 3 [kN]:"),
      input({
        type: "number",
        step: "5",
        value: () => String(lateralLoadKN.val),
        oninput: (e: Event) =>
          (lateralLoadKN.val = Number((e.target as HTMLInputElement).value) || 0),
      }),
    ),
  ),
  div(
    { class: "lp-card" },
    h3("Motor Híbrido (WASM / FastAPI)"),
    div(
      { class: "lp-row" },
      label("Solver:"),
      select(
        {
          onchange: (e: Event) =>
            (solverMode.val = (e.target as HTMLSelectElement).value as "wasm-local" | "fastapi-python"),
        },
        option({ value: "wasm-local" }, "WASM + Monforton-Wu"),
        option({ value: "fastapi-python" }, "FastAPI Python"),
      ),
    ),
    div(
      { class: "lp-row" },
      label("Desplazamiento máx:"),
      span(() => `${maxDispMm.val.toFixed(2)} mm`),
    ),
  ),
);

const rightPanel = div(
  { class: "lp-panel right" },
  getDiagrams({
    lineMaxMomentKNm,
    lineMaxShearKN,
    fixityFactorGamma,
  }),
);

document.body.appendChild(
  div(
    { class: "lp-layout" },
    leftPanel,
    getViewer3D({
      mesh,
      components,
      deformedPositions,
      lineMaxMomentKNm,
      deformationScale,
    }),
    rightPanel,
  ),
);
