import type {
  Coord3D,
  DiscreteMesh,
  GeometryMapping,
  SemanticGeometry,
} from "../data-model";

export function getMesh(
  geometry: SemanticGeometry,
  divisions: number,
): DiscreteMesh {
  const nDiv = Math.max(1, Math.floor(divisions));
  const pointToNodes = new Map<number, number>();
  const lineToElements = new Map<number, number[]>();
  const nodes: Coord3D[] = [];
  const elements: [number, number][] = [];

  for (const ptId of [...geometry.points.keys()].sort((a, b) => a - b)) {
    const c = geometry.points.get(ptId)!;
    pointToNodes.set(ptId, nodes.length);
    nodes.push([c[0], c[1], c[2]]);
  }

  for (const lineId of [...geometry.lines.keys()].sort((a, b) => a - b)) {
    const [p1, p2] = geometry.lines.get(lineId)!;
    const n1 = pointToNodes.get(p1);
    const n2 = pointToNodes.get(p2);
    if (n1 === undefined || n2 === undefined) continue;

    const c1 = nodes[n1];
    const c2 = nodes[n2];
    const chain: number[] = [n1];

    for (let k = 1; k < nDiv; k++) {
      const t = k / nDiv;
      chain.push(nodes.length);
      nodes.push([
        c1[0] + t * (c2[0] - c1[0]),
        c1[1] + t * (c2[1] - c1[1]),
        c1[2] + t * (c2[2] - c1[2]),
      ]);
    }
    chain.push(n2);

    const elemIds: number[] = [];
    for (let k = 0; k < nDiv; k++) {
      elemIds.push(elements.length);
      elements.push([chain[k], chain[k + 1]]);
    }
    lineToElements.set(lineId, elemIds);
  }

  const geometryMapping: GeometryMapping = {
    pointToNodes,
    lineToElements,
  };
  return { nodes, elements, geometryMapping };
}
