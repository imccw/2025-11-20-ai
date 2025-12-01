const API_BASE = window.IMAGE_ANALYSIS_API_URL || "http://127.0.0.1:8000";
const ANALYZE_ENDPOINT = new URL("/analyze-image", API_BASE).href;
const form = document.getElementById("image-form");
const fileInput = document.getElementById("image-file");
const statusText = document.getElementById("status-text");
const macroList = document.getElementById("macro-list");
const analysisOutput = document.getElementById("analysis-output");
const analyzeBtn = document.getElementById("analyze-btn");
const chartCtx = document.getElementById("macro-chart");
let macroChart;

const MACRO_KEYS = [
  { key: "protein_g", label: "Protein" },
  { key: "carbs_g", label: "Carbs" },
  { key: "fat_g", label: "Fat" },
];

const CHART_COLORS = ["#2563eb", "#10b981", "#f97316"];

function parseGramValue(value) {
  if (value === undefined || value === null) return 0;
  const matches = String(value).match(/-?\d+(\.\d+)?/g);
  if (!matches) return 0;
  const numbers = matches.map(Number);
  return numbers.reduce((sum, current) => sum + current, 0) / numbers.length;
}

function parseAnalysisText(text) {
  if (!text) return null;
  let trimmed = text.trim();
  if (!trimmed) return null;

  // Strip Markdown-style code fences and surrounding annotations before parsing.
  trimmed = trimmed.replace(/```[a-z]*\s*/gi, "").replace(/```/g, "");

  try {
    return JSON.parse(trimmed);
  } catch {
    const start = trimmed.indexOf("{");
    const end = trimmed.lastIndexOf("}");
    if (start >= 0 && end > start) {
      try {
        return JSON.parse(trimmed.slice(start, end + 1));
      } catch (err) {
        console.warn("Partial JSON parse failed:", err);
      }
    }
  }
  return null;
}

function renderMacroList(macros) {
  macroList.innerHTML = MACRO_KEYS.map(({ key, label }) => {
    const rawValue = macros && macros[key] !== undefined ? macros[key] : "—";
    return `<div class="macro-row"><span>${label}</span><strong>${rawValue}</strong></div>`;
  }).join("");
}

function renderChart(macros) {
  const data = MACRO_KEYS.map(({ key }) => Math.max(0, parseGramValue(macros?.[key])));

  if (!macroChart) {
    macroChart = new Chart(chartCtx, {
      type: "pie",
      data: {
        labels: MACRO_KEYS.map(({ label }) => label),
        datasets: [
          {
            data,
            backgroundColor: CHART_COLORS,
            borderWidth: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              padding: 12,
              boxWidth: 14,
            },
          },
        },
      },
    });
  } else {
    macroChart.data.datasets[0].data = data;
    macroChart.update();
  }
}

function resetDisplay(message) {
  statusText.textContent = message;
  macroList.textContent = "";
  analysisOutput.textContent = "";
  if (macroChart) {
    macroChart.data.datasets[0].data = [0, 0, 0];
    macroChart.update();
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = fileInput.files?.[0];
  if (!file) {
    statusText.textContent = "Please select an image before analyzing.";
    return;
  }

  analyzeBtn.disabled = true;
  statusText.textContent = "Uploading and analyzing…";

  const formData = new FormData();
  formData.append("file", file, file.name);

  try {
    const response = await fetch(ANALYZE_ENDPOINT, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || "Failed to analyze the image.");
    }

    const payload = await response.json();
    const parsedMacros = parseAnalysisText(payload?.analysis);

    if (!parsedMacros) {
      throw new Error("Unable to parse macronutrient data from the response.");
    }

    renderMacroList(parsedMacros);
    renderChart(parsedMacros);
    analysisOutput.textContent = JSON.stringify(parsedMacros, null, 2);
    statusText.textContent = "Macronutrient breakdown ready.";
  } catch (error) {
    console.error(error);
    resetDisplay("Analysis failed. Try a clearer image or check the server.");
  } finally {
    analyzeBtn.disabled = false;
  }
});
