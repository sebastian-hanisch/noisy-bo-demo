# Verrauschte Auswertungen: empfehlen, wiederholen, gemeinsame Zufallszahlen – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-noisy-bo-demo.streamlit.app/)** -->

Drittes Stück der **Bayessche-Optimierung-Linie** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“.
Es setzt [bayes-opt-demo](https://github.com/sebastian-hanisch/bayes-opt-demo) und [bo-modell-demo](https://github.com/sebastian-hanisch/bo-modell-demo) fort: dort war der
Auswertungsfehler ein Parameter des Modells, hier ist er die Hauptfrage. Im Unterschied zu den Fall-Demos zeigt die Demo ein einziges Verfahren an einem wachsenden Beispiel.

## Warum dieses Problem

Eine Simulation liefert nie **den** Wert einer Einstellung, sondern einen Wert, der um ihn streut. Drei Entscheidungen, die bei exakten Auswertungen keine Fragen sind, werden damit
zur Hauptsache: **Welche Einstellung empfiehlt man?** (die mit der besten Beobachtung hat oft nur Glück), **lohnt es, eine Einstellung mehrfach auszuwerten?** (ein Lauf mehr an
derselben Stelle gegen eine Einstellung weniger) und **helfen gemeinsame Zufallszahlen?** (Unterschiede zwischen Einstellungen werden genauer, aber alle teilen denselben Fehler).

## Befunde aus der Vorarbeit

Die Phase-0-Messreihe der Linie (Hartmann6 mit Rauschen, Terminal) hatte nahegelegt: Wiederholen schadet, die „Glückstreffer“-These sei nicht belegt, gemeinsame Zufallszahlen
könnten helfen. Diese Demo prüft das neu und **vollständig gepaart**; die Glückstreffer-Frage ist hier eine **Messung** (Beobachtung minus Wahrheit der empfohlenen Einstellung).

## Modell

- **Ersatzmodell:** Gauß-Prozess mit Matérn-5/2-Kern, Längenmaße, Signal- und Rauschvarianz gelernt; Auswahl nach erwarteter Verbesserung (bester Mittelwert an den Beobachtungen
  als Maßstab); Startdesign 5 zufällige Einstellungen.
- **Wiederholungen:** bei k Wiederholungen werden `Budget // k` verschiedene Einstellungen gewählt und je k-mal ausgewertet; das Modell sieht das Mittel (und lernt die kleinere
  Rauschvarianz σ²/k mit).
- **Empfehlungsregel:** „beste Beobachtung“ (die Einstellung mit dem kleinsten gemittelten Wert) oder „bester Mittelwert des Modells“ an den ausgewerteten Einstellungen.
- **Landschaften:** Branin auf 31 × 31 mit Gauß-Rauschen (5, 20); die Terminal-Scheibe (Plätze am Stapel × Tempo des Stapels, 12 × 17) mit zwei Tabellen **echter Simulationen** (30
  Wiederholungen je Einstellung und Lauflänge 3 000 bzw. 15 000 Lkw): unabhängige Seeds und **gemeinsame Seeds** (Wiederholung r aller Einstellungen nutzt denselben Seed).
- **Wahrheit:** Mittel zweier Läufe à 100 000 Lkw je Einstellung (aus `bayes-opt-demo`). Das Terminal: 33 Lkw je Stunde, Platzgrenze am Stapel, Kosten je Stunde aus Geräten,
  Stellplätzen und Wartezeit (Annahmen der Demo, wie in `bayes-opt-demo`).
- Formeln im 📐-Expander, Kern in `nbo_algorithm.py`.

## Methodik

1. **Live:** ein Lauf mit gewählter Regel, Wiederholungszahl und Zufallszahlen-Modus gegen Zufall und Basis.
2. **Studie** (vorgerechnet, `generate_study.py`): 8 Varianten (Zufall, Basis, Mittelwert-Regel, 2/3/5 Wiederholungen, gemeinsame Zufallszahlen, gemeinsame Zufallszahlen mit 3
   Wiederholungen), je 20 feste Läufe, vier Rauschstufen (Branin 5 und 20; Terminal 3 000 und 15 000 Lkw), Prüfpunkte 10/20/30 Auswertungen. Alle Varianten **teilen je Seed** das
   Startdesign: der Vergleich mit der Basis ist **gepaart**.
3. **Urteil:** zweiseitiger Vorzeichentest über die Läufe mit Unterschied (Gleichstände zählen nicht), ohne Korrektur für mehrere Vergleiche; Niveau 0,05.
4. **Optimismus:** beobachteter Wert der empfohlenen Einstellung minus ihr wahrer Wert, Mittel über die 20 Läufe nach 30 Auswertungen.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`. „Regret“ = wahrer Wert der Empfehlung minus bester Wert der Landschaft; Median über 20 feste Läufe, nach 30 Auswertungen.

| Frage | Befund |
|---|---|
| Wie sehr täuscht die beste Beobachtung? | Die beste Beobachtung der Basis liegt im Mittel **zu schön**: Branin mit Rauschen 5 um **8,3**, mit Rauschen 20 um **38**; Terminal mit 3 000 Lkw um **21 EUR/h**, mit 15 000 Lkw um **3,8 EUR/h**. Mit 5 Wiederholungen schrumpft das auf 0,3 bzw. 3,5 (Branin) und +2,2 EUR/h (Terminal 3 000). |
| Lohnt es, Einstellungen mehrfach auszuwerten? | **Nein, es schadet.** Branin, Rauschen 5: Regret **1,5** (Basis) gegen **2,5** (2×), **2,3** (3×), **5,6** (5×), in 16, 15 bzw. 17 von 20 Läufen schlechter. Terminal: Basis **12,1** bzw. **6,1 EUR/h** gegen 30 bis 42 bzw. 24 bis 39 EUR/h bei Wiederholungen. Bei **Rauschen 20** (Branin) ist kein Unterschied nachweisbar. |
| Empfehlung nach Mittelwert des Modells | **Nie nachweisbar besser** als die beste Beobachtung. Sie halbiert den Optimismus (Branin, Rauschen 20: 16 statt 38), senkt den Regret aber nicht; am Terminal (15 000 Lkw) bei 20 Auswertungen sogar schlechter (0 gegen 6 Läufe). |
| Gemeinsame Zufallszahlen | Terminal mit kurzen Läufen (3 000 Lkw): bei **20 Auswertungen** besser als unabhängige (**15 gegen 3** Läufe, Median −6 EUR/h, p < 0,01); bei 30 Auswertungen und bei 15 000 Lkw **nicht nachweisbar**. Der Optimismus fällt auf **+0,4 EUR/h**: die Beobachtung entspricht der Wahrheit. |
| Gemeinsame Zufallszahlen mit Wiederholungen | **Schlechter** als die Basis (Terminal, beide Lauflängen): die Wiederholungen mitteln gemeinsame Fehler nicht weg. |
| BO gegen Zufall am Terminal mit kurzen Läufen | Bei **20 Auswertungen** ist die Basis **nicht besser** als der Zufall (Regret 26,2 gegen 15,6 EUR/h). |

## Ehrliche Grenzen

- **Die Wiederholungen sind hier gleichmäßig verteilt.** Adaptive Verfahren (Ranking und Selection, OCBA) geben den aussichtsreichen Kandidaten mehr Läufe; das ist nicht
  geprüft, und das Ergebnis „Wiederholen schadet“ gilt für **gleichmäßiges** Wiederholen.
- **Das Modell lernt ein Rauschen für alle Einstellungen.** Am Terminal streuen kurze Läufe bei Last viel stärker als bei Leerlauf.
- **Gemeinsame Zufallszahlen sind ein Seed je Wiederholung und nur am Terminal geprüft.** Am Branin addiert gemeinsames Gauß-Rauschen nur eine Konstante.
- **„Kein Unterschied nachweisbar“ heißt nicht „kein Unterschied“.** Mit 20 Läufen und starkem Rauschen fehlt die Teststärke (Branin, Rauschen 20).
- **Rund ein Dutzend Vergleiche je Tabelle ohne Korrektur.** Einzelne p-Werte knapp unter 0,05 können Zufall sein; belastbar sind die gehäuften Befunde (Wiederholungen schaden
  in drei von vier Rauschstufen).
- **Die Wahrheit ist ein Mittel aus 200 000 Lkw**, selbst mit kleinem Restfehler; Regrets unter etwa 1 EUR/h sind nicht aussagekräftig.
- **Eigene Implementierung** (Kandidatenmenge, drei feste Startpunkte der Hyperparameter-Suche): Zahlen anderer Bibliotheken können abweichen.

## Verifikation

- **Kern:** Kern und erwartete Verbesserung von Hand, Wiederholungen und Budget in Auswertungen, Empfehlungsregeln (`tests/test_algorithm.py`).
- **Orakel** (`tests/test_oracle_noisy_bo.py`, anderer Rechenweg):
  - Gauß-Prozess-Vorhersage gegen **scikit-learn**; EI gegen **numerische Integration**.
  - **Auswahlverzerrung** gegen die Ordnungsstatistik: Mittel des Kleinsten von 30 unabhängigen Normalwerten gegen das numerisch integrierte Erwartungswertintegral (−2,043 σ); mit
    Wiederholungen sinkt sie wie 1/√m.
  - Eine Zelle der Tabelle mit gemeinsamen Seeds wird mit dem **Simulator** neu gerechnet; die Streuung von Unterschieden zwischen Nachbarn ist dort kleiner als bei unabhängigen Seeds.
  - **Vorzeichentest** gegen die Binomialverteilung von Hand (9 von 10: p = 22/1024).
- **Zahlen im README:** `tests/test_claims.py`.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an Minimum und Maximum) und Footer-Test.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App (Skelett nach DEMO-PLAYBOOK §2) |
| `nbo_algorithm.py` | Kern: Gauß-Prozess, erwartete Verbesserung, Suche mit Wiederholungen, Empfehlungsregeln |
| `nbo_scenario.py`, `nbo_benchmarks.py` | Landschaften (Branin mit Rauschen, Terminal-Tabellen) |
| `nbo_terminal.py`, `nbo_network.py`, `nbo_formulas.py` | Terminal-Simulator (Kopie aus `jackson-network-demo`), nur für Tabellengenerator und Orakel |
| `nbo_evaluation.py` | Läufe, Optimismus, gepaarte Statistik, Studienauswertung |
| `nbo_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `nbo_presets.py` | Permalink (Begrenzen/Einrasten), Presets, Zufalls-Seed-Button |
| `nbo_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `nbo_pdf_export.py` | PDF-Auswertung (fpdf2) |
| `generate_crn_table.py`, `precomputed_crn.json` | Tabelle mit gemeinsamen Zufallszahlen |
| `generate_study.py`, `precomputed_study.json` | Studie (8 Varianten, 20 Läufe, vier Rauschstufen) |
| `precomputed_slice.json` | Wahrheit und unabhängige Wiederholungen (aus `bayes-opt-demo`) |
| `requirements.txt`, `requirements-dev.txt` | Laufzeit bzw. Laufzeit plus pytest und scikit-learn |
| `tests/` | Einheiten, Orakel, Behauptungen, Presets, Landschaften, AppTest, Footer |

## Bewusst nicht umgesetzt

- **Ranking und Selection, OCBA, Wissensgradient:** adaptive Verteilung der Läufe auf die Kandidaten.
- **Rauschmodelle, die vom Ort abhängen** (heteroskedastische Gauß-Prozesse).
- **Korrektur für mehrere Vergleiche** (Holm, Bonferroni).

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy, SciPy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
