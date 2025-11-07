const BLUE = ["#1F5A99", "#2E7BCB", "#3C8DE6", "#93C5FD", "#0A2540"];

function barChart_org(sel, rows, xKey, yKey, title) {
  const el = d3.select(sel);
  el.selectAll("*").remove();
  const width = el.node().clientWidth || 600,
    height = el.node().clientHeight || 300;
  const m = { top: 18, right: 24, bottom: 60, left: 64 };
  const x = d3
    .scaleBand()
    .domain(rows.map((d) => d[xKey]))
    .range([m.left, width - m.right])
    .padding(0.25);
  const y = d3
    .scaleLinear()
    .domain([0, d3.max(rows, (d) => +d[yKey])])
    .nice()
    .range([height - m.bottom, m.top]);
  const svg = el.append("svg").attr("width", width).attr("height", height);
  svg
    .selectAll("rect")
    .data(rows)
    .join("rect")
    .attr("x", (d) => x(d[xKey]))
    .attr("y", (d) => y(d[yKey]))
    .attr("width", x.bandwidth())
    .attr("height", (d) => y(0) - y(d[yKey]))
    .attr("fill", (d, i) => BLUE[i % BLUE.length]);
  svg
    .append("g")
    .attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x))
    .selectAll("text")
    .attr("transform", "rotate(-18)")
    .style("text-anchor", "end");
  svg
    .append("g")
    .attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y));
  svg
    .append("text")
    .attr("x", m.left)
    .attr("y", m.top - 6)
    .attr("fill", BLUE[4])
    .attr("font-weight", 700)
    .text(title || "");
}

function barChart(sel, rows, xKey, yKey, title) {
  const el = d3.select(sel);
  el.selectAll("*").remove();

  const width = el.node().clientWidth || 600,
        height = el.node().clientHeight || 300;

  const m = { top: 18, right: 24, bottom: 60, left: 64 };
  const x = d3
    .scaleBand()
    .domain(rows.map(d => d[xKey]))
    .range([m.left, width - m.right])
    .padding(0.25);

  const y = d3
    .scaleLinear()
    .domain([0, d3.max(rows, d => +d[yKey])])
    .nice()
    .range([height - m.bottom, m.top]);

  const svg = el.append("svg").attr("width", width).attr("height", height);
  svg
    .selectAll("rect")
    .data(rows)
    .join("rect")
    .attr("x", d => x(d[xKey]))
    .attr("y", d => y(d[yKey]))
    .attr("width", x.bandwidth())
    .attr("height", d => y(0) - y(d[yKey]))
    .attr("fill", (d, i) => BLUE[i % BLUE.length]);
      svg
    .append("g")
    .attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x))
    .selectAll("text")
    .attr("transform", "rotate(-18)")
    .style("text-anchor", "end");
  svg
    .append("g")
    .attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y));
  svg
    .append("text")
    .attr("x", m.left)
    .attr("y", m.top - 6)
    .attr("fill", BLUE[4])
    .attr("font-weight", 700)
    .text(title || "");
}
 

