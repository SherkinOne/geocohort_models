const BLUE = ["#1F5A99", "#2E7BCB", "#3C8DE6", "#93C5FD", "#0A2540"];

//creates a bar chart for the overall screen
function barChart(tabID, rows, xKey, yKey) {
  const el = d3.select(tabID);
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
  // svg
  //   .append("text")
  //   .attr("x", m.left)
  //   .attr("y", m.top - 6)
  //   .attr("fill", BLUE[4])
  //   .attr("font-weight", 700)
  //   .text(title || "");
}
// creates the line charts for the k scores and silhouette scores
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

function renderScatterPlot(sel, data, title) {
  // Data preparation
  data.forEach((d) => {
    d.timestamp = new Date(d.timestamp);
    d.appliance_power_kW = +d.appliance_power_kW;
  });
  console.log("Data for Scatter Plot ", data);
  // SVG setup
  const margin = { top: 20, right: 30, bottom: 40, left: 50 };
  const width = 800 - margin.left - margin.right;
  const height = 300 - margin.top - margin.bottom;
  const svg = d3
    .select(sel)
    .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  // X and Y scales
  const x = d3
    .scaleTime()
    .domain(d3.extent(data, (d) => d.timestamp))
    .range([0, width]);

  const y = d3
    .scaleLinear()
    .domain(d3.extent(data, (d) => d.energy_kW))
    .range([height, 0]);

  // Axes
  svg
    .append("g")
    .attr("transform", `translate(0,${height})`)
    .call(d3.axisBottom(x));
  svg.append("g").call(d3.axisLeft(y));

  // Circles for each data point
  svg
    .selectAll("circle")
    .data(data)
    .enter()
    .append("circle")
    .attr("cx", (d) => x(d.timestamp))
    .attr("cy", (d) => y(d.appliance_power_kW))
    .attr("r", 4)
    .style("fill", "steelblue");
}

//renders heatmap for the individual model tabs
function renderHeatmap(sel, data, title) {
  const parsedData = data.map((d) => ({
    x: new Date(d.timestamp).toISOString().split("T")[0], // Day
    y: new Date(d.timestamp).getHours(), // Hour
    value: d.decision_score,
  }));

  console.log("Parsed Data for Heatmap ", parsedData);
  const margin = { top: 30, right: 20, bottom: 50, left: 60 },
    width = 900 - margin.left - margin.right,
    height = 450 - margin.top - margin.bottom;

  const svg = d3
    .select(sel)
    .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
  const xGroups = Array.from(new Set(parsedData.map((d) => d.x)));
  const yGroups = Array.from(new Set(parsedData.map((d) => d.y)));

  const xScale = d3.scaleBand().domain(xGroups).range([0, width]).padding(0.05);

  const yScale = d3
    .scaleBand()
    .domain(yGroups)
    .range([0, height])
    .padding(0.05);

  const colorScale = d3
    .scaleSequential()
    .domain(d3.extent(parsedData, (d) => d.value))
    .interpolator(d3.interpolateRdBu); // or any other

  svg
    .selectAll()
    .data(parsedData, (d) => d.x + ":" + d.y)
    .enter()
    .append("rect")
    .attr("x", (d) => xScale(d.x))
    .attr("y", (d) => yScale(d.y))
    .attr("width", xScale.bandwidth())
    .attr("height", yScale.bandwidth())
    .style("fill", (d) => colorScale(d.value));

  svg
    .append("g")
    .attr("transform", `translate(0,${height})`)
    .call(d3.axisBottom(xScale));
  svg.append("g").call(d3.axisLeft(yScale));
}

//creates the table for the scores on the overall page
function renderScoresTable() {
  const table = document.getElementById("scores-table");

  const tableHeader = document.createElement("thead");
  const headerRow = document.createElement("tr");

  // Add "Model" header
  const thModel = document.createElement("th");
  thModel.textContent = "Model";
  headerRow.appendChild(thModel);

  // Add metric headers
  const metricNames = Object.keys(GRAPHMETRICSDATA); // ["MAE", "MAPE_pct", "R2", "RMSE"]
  metricNames.forEach((metric) => {
    const th = document.createElement("th");
    th.textContent = metric;
    headerRow.appendChild(th);
  });
  tableHeader.appendChild(headerRow);
  table.appendChild(tableHeader);

  const tableBody = document.createElement("tbody");

  // Get all model names (assumes all metric arrays have same model order and count)
  const models = GRAPHMETRICSDATA[metricNames[0]].map((item) => item.category);

  models.forEach((modelName) => {
    const row = document.createElement("tr");
    // Model name cell
    const tdModel = document.createElement("td");
    tdModel.textContent = modelName;
    row.appendChild(tdModel);

    // Metric value cells
    metricNames.forEach((metric) => {
      const metricArr = GRAPHMETRICSDATA[metric];
      const found = metricArr.find((item) => item.category === modelName);
      const tdMetric = document.createElement("td");
      tdMetric.textContent = found ? found.value : "";
      row.appendChild(tdMetric);
    });

    tableBody.appendChild(row);
  });
  table.appendChild(tableBody);
}

