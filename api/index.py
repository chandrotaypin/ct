"""
api/index.py — Vercel entry point for the Composite Trapezoidal Rule Calculator
PIT Finals 2026 · Topic #29

Vercel folder structure:
    COMP.../
    ├── api/
    │   └── index.py            ← this file
    ├── css/
    │   └── trapezoidal.css
    ├── html/
    │   └── trapezoidal.html
    ├── js/
    │   └── script.js
    ├── requirements.txt
    └── vercel.json
"""

import math
import re
import os
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

# Allow cross-origin requests
try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    pass

# Root of the project (one level above /api/)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))




_SAFE_NAMES = {
    # constants
    "pi":        math.pi,
    "e":         math.e,
    "inf":       math.inf,
    # trig
    "sin":       math.sin,
    "cos":       math.cos,
    "tan":       math.tan,
    "asin":      math.asin,
    "acos":      math.acos,
    "atan":      math.atan,
    "sinh":      math.sinh,
    "cosh":      math.cosh,
    "tanh":      math.tanh,
    # exponential / log
    "exp":       math.exp,
    "log":       math.log,
    "log2":      math.log2,
    "log10":     math.log10,
    # power / misc
    "sqrt":      math.sqrt,
    "abs":       abs,
    "ceil":      math.ceil,
    "floor":     math.floor,
    "pow":       math.pow,
    "factorial": math.factorial,
}


def _validate(expr: str) -> None:
    """Block dangerous tokens before eval."""
    forbidden = [
        "__", "import", "exec", "eval", "open", "os", "sys",
        "subprocess", "builtins", "globals", "locals",
        "getattr", "setattr", "delattr", "compile", "input", "print",
    ]
    lower = expr.lower()
    for token in forbidden:
        if token in lower:
            raise ValueError(f"Expression contains forbidden token: '{token}'")
    if re.search(r"[^0-9x+\-*/^().,%\s a-zA-Z_]", expr):
        raise ValueError("Expression contains disallowed characters.")


def _preprocess(expr: str) -> str:
    """
    Convert common math notation to valid Python before eval.
      sin^2(x)  →  sin(x)**2
      cos^2(x)  →  cos(x)**2
      ln(x)     →  log(x)
      e^x       →  exp(x)   (only bare e^ pattern)
      ^         →  **
    """
    # trigo
    expr = re.sub(
        r'(sin|cos|tan|asin|acos|atan|sinh|cosh|tanh|sqrt|log|exp)\^(\d+)\(',
        r'\1(\2(',   # placeholder — handled below
        expr
    )
    # Better approach
    expr = re.sub(
        r'(sin|cos|tan|asin|acos|atan|sinh|cosh|tanh|sqrt|log|exp)\^(\d+)\(([^)]*)\)',
        r'\1(\3)**\2',
        expr
    )
    # ln(x) → log(x)
    expr = re.sub(r'\bln\s*\(', 'log(', expr)
    # e^(...) where ... is a simple token → exp(...)
    expr = re.sub(r'\be\^(\w+)', r'exp(\1)', expr)
    expr = re.sub(r'\be\^\(([^)]*)\)', r'exp(\1)', expr)
    # ^ → **
    expr = expr.replace("^", "**")
    return expr


def evaluate(expr: str, x: float) -> float:
    """Safely evaluate f(x) for a single x value."""
    expr = _preprocess(expr)
    _validate(expr)
    namespace = {**_SAFE_NAMES, "x": x, "__builtins__": {}}
    return float(eval(expr, namespace))  # noqa: S307

