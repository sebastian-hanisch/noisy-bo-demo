"""PDF-Export der aktuellen Auswertung (fpdf2, Kernschriften; Umlaute sind dort erlaubt, Gedankenstrich und Eurozeichen nicht)."""

from fpdf import FPDF

import nbo_constants as C
import nbo_evaluation as ev


def _num(x, nd=2):
    return f"{x:,.{nd}f}".replace(",", " ").replace(".", ",")


def build_pdf(a, choice):
    """Einseitiger Bericht: Einstellungen, Regret und Optimismus von Zufall, Basis und Wahl. Gibt die Bytes der PDF-Datei zurück."""
    s = a.settings
    reg = ev.final_regret(a)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Verrauschte Auswertungen", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Sebastian Hanisch, Operations Research und Machine Learning", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Einstellungen", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    level = f"Rauschen {_num(s.noise, 0)}" if a.kind == "branin" else f"{s.trucks} Lkw je Auswertung"
    for k, v in (("Landschaft", C.KIND_LABELS[a.kind]), ("Rauschstufe", level), ("Auswertungen", str(s.n)), ("Empfehlungsregel", C.RULE_LABELS[choice.rule]),
                 ("Wiederholungen je Einstellung", str(choice.repeats)), ("Gemeinsame Zufallszahlen", "ja" if choice.crn and a.kind == "terminal" else "nein"),
                 ("Zufalls-Seed", str(s.seed))):
        pdf.cell(70, 6, k)
        pdf.cell(0, 6, v, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Regret der Empfehlung und Optimismus der Beobachtung", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for key, label in (("random", "Zufall"), ("base", "Basis"), ("choice", "Gewählt")):
        pdf.cell(70, 6, label)
        pdf.cell(0, 6, f"Regret {_num(reg[key])}; Beobachtung minus Wahrheit {_num(a.runs[key].optimism)}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 5, "Ein einzelner Lauf zeigt nur, was bei diesem Seed geschah; die Studie der Demo mittelt über 20 feste Läufe.")
    return bytes(pdf.output())
