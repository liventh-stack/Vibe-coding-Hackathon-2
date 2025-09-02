async function fetchEntries(alias) {
  const url = alias ? `/api/entries?alias=${encodeURIComponent(alias)}` : "/api/entries";
  const res = await fetch(url);
  return await res.json();
}

function computeJoySeries(rows) {
  const points = [];
  for (const r of rows) {
    const t = new Date(r.created_at);
    const scores = r.emotion_scores || {};
    const joy = typeof scores.joy === "number" ? scores.joy : (r.emotion_label === "joy" ? 1 : 0);
    points.push({ x: t, y: Math.round(joy * 100) });
  }
  points.sort((a,b)=>a.x - b.x);
  return points;
}

let chart;
async function renderChart(alias) {
  const rows = await fetchEntries(alias);
  const dataPoints = computeJoySeries(rows);
  const ctx = document.getElementById("moodChart").getContext("2d");
  if (chart) chart.destroy();
  chart = new Chart(ctx, {
    type: "line",
    data: {
      datasets: [{
        label: "Joy % over time",
        data: dataPoints,
        fill: false,
        tension: 0.2
      }]
    },
    options: {
      parsing: false,
      scales: {
        x: { type: "time", time: { unit: "day" } },
        y: { beginAtZero: true, max: 100, title: { display: true, text: "Joy %" } }
      },
      plugins: {
        tooltip: { callbacks: {
          label: (ctx)=>`Joy: ${ctx.parsed.y}%`
        }}
      }
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  // Load initial chart (all entries)
  renderChart();
  document.getElementById("loadBtn").addEventListener("click", () => {
    const alias = document.getElementById("filterAlias").value.trim();
    renderChart(alias || undefined);
  });
});
