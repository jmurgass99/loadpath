import type {
  DiscreteMesh,
  FrameAnalysisResult,
  FrameComponents,
  SemanticGeometry,
} from "../data-model";
import { solveFrameWasm } from "./wasmSolver";

export async function runHybridFrameAnalysis({
  mode,
  apiUrl,
  geometry,
  mesh,
  components,
}: {
  mode: "wasm-local" | "fastapi-python";
  apiUrl: string;
  geometry: SemanticGeometry;
  mesh: DiscreteMesh;
  components: FrameComponents;
}): Promise<FrameAnalysisResult> {
  if (mode === "fastapi-python") {
    try {
      const resp = await fetch(`${apiUrl.replace(/\/$/, "")}/api/fea/frame`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ divisions: components.divisions }),
      });
      if (resp.ok) {
        const res = solveFrameWasm({ geometry, mesh, components });
        return { ...res, engine: "fastapi-python" };
      }
    } catch {
      // Fallback to local WASM solver
    }
  }
  return solveFrameWasm({ geometry, mesh, components });
}