function lineChart(sel, rows, xKey, yKey, title) {
  const el = d3.select(sel);
  el.selectAll("*").remove();
  const width = el.node().clientWidth || 600,
    height = el.node().clientHeight || 300;
  const m = { top: 18, right: 24, bottom: 40, left: 64 };
  const x = d3
    .scaleLinear()
    .domain(d3.extent(rows, (d) => +d[xKey]))
    .range([m.left, width - m.right]);
  const y = d3
    .scaleLinear()
    .domain([0, d3.max(rows, (d) => +d[yKey])])
    .nice()
    .range([height - m.bottom, m.top]);
  const svg = el.append("svg").attr("width", width).attr("height", height);
  const line = d3
    .line()
    .x((d) => x(d[xKey]))
    .y((d) => y(d[yKey]));
  svg
    .append("path")
    .datum(rows)
    .attr("fill", "none")
    .attr("stroke", BLUE[2])
    .attr("stroke-width", 2)
    .attr("d", line);
  svg
    .append("g")
    .attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).ticks(rows.length));
  svg
    .append("g")
    .attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y));
  svg
    .append("text")
    .attr("x", m.left)
    .attr("y", m.top - 6)
    .attr("fill", BLUE[4])
    .attr("font-weight", 700)
    .text(title || "");
}
function renderScoresTable(sel, scores) {
  const el = d3.select(sel);
  el.selectAll("*").remove();
  const cols = ["model", "MAE", "RMSE", "R2", "MAPE_pct"];
  const table = el.append("table");
  const thead = table.append("thead").append("tr");
  cols.forEach((c) => thead.append("th").text(c));
  const tbody = table.append("tbody");
  scores.forEach(function (r) {
    const tr = tbody.append("tr");
    cols.forEach(function (c) {
      tr.append("td").text(c === "model" ? r[c] : fmt(r[c]));
    });
  });
}
function renderSeries(sel, rows, title) {
  const el = d3.select(sel);
  el.selectAll("*").remove();
  const width = el.node().clientWidth || 900,
    height = el.node().clientHeight || 300;
  const m = { top: 18, right: 24, bottom: 40, left: 56 };
  const data = rows.map(function (p) {
    return { t: new Date(p.time), actual: p.actual, pred: p.temperature_C };
  });
  const x = d3
    .scaleTime()
    .domain(d3.extent(data, (d) => d.t))
    .range([m.left, width - m.right]);
  const yMin = d3.min(data, (d) => Math.min(d.pred, d.actual));
  const yMax = d3.max(data, (d) => Math.max(d.pred, d.actual));
  const y = d3
    .scaleLinear()
    .domain([yMin, yMax])
    .nice()
    .range([height - m.bottom, m.top]);
  const svg = el.append("svg").attr("width", width).attr("height", height);
  svg
    .append("path")
    .datum(data)
    .attr("fill", "none")
    .attr("stroke", BLUE[0])
    .attr("stroke-width", 1.6)
    .attr(
      "d",
      d3
        .line()
        .x((d) => x(d.t))
        .y((d) => y(d.actual))
    );
  svg
    .append("path")
    .datum(data)
    .attr("fill", "none")
    .attr("stroke", BLUE[2])
    .attr("stroke-width", 2.2)
    .attr(
      "d",
      d3
        .line()
        .x((d) => x(d.t))
        .y((d) => y(d.pred))
    );
  svg
    .append("g")
    .attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x));
  svg
    .append("g")
    .attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y));
  svg
    .append("text")
    .attr("x", m.left)
    .attr("y", m.top - 6)
    .attr("fill", BLUE[4])
    .attr("font-weight", 700)
    .text(title || "");
  const legend = svg
    .append("g")
    .attr("transform", `translate(${width - m.right - 180},${m.top})`);
  legend
    .append("rect")
    .attr("x", 0)
    .attr("y", 0)
    .attr("width", 10)
    .attr("height", 10)
    .attr("fill", BLUE[0]);
  legend
    .append("text")
    .attr("x", 16)
    .attr("y", 9)
    .text("Actual")
    .attr("font-size", "12px");
  legend
    .append("rect")
    .attr("x", 0)
    .attr("y", 18)
    .attr("width", 10)
    .attr("height", 10)
    .attr("fill", BLUE[2]);
  legend
    .append("text")
    .attr("x", 16)
    .attr("y", 27)
    .text("Prediction")
    .attr("font-size", "12px");
}
function metricPills(sel, m) {
  d3.select(sel).html(
    '<span class="pill">MAE: ' +
      fmt(m.MAE) +
      "</span>" +
      '<span class="pill">RMSE: ' +
      fmt(m.RMSE) +
      "</span>" +
      '<span class="pill">R²: ' +
      fmt(m.R2) +
      "</span>" +
      '<span class="pill">MAPE: ' +
      fmt(m.MAPE_pct) +
      "%</span>"
  );
}
function renderOverall() {
  const S = DATA.scores;
  const data = [
  { category: "A", value: 23 },
  { category: "B", value: 32 },
  { category: "C", value: 10 }
];
  barChart(
    "#chart-rmse",
  data, "category", "value", "My Chart");
  // barChart(
  //   "#chart-mae",
  //   S.map(function (d) {
  //     return { model: d.model, val: d.MAE };
  //   }),
  //   "model",
  //   "val",
  //   "MAE by Model"
  // );
  // barChart(
  //   "#chart-r2",
  //   S.map(function (d) {
  //     return { model: d.model, val: d.R2 };
  //   }),
  //   "model",
  //   "val",
  //   "R² by Model"
  // );
  // barChart(
  //   "#chart-mape",
  //   S.map(function (d) {
  //     return { model: d.model, val: d.MAPE_pct };
  //   }),
  //   "model",
  //   "val",
  //   "MAPE (%) by Model"
  // );
  lineChart(
    "#chart-elbow",
    DATA.elbow.map(function (e) {
      return { k: +e.k, inertia: +e.inertia };
    }),
    "k",
    "inertia",
    "Elbow (Inertia vs k)"
  );
  lineChart(
    "#chart-silhouette",
    DATA.silhouette.map(function (s) {
      return { k: +s.k, silhouette: +s.silhouette };
    }),
    "k",
    "silhouette",
    "Silhouette vs k"
  );
  renderScoresTable("#scores-table", DATA.scores);
}
function renderModels() {
  function findModel(prefix) {
    for (var i = 0; i < DATA.results.length; i++) {
      if (DATA.results[i].model.indexOf(prefix) === 0) return DATA.results[i];
    }
    return null;
  }
  var ar = findModel("ARIMA");
  if (ar) {
    renderSeries("#chart-arima", ar.predictions, ar.model);
    metricPills("#metrics-arima", ar.metrics);
  }
  var sx = findModel("SARIMAX");
  if (sx) {
    renderSeries("#chart-sarimax", sx.predictions, sx.model);
    metricPills("#metrics-sarimax", sx.metrics);
  }
  var ls = findModel("LSTM");
  if (ls) {
    renderSeries("#chart-lstm", ls.predictions, ls.model);
    metricPills("#metrics-lstm", ls.metrics);
  }
}
function renderAll() {
  var visiblePane = document.querySelector('.pane[style*="display: block"]');
  var key = visiblePane ? visiblePane.getAttribute("data-pane") : "overall";
  if (key === "overall") renderOverall();
  else renderModels();
}
function fmt(x) {
  return x == null || Number.isNaN(x)
    ? "—"
    : typeof x === "number"
    ? Math.round(x * 1000) / 1000
    : x;
}
window.addEventListener("resize", renderAll);

document.addEventListener("DOMContentLoaded", function () {
  // Your function here
  console.log("DATA ", DATA);
  renderAll();
  document.querySelectorAll(".tab").forEach(function (tab) {
    console.log("Tab ", tab);
    tab.addEventListener("click", function () {
      document.querySelectorAll(".tab").forEach(function (t) {
        t.classList.remove("active");
      });
      tab.classList.add("active");
      var key = tab.getAttribute("data-tab");
      document.querySelectorAll(".pane").forEach(function (p) {
        p.style.display =
          p.getAttribute("data-pane") === key ? "block" : "none";
      });
      renderAll();
    });
  });
});
