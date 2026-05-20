from __future__ import annotations

import base64
from io import BytesIO
from typing import Dict, Iterable, List, Optional

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from flask import Flask, render_template_string, request

from fuzzy_credit_risk import RULES, VARIABLES, evaluate, evaluate_scenarios, membership_degree


app = Flask(__name__)


LABELS_TR = {
    "dusuk": "Dusuk",
    "orta": "Orta",
    "yuksek": "Yuksek",
}


TEMPLATE = """
<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Bulanik Kredi Risk Degerlendirme</title>
  <style>
    :root {
      --bg: #f5f7fb;
      --surface: #ffffff;
      --ink: #162033;
      --muted: #667085;
      --line: #d7deea;
      --accent: #0f766e;
      --accent-2: #2563eb;
      --danger: #dc2626;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Arial, Helvetica, sans-serif;
      letter-spacing: 0;
    }
    header {
      background: #102033;
      color: #fff;
      padding: 24px 28px;
      border-bottom: 4px solid var(--accent);
    }
    header h1 {
      margin: 0 0 8px;
      font-size: 28px;
      line-height: 1.15;
      letter-spacing: 0;
    }
    header p {
      margin: 0;
      max-width: 980px;
      color: #d8e2ef;
      line-height: 1.45;
    }
    main {
      width: min(1360px, calc(100% - 32px));
      margin: 18px auto 36px;
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 18px;
      align-items: start;
    }
    section, aside {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 10px 26px rgba(16, 32, 51, 0.07);
    }
    aside {
      padding: 18px;
      position: sticky;
      top: 14px;
    }
    h2, h3 {
      margin: 0 0 14px;
      letter-spacing: 0;
      line-height: 1.2;
    }
    h2 { font-size: 20px; }
    h3 { font-size: 17px; }
    label {
      display: block;
      margin: 16px 0 6px;
      font-weight: 700;
      font-size: 14px;
    }
    input[type="range"] {
      width: 100%;
      accent-color: var(--accent);
    }
    input[type="number"] {
      width: 100%;
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: 6px;
      font-size: 15px;
    }
    button {
      width: 100%;
      border: 0;
      border-radius: 6px;
      padding: 12px 14px;
      margin-top: 18px;
      background: var(--accent);
      color: #fff;
      font-weight: 700;
      cursor: pointer;
      font-size: 15px;
    }
    .content {
      display: grid;
      gap: 18px;
    }
    .panel {
      padding: 18px;
    }
    .metrics {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
    }
    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: #fbfcff;
    }
    .metric span {
      display: block;
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 8px;
    }
    .metric strong {
      font-size: 27px;
      line-height: 1;
    }
    .interpretation {
      margin-top: 12px;
      border-left: 4px solid var(--accent-2);
      background: #eff6ff;
      padding: 12px 14px;
      line-height: 1.45;
    }
    .grid-2 {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }
    img {
      width: 100%;
      height: auto;
      display: block;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }
    th, td {
      border-bottom: 1px solid var(--line);
      padding: 10px 9px;
      text-align: left;
      vertical-align: top;
    }
    th {
      background: #eef3fa;
      color: #263449;
      font-size: 13px;
    }
    .scroll {
      overflow-x: auto;
    }
    .muted {
      color: var(--muted);
      line-height: 1.45;
      margin: 0;
    }
    .value-row {
      display: grid;
      grid-template-columns: 1fr 78px;
      gap: 8px;
      align-items: center;
    }
    @media (max-width: 980px) {
      main {
        grid-template-columns: 1fr;
      }
      aside {
        position: static;
      }
      .metrics, .grid-2 {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <header>
    <h1>Bulanik Mantik ile Banka Kredi Risk Degerlendirme</h1>
    <p>Uc girisli Mamdani bulanik kontrolcu; aylik gelir, kredi notu ve borc/gelir orani ile 0-100 araliginda kredi risk skoru uretir.</p>
  </header>

  <main>
    <aside>
      <h2>Giris degerleri</h2>
      <form id="risk-form" method="get">
        <label for="income">Aylik gelir (bin TL)</label>
        <div class="value-row">
          <input id="income" name="income" type="range" min="0" max="100" step="1" value="{{ income }}" oninput="income_number.value=this.value">
          <input id="income_number" type="number" min="0" max="100" step="1" value="{{ income }}" oninput="income.value=this.value">
        </div>

        <label for="credit_score">Kredi notu</label>
        <div class="value-row">
          <input id="credit_score" name="credit_score" type="range" min="0" max="1000" step="10" value="{{ credit_score }}" oninput="credit_number.value=this.value">
          <input id="credit_number" type="number" min="0" max="1000" step="10" value="{{ credit_score }}" oninput="credit_score.value=this.value">
        </div>

        <label for="debt_ratio">Borc/Gelir orani (%)</label>
        <div class="value-row">
          <input id="debt_ratio" name="debt_ratio" type="range" min="0" max="100" step="1" value="{{ debt_ratio }}" oninput="debt_number.value=this.value">
          <input id="debt_number" type="number" min="0" max="100" step="1" value="{{ debt_ratio }}" oninput="debt_ratio.value=this.value">
        </div>

        <button type="submit">Hesapla</button>
      </form>
    </aside>

    <div class="content">
      <section class="panel">
        <div class="metrics">
          <div class="metric">
            <span>Risk skoru</span>
            <strong>{{ "%.2f"|format(result.risk_score) }}</strong>
          </div>
          <div class="metric">
            <span>Baskin cikti</span>
            <strong>{{ labels[result.dominant_output] }}</strong>
          </div>
          <div class="metric">
            <span>Aktif kural</span>
            <strong>{{ active_rules|length }}</strong>
          </div>
        </div>
        <div class="interpretation">{{ result.interpretation }}</div>
      </section>

      <section class="panel">
        <h2>Durulastirma sonucu</h2>
        <div class="grid-2">
          <img src="{{ output_plot }}" alt="Centroid durulastirma grafigi">
          <div>
            <h3>Cikti uyelik dereceleri</h3>
            {{ output_table|safe }}
          </div>
        </div>
      </section>

      <section class="panel">
        <h2>Uyelik fonksiyonlari</h2>
        <div class="grid-2">
          <img src="{{ income_plot }}" alt="Aylik gelir uyelik fonksiyonlari">
          <img src="{{ credit_plot }}" alt="Kredi notu uyelik fonksiyonlari">
          <img src="{{ debt_plot }}" alt="Borc gelir orani uyelik fonksiyonlari">
          <img src="{{ risk_plot }}" alt="Risk uyelik fonksiyonlari">
        </div>
      </section>

      <section class="panel">
        <h2>Aktif kural listesi</h2>
        {% if active_rules %}
          <div class="grid-2">
            <img src="{{ activation_plot }}" alt="Kural aktivasyon grafigi">
            <div class="scroll">{{ active_rule_table|safe }}</div>
          </div>
        {% else %}
          <p class="muted">Bu girisler icin aktif kural bulunamadi.</p>
        {% endif %}
      </section>

      <section class="panel">
        <h2>Kural tabani</h2>
        <div class="scroll">{{ rule_table|safe }}</div>
      </section>

      <section class="panel">
        <h2>Test senaryolari</h2>
        <div class="grid-2">
          <div class="scroll">{{ scenario_table|safe }}</div>
          <img src="{{ scenario_plot }}" alt="Test senaryolari risk grafigi">
        </div>
      </section>
    </div>
  </main>

  <script>
    const form = document.getElementById("risk-form");
    let submitTimer = null;
    form.querySelectorAll("input").forEach((input) => {
      input.addEventListener("change", () => {
        clearTimeout(submitTimer);
        submitTimer = setTimeout(() => form.submit(), 220);
      });
    });
  </script>
</body>
</html>
"""


