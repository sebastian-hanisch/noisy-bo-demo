"""Verrauschte Auswertungen: empfehlen, wiederholen, gemeinsame Zufallszahlen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Drittes Stück der Linie Bayessche Optimierung. Wenn jede Auswertung streut, wird aus drei Nebenfragen eine Hauptfrage: Welche Einstellung empfiehlt man am Ende, lohnt es, eine
Einstellung mehrfach auszuwerten, und helfen gemeinsame Zufallszahlen?

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import nbo_constants as C
import nbo_evaluation as ev
from nbo_evaluation import Choice, Settings, analyse
from nbo_pdf_export import build_pdf
from nbo_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from nbo_visualization import VARIANT_LABEL, build_convergence_chart, build_optimism_chart, build_variant_chart

st.set_page_config(page_title="Verrauschte Auswertungen – Sebastian Hanisch", layout="wide")


def de(x, nd=2):
    return f"{x:,.{nd}f}".replace(",", " ").replace(".", ",")


@st.cache_data(show_spinner=False)
def _analysis(settings, choice, kind):
    return analyse(settings, choice, kind)


st.title("🔊 Verrauschte Auswertungen: empfehlen, wiederholen, gemeinsame Zufallszahlen")
st.markdown(
    """
Eine Simulation liefert nie **den** Wert einer Einstellung, sondern einen Wert, der um ihn streut. Das ändert drei Dinge, die bei exakten Auswertungen keine Frage sind.
**Erstens die Empfehlung:** die Einstellung mit der besten *Beobachtung* ist oft die mit dem größten Glück; wie sehr sie täuscht, lässt sich messen. **Zweitens die
Wiederholung:** ein Lauf mehr an derselben Stelle macht sie sicherer, aber es gibt dafür eine Einstellung weniger auszuprobieren. **Drittens die Zufallszahlen:** rechnet man alle
Einstellungen mit **denselben** Zufallszahlen, streuen die *Unterschiede* zwischen ihnen weniger als die Werte selbst. Die Demo prüft jede dieser Entscheidungen gegen eine
einfache Basis, mit 20 gepaarten Läufen je Variante. Sie ist das dritte Stück der Linie **Bayessche Optimierung**.

