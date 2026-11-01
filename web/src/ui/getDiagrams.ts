import van, { type State } from "vanjs-core";

export function getDiagrams({
  lineMaxMomentKNm,
  lineMaxShearKN,
  fixityFactorGamma,
}: {
  lineMaxMomentKNm: State<Map<number, number>>;
  lineMaxShearKN: State<Map<number, number>>;
  fixityFactorGamma: State<number>;
}): HTMLElement {
  const wrap = document.createElement("div");
  wrap.style.display = "flex";
  wrap.style.flexDirection = "column";
  wrap.style.gap = "12px";

  const cBars = document.createElement("canvas");
  cBars.className = "lp-chart";
  const cGamma = document.createElement("canvas");
  cGamma.className = "lp-chart";

  const makeCard = (title: string, canvas: HTMLCanvasElement) => {
    const d = document.createElement("div");
    d.className = "lp-card";
    const h = document.createElement("h3");
    h.textContent = title;
    d.append(h, canvas);
    return d;
  };

  wrap.append(
    makeCard("Momentos Máximos por Barra |M| [kN·m]", cBars),
    makeCard("Curva Monforton-Wu γ(Sj) y Cortantes |V| [kN]", cGamma),
  );

  van.derive(() => {
    const ctx1 = cBars.getContext("2d");
    if (ctx1) {
      const w = (cBars.width = cBars.clientWidth || 320);
      const h = (cBars.height = cBars.clientHeight || 150);
      ctx1.clearRect(0, 0, w, h);
      const entries = [...lineMaxMomentKNm.val.entries()];
      const maxM = Math.max(...entries.map((e) => e[1]), 1);
      entries.forEach(([lid, mVal], idx) => {
        const bw = (w - 50) / Math.max(entries.length, 1) - 10;
        const x = 35 + idx * (bw + 10);
        const bh = ((h - 40) * mVal) / maxM;
        ctx1.fillStyle = "#38bdf8";
        ctx1.fillRect(x, h - 22 - bh, bw, bh);
        ctx1.fillStyle = "#f8fafc";
        ctx1.font = "11px Inter, sans-serif";
        ctx1.fillText(`L${lid}: ${mVal.toFixed(1)}`, x, h - 7);
      });
    }

    const ctx2 = cGamma.getContext("2d");
    if (ctx2) {
      const w = (cGamma.width = cGamma.clientWidth || 320);
      const h = (cGamma.height = cGamma.clientHeight || 150);
      ctx2.clearRect(0, 0, w, h);
      ctx2.fillStyle = "#10b981";
      ctx2.font = "12px Inter, sans-serif";
      ctx2.fillText(`Factor de Empotramiento γ = ${fixityFactorGamma.val.toFixed(3)}`, 14, 24);
      let y = 48;
      for (const [lid, vVal] of lineMaxShearKN.val.entries()) {
        ctx2.fillStyle = "#94a3b8";
        ctx2.fillText(`Barra L${lid} -> |V|max = ${vVal.toFixed(2)} kN`, 14, y);
        y += 22;
      }
    }
  });

  return wrap;
}
