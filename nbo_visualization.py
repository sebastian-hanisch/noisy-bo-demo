"""Plotly-Abbildungen (alle Achsen fest, damit Touch-Scrollen auf der Seite nicht am Diagramm hängen bleibt)."""

import math
import plotly.graph_objects as go

import nbo_constants as C

VARIANT_LABEL = {
    "random": "Zufall", "base": "Basis (beste Beobachtung, einmal)", "rule_mean": "bester Mittelwert des Modells", "rep2": "2 Wiederholungen je Einstellung",
    "rep3": "3 Wiederholungen", "rep5": "5 Wiederholungen", "crn": "gemeinsame Zufallszahlen", "crn_rep3": "gemeinsame Zufallszahlen, 3 Wiederholungen",
}


def _ref_line(fig, value, text, position, axis, log=True, **line_kwargs):
    """Referenzlinie mit Beschriftung auf einer logarithmischen Achse: die Linie liegt auf dem Datenwert, die Beschriftung braucht log10 des Werts
    (add_hline und add_vline setzen beide auf denselben Wert, die Beschriftung sitzt dann falsch und dehnt die Achse); log=False für lineare Achsen."""
    if log and not value > 0.0:
        return
    pos = math.log10(value) if log else value
    top, left = "top" in position, "left" in position
    if axis == "y":
        fig.add_hline(y=value, **line_kwargs)
        if text:
            fig.add_annotation(xref="paper", yref="y", x=0 if left else 1, y=pos, text=text, showarrow=False, xanchor="left" if left else "right", yanchor="bottom" if top else "top")
    else:
        fig.add_vline(x=value, **line_kwargs)
        if text:
            fig.add_annotation(xref="x", yref="paper", x=pos, y=1 if top else 0, text=text, showarrow=False, xanchor="right" if left else "left", yanchor="top" if top else "bottom")


def _fixed(fig, **layout):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=-0.25), **layout)
    return fig


def build_convergence_chart(a):
    """Wahrer Wert der Empfehlung nach t Auswertungen für Zufall, Basis und Wahl (Regret; bei Terminal wahre Kosten). Wiederholungen: eine Stufe je abgeschlossener Einstellung."""
    fig = go.Figure()
    opt = a.optimum[2]
    spec = (("random", "Zufall", C.COLOR_RANDOM, 1.8), ("base", "Basis", C.COLOR_BASE, 2.5), ("choice", "Gewählt", C.COLOR_CHOICE, 3.0))
    for key, name, col, w in spec:
        run = a.runs[key]
        rep = run.repeats
        ts = [(p + 1) * rep for p in range(len(run.truth_by_points))]
        tr = run.truth_by_points
        y = [max(v - opt, 1e-3) for v in tr] if a.kind == "branin" else [min(v, 3000) for v in tr]
        fig.add_trace(go.Scatter(x=ts, y=y, mode="lines", name=name, line=dict(color=col, width=w, dash="dot" if key == "base" else "solid"), line_shape="hv"))
    fig.update_xaxes(title_text="Auswertungen (Simulationsläufe)")
    if a.kind == "branin":
        fig.update_yaxes(title_text="Regret der Empfehlung (log)", type="log")
    else:
        _ref_line(fig, opt, "wahres Optimum", "bottom right", "y", line_dash="dash", line_color=C.COLOR_NEXT)
        fig.update_yaxes(title_text="Wahre Kosten der Empfehlung (EUR/h)", range=[opt * 0.98, opt * 1.2])
    return _fixed(fig, height=340)


def build_variant_chart(table, keys, checkpoint, unit_eur=False):
    """Median des Regrets je Variante an einem Prüfpunkt (Balken) und das schlechteste Zehntel der Läufe (Raute)."""
    fig = go.Figure()
    names = [VARIANT_LABEL[k] for k in keys]
    vals = [max(table[k][checkpoint]["median"], 1e-2) for k in keys]
    q90 = [max(table[k][checkpoint]["q90"], 1e-2) for k in keys]
    fig.add_trace(go.Bar(x=names, y=vals, marker_color=[C.COLOR_RANDOM if k == "random" else C.COLOR_BASE if k == "base" else C.COLOR_CHOICE for k in keys], name="Median",
                         hovertemplate="%{x}<br>Median %{y:.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=names, y=q90, mode="markers", marker=dict(symbol="diamond", size=9, color=C.COLOR_BAD), name="schlechtestes Zehntel der Läufe (90-%-Quantil)"))
    fig.update_yaxes(title_text="Regret nach %d Auswertungen (log)%s" % (checkpoint, " in EUR/h" if unit_eur else ""), type="log")
    return _fixed(fig, height=360)


def build_optimism_chart(opt_by_variant):
    """Mittlerer Optimismus der besten Beobachtung (Beobachtung minus Wahrheit der empfohlenen Einstellung; negativ = zu schön) je Variante."""
    keys = list(opt_by_variant)
    fig = go.Figure(go.Bar(x=[VARIANT_LABEL[k] for k in keys], y=[opt_by_variant[k] for k in keys], marker_color=[C.COLOR_BAD if opt_by_variant[k] < 0 else C.COLOR_CHOICE for k in keys],
                           hovertemplate="%{x}<br>%{y:.2f}<extra></extra>"))
    fig.update_yaxes(title_text="Beobachtung minus Wahrheit der Empfehlung")
    return _fixed(fig, height=300)
