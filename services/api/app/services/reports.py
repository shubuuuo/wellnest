"""PDF reports built with reportlab (pure Python, nothing else to install)."""
from datetime import datetime, timezone
from io import BytesIO
from xml.sax.saxutils import escape

from fastapi import Response
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BRAND = colors.HexColor("#991b1b")
GREY = colors.HexColor("#6b7280")
LINE = colors.HexColor("#d1d5db")
SOFT = colors.HexColor("#f3f4f6")
BAND_COLORS = {"low": colors.HexColor("#15803d"), "moderate": colors.HexColor("#b45309"), "high": colors.HexColor("#b91c1c")}
BAND_TEXT = {"low": "Lower estimated risk", "moderate": "Moderate estimated risk", "high": "Higher estimated risk"}
BAND_RANGE = {"low": "below 30%", "moderate": "30% to below 70%", "high": "70% or above"}
TREND_TEXT = {"up": "higher than the previous check", "down": "lower than the previous check",
              "flat": "about the same as the previous check", "first": "first check for this dataset"}

DISCLAIMER = (
    "This report is an estimate produced by a machine-learning model for educational purposes. It is not a medical "
    "diagnosis and must not be used to start, change or stop any treatment. Please consult a qualified clinician "
    "about any health concern."
)

PAGE_W = A4[0]
CONTENT_W = PAGE_W - 36 * mm

S_TITLE = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=BRAND, spaceAfter=2)
S_SUB = ParagraphStyle("sub", fontName="Helvetica", fontSize=9, leading=12, textColor=GREY, spaceAfter=10)
S_H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=12, leading=15, spaceBefore=12, spaceAfter=5)
S_BODY = ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=13)
S_CELL = ParagraphStyle("cell", fontName="Helvetica", fontSize=9, leading=11.5)
S_CELLB = ParagraphStyle("cellb", parent=S_CELL, fontName="Helvetica-Bold")
S_NOTE = ParagraphStyle("note", fontName="Helvetica-Oblique", fontSize=8.5, leading=11, textColor=GREY)


def _p(text: object, style: ParagraphStyle = S_CELL) -> Paragraph:
    return Paragraph(escape(str(text)), style)


def _fmt_dt(value: datetime | None) -> str:
    if value is None:
        return "not recorded"
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%d %b %Y, %H:%M UTC")


def _pct(probability: float) -> str:
    return f"{probability * 100:.1f}%"


def _field(name: str) -> str:
    return name.replace("_", " ").strip().capitalize()


def _value(value: object) -> str:
    return f"{value:g}" if isinstance(value, float) else str(value)


def _grid(data: list[list], widths: list[float], header: bool = True) -> Table:
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), SOFT))
    table.setStyle(TableStyle(style))
    return table


def _facts(rows: list[tuple[str, str]]) -> Table:
    data = [[_p(k, S_CELLB), _p(v)] for k, v in rows]
    table = _grid(data, [45 * mm, CONTENT_W - 45 * mm], header=False)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), SOFT)]))
    return table


def _inputs_table(inputs: dict) -> Table:
    data = [[_p("Field", S_CELLB), _p("Value", S_CELLB)]] + [[_p(_field(k)), _p(_value(v))] for k, v in inputs.items()]
    return _grid(data, [75 * mm, CONTENT_W - 75 * mm])


def _inputs_compact(inputs: dict) -> Table:
    """Two field/value pairs per row, to keep long forms short."""
    items = [(_field(k), _value(v)) for k, v in inputs.items()]
    rows = []
    for i in range(0, len(items), 2):
        pair = items[i:i + 2]
        row = []
        for k, v in pair:
            row += [_p(k, S_CELLB), _p(v)]
        while len(row) < 4:
            row.append(_p(""))
        rows.append(row)
    w = CONTENT_W
    table = _grid(rows, [w * 0.27, w * 0.23, w * 0.27, w * 0.23], header=False)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), SOFT), ("BACKGROUND", (2, 0), (2, -1), SOFT)]))
    return table


