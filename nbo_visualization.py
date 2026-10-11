"""Plotly-Abbildungen (alle Achsen fest, damit Touch-Scrollen auf der Seite nicht am Diagramm hängen bleibt)."""

import plotly.graph_objects as go

import nbo_constants as C

VARIANT_LABEL = {
    "random": "Zufall", "base": "Basis (beste Beobachtung, einmal)", "rule_mean": "bester Mittelwert des Modells", "rep2": "2 Wiederholungen je Einstellung",
    "rep3": "3 Wiederholungen", "rep5": "5 Wiederholungen", "crn": "gemeinsame Zufallszahlen", "crn_rep3": "gemeinsame Zufallszahlen, 3 Wiederholungen",
}


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
        fig.add_hline(y=opt, line_dash="dash", line_color=C.COLOR_NEXT, annotation_text="wahres Optimum", annotation_position="bottom right")
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