def parse_number(name: str, default: float, minimum: float, maximum: float) -> float:
    raw_value = request.args.get(name, default)
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def fig_to_uri(fig) -> str:
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def plot_variable(variable_key: str, current_value: Optional[float] = None) -> str:
    variable = VARIABLES[variable_key]
    fig, ax = plt.subplots(figsize=(7.6, 3.1))
    for label in variable.labels:
        ax.plot(variable.universe, variable.sets[label], linewidth=2, label=LABELS_TR[label])
        if current_value is not None:
            degree = membership_degree(variable, label, current_value)
            ax.scatter([current_value], [degree], s=38)
    if current_value is not None:
        ax.axvline(current_value, color="#111827", linestyle="--", linewidth=1.5)
    ax.set_title(f"{variable.name} uyelik fonksiyonlari")
    ax.set_xlabel(f"{variable.name} ({variable.unit})")
    ax.set_ylabel("Uyelik derecesi")
    ax.set_ylim(-0.03, 1.05)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper right")
    fig.tight_layout()
    return fig_to_uri(fig)


def plot_output(result: Dict[str, object]) -> str:
    risk_variable = VARIABLES["risk"]
    fig, ax = plt.subplots(figsize=(8.4, 3.45))
    for label in risk_variable.labels:
        ax.plot(
            risk_variable.universe,
            risk_variable.sets[label],
            linestyle="--",
            linewidth=1.8,
            label=f"{LABELS_TR[label]} risk",
        )
    ax.fill_between(
        risk_variable.universe,
        result["aggregated_output"],
        color="#2563eb",
        alpha=0.28,
        label="Birlesik cikti alani",
    )
    ax.axvline(
        result["risk_score"],
        color="#dc2626",
        linewidth=2.4,
        label=f"Centroid = {result['risk_score']:.2f}",
    )
    ax.set_title("Durulastirma: agirlik merkezi (centroid)")
    ax.set_xlabel("Risk skoru")
    ax.set_ylabel("Uyelik derecesi")
    ax.set_ylim(-0.03, 1.05)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper right")
    fig.tight_layout()
    return fig_to_uri(fig)


