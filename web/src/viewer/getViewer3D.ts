import * as THREE from "three";
import van, { type State } from "vanjs-core";
import type { DiscreteMesh, FrameComponents } from "../data-model";

export function getViewer3D({
  mesh,
  components,
  deformedPositions,
  lineMaxMomentKNm,
  deformationScale,
}: {
  mesh: State<DiscreteMesh>;
  components: State<FrameComponents>;
  deformedPositions: State<number[]>;
  lineMaxMomentKNm: State<Map<number, number>>;
  deformationScale: State<number>;
}): HTMLElement {
  const container = document.createElement("div");
  container.className = "lp-viewer";

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 300);
  camera.position.set(4, -14, 4);
  camera.up.set(0, 0, 1);
  camera.lookAt(4, 0, 2.5);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  container.appendChild(renderer.domElement);

  const grid = new THREE.GridHelper(16, 16, 0x334155, 0x1e293b);
  grid.rotation.x = Math.PI / 2;
  grid.position.set(4, 0, 0);
  scene.add(grid);

  const group = new THREE.Group();
  scene.add(group);

  van.derive(() => {
    while (group.children.length > 0) group.remove(group.children[0]);
    const m = mesh.val;
    const pos = deformedPositions.val;
    const scale = deformationScale.val;
    const mMap = lineMaxMomentKNm.val;
    const comps = components.val;

    if (!m.nodes.length) return;

    const defCoords = m.nodes.map((orig, i) => {
      if (pos.length >= (i + 1) * 3) {
        return new THREE.Vector3(
          orig[0] + (pos[3 * i] - orig[0]) * scale,
          orig[1] + (pos[3 * i + 1] - orig[1]) * scale,
          orig[2] + (pos[3 * i + 2] - orig[2]) * scale,
        );
      }
      return new THREE.Vector3(orig[0], orig[1], orig[2]);
    });

    const maxM = Math.max(...mMap.values(), 1);
    for (const [lineId, elemIds] of m.geometryMapping.lineToElements.entries()) {
      const ratio = Math.min((mMap.get(lineId) ?? 0) / maxM, 1);
      const col = new THREE.Color().setHSL(0.55 - ratio * 0.5, 0.9, 0.55);
      const pts: THREE.Vector3[] = [];
      for (const eIdx of elemIds) {
        const [na, nb] = m.elements[eIdx];
        pts.push(defCoords[na], defCoords[nb]);
      }
      group.add(
        new THREE.LineSegments(
          new THREE.BufferGeometry().setFromPoints(pts),
          new THREE.LineBasicMaterial({ color: col }),
        ),
      );
    }

    const nodeGeom = new THREE.SphereGeometry(0.07, 10, 10);
    const nodeMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
    for (const v of defCoords) {
      const sp = new THREE.Mesh(nodeGeom, nodeMat);
      sp.position.copy(v);
      group.add(sp);
    }

    const suppGeom = new THREE.ConeGeometry(0.25, 0.35, 4);
    const suppMat = new THREE.MeshBasicMaterial({ color: 0xf43f5e, wireframe: true });
    for (const ptId of comps.supports.keys()) {
      const ni = m.geometryMapping.pointToNodes.get(ptId);
      if (ni !== undefined && defCoords[ni]) {
        const cone = new THREE.Mesh(suppGeom, suppMat);
        cone.rotation.x = Math.PI / 2;
        cone.position.copy(defCoords[ni]);
        cone.position.z -= 0.18;
        group.add(cone);
      }
    }

    renderer.render(scene, camera);
  });

  const ro = new ResizeObserver(() => {
    const w = container.clientWidth || 700;
    const h = container.clientHeight || 500;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
    renderer.render(scene, camera);
  });
  ro.observe(container);

  return container;
}