// This renders series for the individual model tabs
function renderSeries(sel, rows, title) {
  const el = d3.select(sel);
  // el.selectAll("*").remove();
  const width = el.node().clientWidth || 900,
    height = el.node().clientHeight || 300;
  const m = { top: 18, right: 24, bottom: 40, left: 56 };
  keyNames = Object.keys(rows[0]);
  const substring = "time";
  keyNames = keyNames.filter((item) => !item.includes(substring));
  const data = rows.map(function (p) {
    return {
      t: new Date(p.timestamp),
      actual: p[keyNames[1]],
      pred: p[keyNames[0]],
    };
  });
  console.log("DATA FOR RENDER SERIES ", data);
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

// I have no idea what this does
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

// this is called on the overall page to render all the charts and table when the doc loads
function renderOverall() {
  // split GRAPHMETRICSDATA
  console.log(
    "GRAPHMETRICSDATA ",
    GRAPHMETRICSDATA,
    Object.keys(GRAPHMETRICSDATA).length
  );
  if (Object.keys(GRAPHMETRICSDATA).length > 0) {
    const parent = document.getElementById("overallTabPane");
    let htmlString = "";
    switch (tabName) {
      case "Load Balancing Models":
      case "Behavioural Change Impact Models":
      case "Dynamic Pricing Optimisation Models":
      case "Anomaly Detection Models":
        console.log("here")
        htmlString = Anomaly_Detection_Models_html;
        console.log(htmlString)
        parent.insertAdjacentHTML("afterbegin", htmlString);
        for (key in GRAPHMETRICSDATA) {
          console.log(key -  GRAPHMETRICSDATA[key]);
           barChart(
            "#chart-" + key.toLowerCase(),
            GRAPHMETRICSDATA[key],
            "category",
            "value"
          );
        }
        // renderHeatmap(keyID, data.results, "Heatmap for ");
        // renderScatterPlot(keyID, data.results, "Scatter Plot for ");
        break;
      case "Energy Consumption Forecasting":
        console.log("Enery")
        htmlString = energy_consumption_forecasting_html;
        // Inserts HTML as the last child *within* overallTabPane
        parent.insertAdjacentHTML("afterbegin", htmlString);
        for (key in GRAPHMETRICSDATA) {
          barChart(
            "#chart-" + key.toLowerCase(),
            GRAPHMETRICSDATA[key],
            "category",
            "value"
          );
        }
        break;
      default:
    } // end of switch
    renderScoresTable();
  } // enfd of if

  lineChart(
    "#chart-elbow",
    KDATA.elbow.map(function (e) {
      return { k: +e.k, inertia: +e.inertia };
    }),
    "k",
    "inertia",
    "Elbow (Inertia vs k)"
  );

  lineChart(
    "#chart-silhouette",
    KDATA.silhouette.map(function (s) {
      return { k: +s.k, silhouette: +s.silhouette };
    }),
    "k",
    "silhouette",
    "Silhouette vs k"
  );
  // renderScoresTable();
}
function fmt(x) {
  return x == null || Number.isNaN(x)
    ? "—"
    : typeof x === "number"
    ? Math.round(x * 1000) / 1000
    : x;
}
// window.addEventListener("resize", renderAll);

document.addEventListener("DOMContentLoaded", function () {
  // Your function here
  // console.log("DATA ", GRAPHMETRICSDATA);
  renderOverall();
  document.querySelectorAll(".tab").forEach(function (tab) {
    tab.addEventListener("click", function () {
      document.querySelectorAll(".tab").forEach(function (t) {
        t.classList.remove("active");
      });
      tab.classList.add("active");
      var key = tab.getAttribute("data-tab");
      document.querySelectorAll(".pane").forEach(function (p) {
        if (p.getAttribute("data-pane") === key) {
          p.style.display = "block";
          console.log("key ", key);
          let greatGrandChild = p.querySelector(
            "div > .grid > .card > .chart "
          );
          let keyID = key.replace(/ /g, "_");
          if (greatGrandChild) {
            if (!greatGrandChild.hasAttribute("id")) {
              greatGrandChild.setAttribute("id", "chart-" + keyID);
              const formData = new FormData();
              formData.append("graphType", tab.getAttribute("data-tab"));
              formData.append("activePage", tabName);
              console.log(formData);
              fetch("/get_graph_data", {
                method: "POST",
                body: formData,
              })
                .then((response) => {
                  if (!response.ok) {
                    throw new Error("Network response was not ok");
                  }
                  return response.json(); // ← parses the body as JSON
                })
                .then((data) => {
                  keyID = "#chart-" + keyID;
                  console.log("DATA FETCHED FOR TAB ", tabName);
                  switch (tabName) {
                    case "Load Balancing Models":
                    case "Behavioural Change Impact Models":
                    case "Dynamic Pricing Optimisation Models":
                    case "Anomaly Detection Models":
                      renderSeries(keyID, data.results, "Graph for ");
                      // renderHeatmap(keyID, data.results, "Heatmap for ");
                      // renderScatterPlot(keyID, data.results, "Scatter Plot for ");
                      break;
                    case "Energy Consumption Forecasting":
                      renderSeries(keyID, data.results, "Graph for ");
                      break;
                    default:
                  }
                });
              // .catch((error) => {
              //   console.error("Fetch error:", error);
              // });
            }
          }
        } else {
          p.style.display = "none";
        }
      });

      // renderAll();
    });
  });
});