def _disclaimer() -> Table:
    table = Table([[Paragraph(f"<b>Important.</b> {escape(DISCLAIMER)}", S_BODY)]], colWidths=[CONTENT_W])
    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, BRAND), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef2f2")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _timeline_chart(points: list[dict]) -> Drawing:
    points = points[-20:]
    drawing = Drawing(CONTENT_W, 52 * mm)
    chart = VerticalBarChart()
    chart.x, chart.y, chart.width, chart.height = 12 * mm, 12 * mm, CONTENT_W - 18 * mm, 34 * mm
    chart.data = [[round(p["probability"] * 100, 1) for p in points]]
    chart.categoryAxis.categoryNames = [p["created_at"].strftime("%d %b") for p in points]
    chart.categoryAxis.labels.fontSize = 6.5
    chart.categoryAxis.labels.angle = 35
    chart.categoryAxis.labels.boxAnchor = "ne"
    chart.categoryAxis.labels.dy = -2
    chart.valueAxis.valueMin, chart.valueAxis.valueMax, chart.valueAxis.valueStep = 0, 100, 25
    chart.valueAxis.labels.fontSize = 7
    chart.valueAxis.labelTextFormat = "%d%%"
    chart.bars.strokeColor = None
    chart.barWidth = 6
    for i, p in enumerate(points):
        chart.bars[(0, i)].fillColor = BAND_COLORS[p["risk_band"]]
    drawing.add(chart)
    return drawing


def _build(story: list, footer_text: str) -> bytes:
    buffer = BytesIO()

    def decorate(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(BRAND)
        canvas.rect(0, A4[1] - 9 * mm, PAGE_W, 9 * mm, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(18 * mm, A4[1] - 6 * mm, "WellNest")
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(PAGE_W - 18 * mm, A4[1] - 6 * mm, "Cancer risk assessment")
        canvas.setStrokeColor(LINE)
        canvas.line(18 * mm, 14 * mm, PAGE_W - 18 * mm, 14 * mm)
        canvas.setFillColor(GREY)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(18 * mm, 10 * mm, footer_text)
        canvas.drawRightString(PAGE_W - 18 * mm, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=18 * mm, bottomMargin=20 * mm, title="WellNest risk report", author="WellNest")
    doc.build(story, onFirstPage=decorate, onLaterPages=decorate)
    return buffer.getvalue()


def prediction_report_pdf(name: str, email: str, p: dict, metrics: dict | None) -> bytes:
    """One saved check as a report. p is a dict from history.prediction_dict()."""
    band = p["risk_band"]
    hex_band = BAND_COLORS[band].hexval()[2:]
    now = datetime.now(timezone.utc)
    story: list = [
        Paragraph("Cancer Risk Assessment Report", S_TITLE),
        Paragraph("An educational estimate from a machine-learning model, not a diagnosis.", S_SUB),
        _facts([
            ("Name", name), ("Email", email), ("Report ID", p["id"]),
            ("Date of check", _fmt_dt(p["created_at"])), ("Dataset", p["dataset_label"]),
            ("Model used", f"{p['model_name']} (trained {_fmt_dt(p['model_trained_at'])})"),
        ]),
        Paragraph("Result", S_H2),
    ]
    result = Table([[
        Paragraph(f'<font size="26" color="#{hex_band}"><b>{_pct(p["probability"])}</b></font><br/>'
                  f'<font size="8.5" color="#6b7280">estimated probability</font>', S_BODY),
        Paragraph(f'<font size="12" color="#{hex_band}"><b>{BAND_TEXT[band]}</b></font><br/>'
                  f'<font size="8.5" color="#6b7280">risk band: {BAND_RANGE[band]}</font>', S_BODY),
    ]], colWidths=[CONTENT_W * 0.4, CONTENT_W * 0.6])
    result.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, BAND_COLORS[band]), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8), ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story += [result, Paragraph("Values entered", S_H2), _inputs_table(p["inputs"])]

    if metrics:
        story.append(Paragraph("About the model", S_H2))
        story.append(Paragraph(
            f"Scores of the model on {metrics['test_rows']:,} held-out test records it never trained on "
            "(the model's current version):" if metrics.get("test_rows") else
            "Scores of the model on held-out test records it never trained on (the model's current version):", S_BODY))
        story.append(Spacer(1, 4))
        head = [_p(h, S_CELLB) for h in ("Accuracy", "Precision", "Recall", "F1 score", "ROC-AUC")]
        vals = [_p(f"{metrics[k]:.3f}") for k in ("accuracy", "precision", "recall", "f1", "roc_auc")]
        story.append(_grid([head, vals], [CONTENT_W / 5] * 5))

    story.append(Paragraph("How to read this result", S_H2))
    story.append(Paragraph(
        "The percentage is the probability the model assigns to the cancer class, based only on the values listed "
        "above. Below 30% is shown as lower, 30% to below 70% as moderate and 70% or above as higher estimated risk. "
        "A lower value does not rule cancer out and a higher value does not mean cancer is present.", S_BODY))
    story += [Spacer(1, 10), _disclaimer()]
    return _build(story, f"WellNest report {p['id'][:8]} - generated {_fmt_dt(now)}")


