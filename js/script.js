/**
 * script.js — Composite Trapezoidal Rule Calculator
 * Sends form data to Flask POST /calculate and renders results.
 */

const API_URL = "/calculate";

// ── Element refs ──────────────────────────────────────────────────────────────
const calcBtn   = document.getElementById("calc-btn");
const resultBox = document.getElementById("result-box");
const resultVal = document.getElementById("result-value");
const resultSub = document.getElementById("result-sub");
const outH      = document.getElementById("out-h");
const outErr    = document.getElementById("out-err");
const stepsBody = document.getElementById("steps-body");

// ── Calculate ─────────────────────────────────────────────────────────────────
calcBtn.addEventListener("click", async () => {
  const func  = document.getElementById("func-input").value.trim();
  const a     = document.getElementById("lower-bound").value.trim();
  const b     = document.getElementById("upper-bound").value.trim();
  const n     = document.getElementById("n-input").value.trim();
  const exact = document.getElementById("exact-val").value.trim();

  // ── Client-side validation ────────────────────────────────────────────────
  if (!func)        return showError("Please enter a function f(x).");
  if (a === "")     return showError("Please enter the lower bound a.");
  if (b === "")     return showError("Please enter the upper bound b.");
  if (n === "")     return showError("Please enter the number of subintervals n.");
  if (+a >= +b)     return showError("Lower bound a must be less than upper bound b.");
  if (+n < 2)       return showError("n must be at least 2.");
  if (+n % 2 !== 0) return showError("n should be an even integer.");

  setLoading(true);

  const payload = {
    func,
    a:     parseFloat(a),
    b:     parseFloat(b),
    n:     parseInt(n, 10),
    exact: exact !== "" ? parseFloat(exact) : null,
  };

  try {
    const res  = await fetch(API_URL, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(payload),
    });

    const data = await res.json();

    if (!data.ok) {
      showError(data.error || "Calculation failed.");
      return;
    }

    renderResult(data);
  } catch (err) {
    showError("Network error — is the Flask server running on port 5000?");
  } finally {
    setLoading(false);
  }
});

// ── Render result ─────────────────────────────────────────────────────────────
function renderResult(data) {
  resultBox.classList.remove("empty");
  resultVal.textContent = fmt(data.result, 8);
  resultSub.textContent =
    data.exact != null
      ? `Exact: ${fmt(data.exact, 8)}  |  Absolute error: ${fmt(data.abs_error, 6)}`
      : "No exact value provided — error comparison unavailable.";

  outH.textContent   = fmt(data.h, 6);
  outErr.textContent = data.abs_error != null ? fmt(data.abs_error, 6) : "N/A";

  // ── Render step-by-step breakdown ─────────────────────────────────────────
  stepsBody.innerHTML = "";
  data.steps.forEach(step => {
    const lines = step.split("\n");
    const div   = document.createElement("div");
    div.className = "out-step";

    const heading       = document.createElement("div");
    heading.className   = "out-step-label";
    heading.textContent = lines[0];
    div.appendChild(heading);

    const body       = document.createElement("div");
    body.style.paddingTop = "4px";
    body.textContent = lines.slice(1).join("\n");
    div.appendChild(body);

    stepsBody.appendChild(div);
  });

  // Open the steps panel if it's collapsed
  if (stepsBody.style.display === "none") {
    stepsBody.style.display = "block";
    document.querySelector(".chevron").style.transform = "rotate(0deg)";
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmt(val, sig = 6) {
  return Number(val).toPrecision(sig).replace(/\.?0+$/, "");
}

function showError(msg) {
  resultBox.classList.add("empty");
  resultVal.textContent = "✕";
  resultSub.textContent = msg;
  outH.textContent      = "—";
  outErr.textContent    = "—";
  stepsBody.innerHTML   = `<span class="placeholder">${msg}</span>`;
}

function setLoading(on) {
  calcBtn.disabled = on;
  if (on) {
    calcBtn.textContent = "Calculating…";
  } else {
    calcBtn.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
           stroke-linecap="round" stroke-linejoin="round">
        <polygon points="5 3 19 12 5 21 5 3"/>
      </svg>
      Calculate Integral`;
  }
}