Weiter unten: vier Experimente (**🔬**), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("Die drei Entscheidungen", expanded=True):
    st.markdown(
        """
| Entscheidung | Was sie festlegt | Varianten |
|---|---|---|
| **Empfehlungsregel** | Welche der ausgewerteten Einstellungen am Ende als Ergebnis gilt. | beste Beobachtung (Basis) · bester Mittelwert des Ersatzmodells an den ausgewerteten Einstellungen |
| **Wiederholungen** | Wie oft jede ausgewählte Einstellung ausgewertet und gemittelt wird, bei gleichem Gesamtbudget. | 1 (Basis) · 2 · 3 · 5 |
| **Gemeinsame Zufallszahlen** | Ob alle Einstellungen eines Laufs mit denselben Zufallszahlen simuliert werden (nur Terminal, dort gibt es echte Simulationen). | nein (Basis) · ja |

Verglichen wird immer mit der **Basis**: Ersatzmodell mit erwarteter Verbesserung, jede Einstellung einmal, Empfehlung = beste Beobachtung.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
cols = st.columns(len(C.PRESETS))
for col, name in zip(cols, C.PRESETS):
    with col:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Die Landschaft**")
    kind = st.radio("Landschaft", C.KINDS, format_func=lambda k: C.KIND_LABELS[k], key="kind_radio")
    n = st.slider("Auswertungen (Simulationsläufe)", *bounds("n_slider"), key="n_slider", step=1, help="Das Gesamtbudget, auch bei Wiederholungen.")
    noise = st.select_slider("Rauschen (Branin)", C.BRANIN_NOISES, key="noise_select", format_func=lambda z: C.NOISE_LABEL[z],
                             help="Standardabweichung des Gauß-Rauschens auf jeder Auswertung der Branin-Landschaft.")
    trucks = st.select_slider("Länge eines Laufs (Terminal)", C.TRUCK_CHOICES, key="trucks_select", format_func=lambda t: C.TRUCKS_LABEL[t],
                              help="Kurze Läufe sind billig, aber streuen stark; lange sind ruhiger. Beide Tabellen enthalten je 30 echte Wiederholungen je Einstellung.")
    st.markdown("**Die Entscheidungen**")
    rule = st.radio("Empfehlungsregel", C.RULES, format_func=lambda r: C.RULE_LABELS[r], key="rule_select")
    repeats = st.select_slider("Wiederholungen je Einstellung", C.REPEAT_CHOICES, key="repeats_select",
                               help="Jede ausgewählte Einstellung wird so oft ausgewertet und gemittelt; das Gesamtbudget bleibt gleich.")
    crn = st.checkbox("Gemeinsame Zufallszahlen (Terminal)", key="crn_check", disabled=(kind != "terminal"),
                      help="Nur Terminal: alle Einstellungen werden mit denselben Zufallszahlen simuliert. Bei Branin addiert gemeinsames Rauschen nur eine Konstante.")
    seed = st.number_input("Zufalls-Seed des Laufs", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neuen Lauf generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"kind_radio": kind, "n_slider": int(n), "noise_select": float(noise), "trucks_select": int(trucks), "rule_select": rule, "repeats_select": int(repeats),
                   "crn_check": bool(crn), "seed_input": int(seed)})

settings = Settings(n=int(n), noise=float(noise), trucks=int(trucks), seed=int(seed))
choice = Choice(rule=rule, repeats=int(repeats), crn=bool(crn) and kind == "terminal")
a = _analysis(settings, choice, kind)
reg = ev.final_regret(a)
unit = " EUR/h" if kind == "terminal" else ""

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
st.caption(f"Landschaft: **{C.KIND_LABELS[kind]}**. Basis und Wahl teilen Seed und Startdesign; die Zufallsreihe der Auswertungen ist je Modus gleich lang und reproduzierbar.")
m = st.columns(3)
m[0].metric("Zufall", f"{de(reg['random'])}{unit}", help="Regret: wahrer Wert der empfohlenen Einstellung minus bester Wert der Landschaft. 0 wäre die beste Einstellung.")
m[1].metric("Basis", f"{de(reg['base'])}{unit}", delta=f"{reg['base'] - reg['random']:+.2f} gegen Zufall".replace(".", ","), delta_color="inverse")
m[2].metric("Gewählt", f"{de(reg['choice'])}{unit}", delta=f"{reg['choice'] - reg['base']:+.2f} gegen Basis".replace(".", ","), delta_color="inverse")
st.plotly_chart(build_convergence_chart(a), width="stretch", key="convergence_chart")
st.download_button("📄 Auswertung als PDF", data=build_pdf(a, choice), file_name="verrauschte_auswertungen.pdf", mime="application/pdf", key="pdf_button")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie sehr täuscht die beste Beobachtung?")
b, c = a.runs["base"], a.runs["choice"]
st.info(
    f"In diesem Lauf lag die beste Beobachtung der Basis bei **{de(b.y[b.idx.index(b.rec)])}{unit}**, die wahren Kosten dieser Einstellung bei **{de(a.truth.reshape(-1)[b.rec])}{unit}**: "
    f"Unterschied **{de(b.optimism)}{unit}** ({'die Beobachtung war zu schön' if b.optimism < 0 else 'die Beobachtung war zu schlecht'}). "
    f"Die gewählte Variante: Beobachtung minus Wahrheit {de(c.optimism)}{unit}."
)
st.caption("Ein einzelner Lauf zeigt nur, was bei diesem Seed geschah. Experiment 1 mittelt über 20 feste Läufe.")

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

level_noise = float(noise) if kind == "branin" else None
level_trucks = int(trucks) if kind == "terminal" else None
table, opt = ev.variant_table(kind, level_noise, level_trucks)
keys_all = ["random", "base", "rule_mean", "rep2", "rep3", "rep5"] + (["crn", "crn_rep3"] if kind == "terminal" else [])
unit_eur = kind == "terminal"
level_label = f"Rauschen {C.NOISE_LABEL[float(noise)]}" if kind == "branin" else C.TRUCKS_LABEL[int(trucks)]
cp = st.select_slider("Prüfpunkt (Auswertungen insgesamt)", C.CHECKPOINTS, value=C.CHECKPOINTS[-1], key="cp_select", help="An welcher Zahl von Auswertungen die Varianten verglichen werden.")

st.subheader("🔬 Experiment 1: Wie sehr täuscht die beste Beobachtung?")
st.caption(f"Landschaft und Rauschstufe wie in der Seitenleiste ({level_label}); mittlerer Unterschied zwischen dem beobachteten und dem wahren Wert der empfohlenen Einstellung nach "
           f"{C.CHECKPOINTS[-1]} Auswertungen, 20 feste Läufe. Negativ heißt: die Beobachtung war zu schön.")
opt_by = {k: table[k]["optimism"] for k in keys_all if k not in ("random",)}
st.plotly_chart(build_optimism_chart(opt_by), width="stretch", key="optimism_chart")
st.info(
    f"Die beste Beobachtung der **Basis** lag im Mittel um **{de(abs(opt_by['base']))}{' EUR/h' if unit_eur else ''}** zu schön. "
    + ("Jede Wiederholung mittelt Rauschen weg: mit 5 Wiederholungen sind es " + f"{de(abs(opt_by['rep5']))}{' EUR/h' if unit_eur else ''}. " if "rep5" in opt_by else "")
    + "Diese Verzerrung entsteht, weil man unter vielen verrauschten Werten den kleinsten auswählt; sie ist **kein Fehler des Modells**, sondern der Auswahl."
)


def paired_table(keys, title):
    rows = []
    for k in keys:
        s = ev.paired_stats(kind, k, cp, level_noise, level_trucks)
        rows.append(f"| {VARIANT_LABEL[k]} | {s['better']} | {s['worse']} | {s['equal']} | {de(s['median_diff'])} | {de(s['p'], 3)} | {ev.verdict_of(s)} |")
    st.markdown(f"**{title}** (gepaart gegen die Basis, 20 Läufe; Differenz = Variante minus Basis, negativ ist besser):\n\n"
                "| Variante | besser | schlechter | gleich | Median der Differenz | p | Urteil |\n|---|---|---|---|---|---|---|\n" + "\n".join(rows))
    return {k: ev.verdict_of(ev.paired_stats(kind, k, cp, level_noise, level_trucks)) for k in keys}


st.subheader("🔬 Experiment 2: Lohnt es, Einstellungen mehrfach auszuwerten?")
st.caption(f"Gleiches Gesamtbudget: bei k Wiederholungen werden nur ein k-tel so viele verschiedene Einstellungen ausprobiert. Prüfpunkt {cp} Auswertungen, {level_label}.")
st.plotly_chart(build_variant_chart(table, ["random", "base", "rep2", "rep3", "rep5"], cp, unit_eur), width="stretch", key=f"rep_chart_{cp}")
v2 = paired_table(["rep2", "rep3", "rep5"], "Wiederholungen")
if all(v == "schlechter" for v in v2.values()):
    st.info("**Jede Wiederholung schadet**, und je mehr, desto mehr: Das Ersatzmodell mittelt das Rauschen über benachbarte Einstellungen schon selbst; die Wiederholung verschenkt Läufe.")
elif any(v == "besser" for v in v2.values()):
    st.info("Wiederholungen helfen hier in mindestens einer Variante; die Tabelle zeigt in welcher.")
else:
    st.info("Keine Wiederholungs-Variante ist nachweisbar besser, keine eindeutig schlechter: bei 20 Läufen und dieser Streuung ist der Unterschied nicht zu trennen.")

st.subheader("🔬 Experiment 3: Welche Einstellung empfiehlt man?")
st.caption("Beste Beobachtung (Basis) gegen den besten Mittelwert des Ersatzmodells an den ausgewerteten Einstellungen.")
st.plotly_chart(build_variant_chart(table, ["base", "rule_mean"], cp, unit_eur), width="stretch", key=f"rule_chart_{cp}")
v3 = paired_table(["rule_mean"], "Empfehlungsregel")
st.info(
    {"besser": "Der Mittelwert des Modells ist hier die bessere Empfehlung: er glättet das Glück der besten Einzelbeobachtung.",
     "schlechter": "Der Mittelwert des Modells ist hier **schlechter**: Das Modell glättet auch echte Spitzen und Klippen weg, und eine einzelne gute Beobachtung wäre die richtige gewesen.",
     "kein Unterschied nachweisbar": "Kein nachweisbarer Unterschied zwischen beiden Regeln bei diesem Prüfpunkt."}[v3["rule_mean"]]
)

st.subheader("🔬 Experiment 4: Helfen gemeinsame Zufallszahlen?")
if kind == "terminal":
    st.caption(f"Alle Einstellungen eines Laufs werden mit denselben Zufallszahlen simuliert (Tabelle echter Simulationen, {C.TRUCKS_LABEL[int(trucks)]}).")
    st.plotly_chart(build_variant_chart(table, ["base", "crn", "rep3", "crn_rep3"], cp, unit_eur), width="stretch", key=f"crn_chart_{cp}")
    v4 = paired_table(["crn", "crn_rep3"], "Gemeinsame Zufallszahlen")
    st.info(
        "Gemeinsame Zufallszahlen sind in dieser Studie "
        + ("**nachweisbar hilfreich**." if v4["crn"] == "besser" else "**nachweisbar schädlich**." if v4["crn"] == "schlechter" else "nicht nachweisbar anders als unabhängige Zufallszahlen.")
        + " Ihr Vorteil ist, dass Unterschiede zwischen Einstellungen genauer werden; ihr Preis ist, dass **alle** Werte denselben Zufallsfehler teilen: das Optimum der gemeinsamen Zufallszahlen "
        "kann daneben liegen."
    )
else:
    st.info("Für Branin gibt es hier nichts zu prüfen: gemeinsames Gauß-Rauschen addiert auf jede Einstellung dieselbe Zahl und ändert keine Rangfolge. Wählen Sie das Terminal.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Das Rauschen ist gleichmäßig** | Am Terminal streuen kurze Läufe bei Last viel stärker als bei Leerlauf; das Modell lernt **ein** Rauschen für alle Einstellungen. | Rauschmodelle, die vom Ort abhängen |
| **Das Rauschen ist unabhängig** | Gemeinsame Zufallszahlen machen es abhängig über Einstellungen hinweg: der Mittelwert der Beobachtungen ist dann ein Stichprobenfehler, den **alle** Einstellungen teilen. | Mehrere unabhängige Zufallsreihen |
| **Wiederholungen sind gleichmäßig verteilt** | Hier bekommt jede Einstellung gleich viele. Adaptive Verfahren (Ranking und Selection, OCBA) geben den Kandidaten Läufe, bei denen es sich lohnt. | Ranking und Selection |
| **20 Läufe reichen** | Bei starkem Rauschen fehlt die Teststärke: „kein Unterschied nachweisbar“ heißt nicht „kein Unterschied“. | Mehr Läufe |
| **Zwei Landschaften stehen für die Praxis** | Branin ist glatt, die Terminal-Scheibe ein flaches Tal mit Klippe. | Eigene Messung |
    """
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Beobachtung.** Wertung einer Einstellung $x$: $y = f(x) + \varepsilon$, $\varepsilon$ unabhängig mit Mittel 0 und Varianz $\sigma^2$. Mit $m$ Wiederholungen ist
das Mittel $\bar y$ ein Wert mit Varianz $\sigma^2/m$; das Ersatzmodell lernt diese Rauschvarianz mit.

**Optimismus der besten Beobachtung.** Wählt man $\hat x = \arg\min_i \bar y_i$, dann ist

$$\mathbb{E}\bigl[\bar y_{\hat x} - f(\hat x)\bigr] \le 0$$

weil $\hat x$ gerade die Einstellung mit dem kleinsten Fehler $\bar y_i - f(x_i)$ begünstigt (Auswahlverzerrung). Die Demo misst diesen Wert; er sinkt in der Beobachtung mit
$\sigma/\sqrt m$.

**Gemeinsame Zufallszahlen.** Für zwei Einstellungen $x, x'$ mit Zufallszahlen $\omega$:

$$\operatorname{Var}\bigl[\hat f(x;\omega) - \hat f(x';\omega)\bigr] = \operatorname{Var}\hat f(x) + \operatorname{Var}\hat f(x') - 2\operatorname{Cov}\bigl(\hat f(x), \hat f(x')\bigr)$$

Mit gemeinsamen $\omega$ ist die Kovarianz positiv, die Streuung des **Unterschieds** sinkt. Den Mittelwert verschiebt es nicht: der Fehler $\hat f(x;\omega) - f(x)$ ist für ein
festes $\omega$ von Einstellung zu Einstellung gekoppelt, aber nicht null.

**Empfehlung nach Mittelwert.** Mit dem Gauß-Prozess $\mu(x) = k(x, X)(K + \sigma_n^2 I)^{-1}y$ ist $\hat x = \arg\min_{x_i \in X} \mu(x_i)$ die Einstellung mit dem kleinsten
geglätteten Wert.

**Literatur.** C. E. Rasmussen, C. K. I. Williams (2006), *Gaussian Processes for Machine Learning*, MIT Press; zur Auswahlverzerrung beim Optimieren verrauschter Werte
J. E. Smith, R. L. Winkler (2006), *The Optimizer's Curse*, Management Science (Auswahlverzerrung bei der Optimierung über verrauschte Schätzungen; die Übertragung auf diese Demo ist eine eigene Anwendung).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