def activation_chart(active_rules: List[Dict[str, object]]) -> str:
    fig, ax = plt.subplots(figsize=(8.2, 3.2))
    top_rules = active_rules[:10]
    labels = [f"Kural {item['id']}" for item in top_rules]
    values = [item["activation"] for item in top_rules]
    ax.bar(labels, values, color="#0891b2")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Aktivasyon")
    ax.set_title("En aktif kurallar")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig_to_uri(fig)


def scenario_chart(rows: List[Dict[str, object]]) -> str:
    fig, ax = plt.subplots(figsize=(8.4, 3.4))
    ax.bar([str(row["Senaryo"]) for row in rows], [float(row["Risk Skoru"]) for row in rows], color="#7c3aed")
    ax.set_ylabel("Risk skoru")
    ax.set_ylim(0, 100)
    ax.set_title("Test senaryolari risk karsilastirmasi")
    ax.tick_params(axis="x", rotation=18)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig_to_uri(fig)


def table_html(rows: Iterable[Dict[str, object]], columns: Optional[List[str]] = None) -> str:
    rows = list(rows)
    if not rows:
        return "<p class='muted'>Kayit yok.</p>"
    columns = columns or list(rows[0].keys())
    header = "".join(f"<th>{column}</th>" for column in columns)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f"<td>{row.get(column, '')}</td>" for column in columns) + "</tr>"
    return f"<table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table>"


@app.route("/")
def index():
    income = parse_number("income", 52, 0, 100)
    credit_score = parse_number("credit_score", 650, 0, 1000)
    debt_ratio = parse_number("debt_ratio", 42, 0, 100)
    result = evaluate(income, credit_score, debt_ratio)

    active_rows = [
        {
            "Kural No": item["id"],
            "Kural": item["rule"],
            "Cikti": LABELS_TR[item["risk"]],
            "Aktivasyon": f"{float(item['activation']):.3f}",
        }
        for item in result["active_rules"]
    ]
    output_rows = [
        {"Risk etiketi": LABELS_TR[label], "Uyelik derecesi": f"{value:.3f}"}
        for label, value in result["output_degrees"].items()
    ]
    rule_rows = [
        {
            "Kural No": rule.id,
            "Gelir": LABELS_TR[rule.income],
            "Kredi Notu": LABELS_TR[rule.credit_score],
            "Borc/Gelir": LABELS_TR[rule.debt_ratio],
            "Cikti Risk": LABELS_TR[rule.risk],
            "IF-THEN": rule.text,
        }
        for rule in RULES
    ]
    scenario_rows = evaluate_scenarios()
    for row in scenario_rows:
        row["Baskin Cikti"] = LABELS_TR[row["Baskin Cikti"]]

    return render_template_string(
        TEMPLATE,
        income=int(income),
        credit_score=int(credit_score),
        debt_ratio=int(debt_ratio),
        result=result,
        labels=LABELS_TR,
        active_rules=result["active_rules"],
        output_plot=plot_output(result),
        income_plot=plot_variable("income", income),
        credit_plot=plot_variable("credit_score", credit_score),
        debt_plot=plot_variable("debt_ratio", debt_ratio),
        risk_plot=plot_variable("risk", float(result["risk_score"])),
        activation_plot=activation_chart(result["active_rules"]) if result["active_rules"] else "",
        scenario_plot=scenario_chart(scenario_rows),
        output_table=table_html(output_rows),
        active_rule_table=table_html(active_rows),
        rule_table=table_html(rule_rows),
        scenario_table=table_html(scenario_rows),
    )


if __name__ == "__main__":
    app.run(debug=True)