#COMPOSITE RULE
def composite_trapezoidal(func_expr: str, a: float, b: float, n: int) -> dict:
    """
    Approximate ∫[a,b] f(x) dx using the Composite Trapezoidal Rule.

    Returns a dict with: result, h, nodes, steps, interior_sum,
                         weighted_sum, f0, fn
    """
    if n < 2:
        raise ValueError("n must be at least 2.")
    if a >= b:
        raise ValueError("Lower bound a must be less than upper bound b.")

    h = (b - a) / n

    # Build node table
    nodes = []
    for i in range(n + 1):
        xi  = a + i * h
        fxi = evaluate(func_expr, xi)
        nodes.append({
            "i":      i,
            "x":      round(xi, 8),
            "fx":     round(fxi, 8),
            "weight": 1 if (i == 0 or i == n) else 2,
        })

    f0            = nodes[0]["fx"]
    fn            = nodes[-1]["fx"]
    interior_vals = [nd["fx"] for nd in nodes[1:-1]]
    interior_sum  = sum(interior_vals)
    weighted_sum  = f0 + 2 * interior_sum + fn
    result        = (h / 2) * weighted_sum

    # ── Step-by-step text ─────────────────────────────────────────────────────
    steps = []

    steps.append(
        f"STEP 1 — Parameters\n"
        f"  a = {a},  b = {b},  n = {n},  f(x) = {func_expr}"
    )

    steps.append(
        f"STEP 2 — Step size\n"
        f"  h = (b − a) / n = ({b} − {a}) / {n} = {h:.8g}"
    )

    node_lines = "\n".join(
        f"  i={nd['i']:>3}   x = {nd['x']:.6f}   "
        f"f(x) = {nd['fx']:.8g}   weight = {nd['weight']}"
        for nd in nodes
    )
    steps.append(f"STEP 3 — Function evaluations at nodes\n{node_lines}")

    interior_detail = " + ".join(f"{v:.8g}" for v in interior_vals)
    steps.append(
        f"STEP 4 — Interior sum\n"
        f"  Σ f(x₁…xₙ₋₁) = {interior_detail}\n"
        f"               = {interior_sum:.8g}"
    )

    steps.append(
        f"STEP 5 — Apply the formula\n"
        f"  T = (h/2) × [f(x₀) + 2·Σ_interior + f(xₙ)]\n"
        f"    = ({h:.8g}/2) × [{f0:.8g} + 2·({interior_sum:.8g}) + {fn:.8g}]\n"
        f"    = {h/2:.8g} × {weighted_sum:.8g}\n"
        f"    = {result:.10g}"
    )

    return {
        "result":       result,
        "h":            h,
        "nodes":        nodes,
        "steps":        steps,
        "interior_sum": interior_sum,
        "weighted_sum": weighted_sum,
        "f0":           f0,
        "fn":           fn,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  API ROUTE
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/calculate", methods=["POST"])
def calculate():
    """
    POST /calculate
    Request JSON:
        { "func": "x**2", "a": 0, "b": 1, "n": 4, "exact": null }

    Response JSON (success):
        { "ok": true, "result": 0.34375, "h": 0.25, "nodes": [...],
          "steps": [...], "abs_error": 0.01042, "exact": 0.33333 }

    Response JSON (error):
        { "ok": false, "error": "..." }
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify(ok=False, error="Request body must be valid JSON."), 400

    func_expr = data.get("func", "").strip()
    if not func_expr:
        return jsonify(ok=False, error="func is required."), 400

    try:
        a = float(data["a"])
        b = float(data["b"])
        n = int(data["n"])
    except (KeyError, TypeError, ValueError) as exc:
        return jsonify(ok=False, error=f"Invalid parameter: {exc}"), 400

    exact = data.get("exact")
    if exact is not None:
        try:
            exact = float(exact)
        except (TypeError, ValueError):
            exact = None

    try:
        res = composite_trapezoidal(func_expr, a, b, n)
    except ValueError as exc:
        return jsonify(ok=False, error=str(exc)), 422
    except ZeroDivisionError:
        return jsonify(ok=False, error="Division by zero in f(x)."), 422
    except Exception as exc:
        return jsonify(ok=False, error=f"Evaluation error: {exc}"), 422

    payload = {"ok": True, **res}

    if exact is not None:
        payload["exact"]     = exact
        payload["abs_error"] = abs(exact - res["result"])
        payload["steps"].append(
            f"STEP 6 — Error analysis\n"
            f"  Exact value    = {exact:.10g}\n"
            f"  Approx. value  = {res['result']:.10g}\n"
            f"  Absolute error = |{exact:.10g} − {res['result']:.10g}|\n"
            f"                 = {payload['abs_error']:.6g}"
        )

    return jsonify(payload)


if __name__ == "__main__":
    app.run(debug=True, port=5000)