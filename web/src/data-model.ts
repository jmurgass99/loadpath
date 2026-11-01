export type Coord3D = [number, number, number];
export type LineSegment = [number, number];
export type SupportFlags = [boolean, boolean, boolean]; // [ux, uz, ry]

export interface SemanticGeometry {
  points: Map<number, Coord3D>;
  lines: Map<number, LineSegment>;
}

export interface FrameComponents {
  supports: Map<number, SupportFlags>;
  pointLoadsKN: Map<number, [number, number, number]>;
  distributedLoadsKNm: Map<number, number>;
  endSpringsKNmRad: Map<number, [number, number]>;
  E_MPa: number;
  A_mm2: number;
  I_mm4: number;
  divisions: number;
}

export interface GeometryMapping {
  pointToNodes: Map<number, number>;
  lineToElements: Map<number, number[]>;
}

export interface DiscreteMesh {
  nodes: Coord3D[];
  elements: [number, number][];
  geometryMapping: GeometryMapping;
}

export interface FrameAnalysisResult {
  engine: "wasm-local" | "fastapi-python";
  deformedPositions: number[];
  maxDisplacementMm: number;
  lineMaxMomentKNm: Map<number, number>;
  lineMaxShearKN: Map<number, number>;
  connectionClasses: Map<number, string>;
  fixityFactorGamma: number;
}
