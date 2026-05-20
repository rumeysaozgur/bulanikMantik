"""Fuzzy credit risk controller used by the Flask interface.

The system evaluates a consumer loan applicant with three crisp inputs:
monthly income, credit score, and debt-to-income ratio. It returns a crisp
risk score in the range 0-100 by using Mamdani inference and centroid
defuzzification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np

try:
    import skfuzzy as _skfuzzy
except Exception:
    _skfuzzy = None


Label = str
MembershipSet = Dict[Label, np.ndarray]
USING_SCIKIT_FUZZY = _skfuzzy is not None


def trimf(x: np.ndarray, abc: List[float]) -> np.ndarray:
    if _skfuzzy is not None:
        return _skfuzzy.trimf(x, abc)

    a, b, c = abc
    y = np.zeros_like(x, dtype=float)
    if b != a:
        left = (x >= a) & (x <= b)
        y[left] = (x[left] - a) / (b - a)
    if c != b:
        right = (x >= b) & (x <= c)
        y[right] = np.maximum(y[right], (c - x[right]) / (c - b))
    y[x == b] = 1.0
    return np.clip(y, 0, 1)


def trapmf(x: np.ndarray, abcd: List[float]) -> np.ndarray:
    if _skfuzzy is not None:
        return _skfuzzy.trapmf(x, abcd)

    a, b, c, d = abcd
    y = np.zeros_like(x, dtype=float)
    if b != a:
        rising = (x >= a) & (x <= b)
        y[rising] = (x[rising] - a) / (b - a)
    else:
        y[x <= b] = 1.0
    plateau = (x >= b) & (x <= c)
    y[plateau] = 1.0
    if d != c:
        falling = (x >= c) & (x <= d)
        y[falling] = np.maximum(y[falling], (d - x[falling]) / (d - c))
    else:
        y[x >= c] = 1.0
    return np.clip(y, 0, 1)


def interp_membership(universe: np.ndarray, membership: np.ndarray, value: float) -> float:
    if _skfuzzy is not None:
        return float(_skfuzzy.interp_membership(universe, membership, value))
    return float(np.interp(value, universe, membership))


def centroid(universe: np.ndarray, membership: np.ndarray) -> float:
    if _skfuzzy is not None:
        return float(_skfuzzy.defuzz(universe, membership, "centroid"))

    area = float(np.trapz(membership, universe))
    if area == 0:
        return 50.0
    moment = float(np.trapz(membership * universe, universe))
    return moment / area


@dataclass(frozen=True)
class Variable:
    name: str
    unit: str
    universe: np.ndarray
    sets: MembershipSet
    labels: Tuple[Label, ...]


@dataclass(frozen=True)
class Rule:
    id: int
    income: Label
    credit_score: Label
    debt_ratio: Label
    risk: Label

    @property
    def text(self) -> str:
        return (
            f"IF gelir {self.income} AND kredi notu {self.credit_score} "
            f"AND borc/gelir orani {self.debt_ratio} THEN risk {self.risk}"
        )


def build_variables() -> Dict[str, Variable]:
    """Create universes and membership functions for all fuzzy variables."""

    income_x = np.arange(0, 101, 1)
    credit_x = np.arange(0, 1001, 1)
    debt_x = np.arange(0, 101, 1)
    risk_x = np.arange(0, 101, 1)

    variables = {
        "income": Variable(
            name="Aylik Gelir",
            unit="bin TL",
            universe=income_x,
            labels=("dusuk", "orta", "yuksek"),
            sets={
                "dusuk": trapmf(income_x, [0, 0, 15, 35]),
                "orta": trimf(income_x, [25, 50, 75]),
                "yuksek": trapmf(income_x, [65, 85, 100, 100]),
            },
        ),
        "credit_score": Variable(
            name="Kredi Notu",
            unit="puan",
            universe=credit_x,
            labels=("dusuk", "orta", "yuksek"),
            sets={
                "dusuk": trapmf(credit_x, [0, 0, 350, 550]),
                "orta": trimf(credit_x, [450, 650, 800]),
                "yuksek": trapmf(credit_x, [700, 850, 1000, 1000]),
            },
        ),
        "debt_ratio": Variable(
            name="Borc/Gelir Orani",
            unit="%",
            universe=debt_x,
            labels=("dusuk", "orta", "yuksek"),
            sets={
                "dusuk": trapmf(debt_x, [0, 0, 20, 35]),
                "orta": trimf(debt_x, [25, 45, 65]),
                "yuksek": trapmf(debt_x, [55, 75, 100, 100]),
            },
        ),
        "risk": Variable(
            name="Kredi Risk Skoru",
            unit="puan",
            universe=risk_x,
            labels=("dusuk", "orta", "yuksek"),
            sets={
                "dusuk": trapmf(risk_x, [0, 0, 20, 40]),
                "orta": trimf(risk_x, [30, 50, 70]),
                "yuksek": trapmf(risk_x, [60, 80, 100, 100]),
            },
        ),
    }
    return variables


VARIABLES = build_variables()


RULES: Tuple[Rule, ...] = (
    Rule(1, "dusuk", "dusuk", "dusuk", "orta"),
    Rule(2, "dusuk", "dusuk", "orta", "yuksek"),
    Rule(3, "dusuk", "dusuk", "yuksek", "yuksek"),
    Rule(4, "dusuk", "orta", "dusuk", "orta"),
    Rule(5, "dusuk", "orta", "orta", "orta"),
    Rule(6, "dusuk", "orta", "yuksek", "yuksek"),
    Rule(7, "dusuk", "yuksek", "dusuk", "dusuk"),
    Rule(8, "dusuk", "yuksek", "orta", "orta"),
    Rule(9, "dusuk", "yuksek", "yuksek", "orta"),
    Rule(10, "orta", "dusuk", "dusuk", "orta"),
    Rule(11, "orta", "dusuk", "orta", "orta"),
    Rule(12, "orta", "dusuk", "yuksek", "yuksek"),
    Rule(13, "orta", "orta", "dusuk", "dusuk"),
    Rule(14, "orta", "orta", "orta", "orta"),
    Rule(15, "orta", "orta", "yuksek", "orta"),
    Rule(16, "orta", "yuksek", "dusuk", "dusuk"),
    Rule(17, "orta", "yuksek", "orta", "dusuk"),
    Rule(18, "orta", "yuksek", "yuksek", "orta"),
    Rule(19, "yuksek", "dusuk", "dusuk", "orta"),
    Rule(20, "yuksek", "dusuk", "orta", "orta"),
    Rule(21, "yuksek", "dusuk", "yuksek", "yuksek"),
    Rule(22, "yuksek", "orta", "dusuk", "dusuk"),
    Rule(23, "yuksek", "orta", "orta", "dusuk"),
    Rule(24, "yuksek", "orta", "yuksek", "orta"),
    Rule(25, "yuksek", "yuksek", "dusuk", "dusuk"),
    Rule(26, "yuksek", "yuksek", "orta", "dusuk"),
    Rule(27, "yuksek", "yuksek", "yuksek", "orta"),
)


def _membership_degree(variable: Variable, label: Label, value: float) -> float:
    return interp_membership(variable.universe, variable.sets[label], value)


def membership_degree(variable: Variable, label: Label, value: float) -> float:
    return _membership_degree(variable, label, value)


def fuzzify(inputs: Dict[str, float]) -> Dict[str, Dict[Label, float]]:
    """Return membership degrees for every input variable and label."""

    degrees: Dict[str, Dict[Label, float]] = {}
    for key in ("income", "credit_score", "debt_ratio"):
        variable = VARIABLES[key]
        degrees[key] = {
            label: _membership_degree(variable, label, inputs[key])
            for label in variable.labels
        }
    return degrees


def evaluate(
    income: float,
    credit_score: float,
    debt_ratio: float,
) -> Dict[str, object]:
    """Run Mamdani inference and centroid defuzzification."""

    crisp_inputs = {
        "income": float(np.clip(income, 0, 100)),
        "credit_score": float(np.clip(credit_score, 0, 1000)),
        "debt_ratio": float(np.clip(debt_ratio, 0, 100)),
    }
    degrees = fuzzify(crisp_inputs)
    risk_variable = VARIABLES["risk"]
    aggregated = np.zeros_like(risk_variable.universe, dtype=float)
    active_rules: List[Dict[str, object]] = []

    for rule in RULES:
        activation = min(
            degrees["income"][rule.income],
            degrees["credit_score"][rule.credit_score],
            degrees["debt_ratio"][rule.debt_ratio],
        )
        if activation > 0:
            clipped_output = np.minimum(activation, risk_variable.sets[rule.risk])
            aggregated = np.maximum(aggregated, clipped_output)
            active_rules.append(
                {
                    "id": rule.id,
                    "rule": rule.text,
                    "risk": rule.risk,
                    "activation": activation,
                }
            )

    if np.max(aggregated) == 0:
        risk_score = 50.0
    else:
        risk_score = centroid(risk_variable.universe, aggregated)

    output_degrees = {
        label: _membership_degree(risk_variable, label, risk_score)
        for label in risk_variable.labels
    }
    dominant_output = max(output_degrees, key=output_degrees.get)

    return {
        "inputs": crisp_inputs,
        "input_degrees": degrees,
        "active_rules": sorted(
            active_rules, key=lambda item: item["activation"], reverse=True
        ),
        "aggregated_output": aggregated,
        "risk_score": risk_score,
        "output_degrees": output_degrees,
        "dominant_output": dominant_output,
        "interpretation": interpret_risk(risk_score),
    }


def interpret_risk(score: float) -> str:
    if score < 35:
        return "Dusuk risk: basvuru genel olarak olumlu gorunuyor."
    if score < 65:
        return "Orta risk: ek teminat, kefil veya limit azaltimi onerilir."
    return "Yuksek risk: basvuru dikkatli incelenmeli veya reddedilmelidir."


def scenario_rows() -> List[Dict[str, float]]:
    return [
        {
            "Senaryo": "Guclu profil",
            "income": 85,
            "credit_score": 880,
            "debt_ratio": 18,
        },
        {
            "Senaryo": "Dengeli profil",
            "income": 52,
            "credit_score": 650,
            "debt_ratio": 42,
        },
        {
            "Senaryo": "Gelir dusuk, not iyi",
            "income": 24,
            "credit_score": 790,
            "debt_ratio": 32,
        },
        {
            "Senaryo": "Borc yuku fazla",
            "income": 70,
            "credit_score": 720,
            "debt_ratio": 78,
        },
        {
            "Senaryo": "Riskli basvuru",
            "income": 18,
            "credit_score": 390,
            "debt_ratio": 82,
        },
    ]


def evaluate_scenarios(rows: Optional[Iterable[Dict[str, float]]] = None) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []
    for row in rows or scenario_rows():
        result = evaluate(row["income"], row["credit_score"], row["debt_ratio"])
        results.append(
            {
                "Senaryo": row["Senaryo"],
                "Aylik Gelir (bin TL)": row["income"],
                "Kredi Notu": row["credit_score"],
                "Borc/Gelir (%)": row["debt_ratio"],
                "Risk Skoru": round(float(result["risk_score"]), 2),
                "Baskin Cikti": result["dominant_output"],
                "Aktif Kural Sayisi": len(result["active_rules"]),
            }
        )
    return results