def health_report_pdf(name: str, email: str, summary: dict, predictions: list[dict]) -> bytes:
    """A person's whole history. summary comes from history.build_summary(), predictions are newest first."""
    now = datetime.now(timezone.utc)
    story: list = [
        Paragraph("Personal Health Risk Report", S_TITLE),
        Paragraph("A summary of every risk check saved in WellNest. Educational estimates, not diagnoses.", S_SUB),
        _facts([
            ("Name", name), ("Email", email), ("Report generated", _fmt_dt(now)),
            ("Checks saved", str(summary["total_checks"])),
            ("First check", _fmt_dt(summary["first_check_at"])), ("Latest check", _fmt_dt(summary["last_check_at"])),
        ]),
    ]
    if summary["total_checks"] == 0:
        story += [Spacer(1, 10), Paragraph("No risk checks have been saved yet.", S_BODY), Spacer(1, 10), _disclaimer()]
        return _build(story, f"WellNest health report - generated {_fmt_dt(now)}")

    counts = summary["band_counts"]
    story.append(Paragraph("Overview", S_H2))
    story.append(_grid(
        [[_p("Lower estimated risk", S_CELLB), _p("Moderate estimated risk", S_CELLB), _p("Higher estimated risk", S_CELLB)],
         [_p(counts["low"]), _p(counts["moderate"]), _p(counts["high"])]], [CONTENT_W / 3] * 3))

    for d in summary["datasets"]:
        latest = d["latest"]
        change = ""
        if d["change"] is not None:
            change = f" ({d['change'] * 100:+.1f} percentage points)"
        block = [
            Paragraph(escape(d["label"]), S_H2),
            Paragraph(
                f"Latest result: <b>{_pct(latest['probability'])}</b> ({BAND_TEXT[latest['risk_band']].lower()}) "
                f"on {_fmt_dt(latest['created_at'])}. This is {TREND_TEXT[d['trend']]}{escape(change)}. "
                f"Checks for this dataset: {d['checks']}.", S_BODY),
            Spacer(1, 4),
            _timeline_chart(d["points"]),
            Paragraph("Bars show the estimated probability of each check, oldest to newest (newest 20 shown); "
                      "green is lower, amber moderate and red higher risk.", S_NOTE),
        ]
        story.append(KeepTogether(block))
        story += [Paragraph("Values entered at the latest check", S_BODY), Spacer(1, 3), _inputs_compact(latest["inputs"])]

    shown = predictions[:200]
    story.append(Paragraph("All checks", S_H2))
    rows = [[_p(h, S_CELLB) for h in ("Date", "Dataset", "Probability", "Risk band", "Model")]]
    for p in shown:
        rows.append([_p(_fmt_dt(p["created_at"])), _p(p["dataset_label"]), _p(_pct(p["probability"])),
                     _p(BAND_TEXT[p["risk_band"]].replace(" estimated risk", "")), _p(p["model_name"])])
    w = CONTENT_W
    story.append(_grid(rows, [w * 0.25, w * 0.22, w * 0.13, w * 0.13, w * 0.27]))
    if len(predictions) > len(shown):
        story.append(Paragraph(f"Showing the newest {len(shown)} of {len(predictions)} checks.", S_NOTE))
    story += [Spacer(1, 12), _disclaimer()]
    return _build(story, f"WellNest health report - generated {_fmt_dt(now)}")


def pdf_response(content: bytes, filename: str) -> Response:
    return Response(content=content, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})