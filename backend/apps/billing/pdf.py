"""PDF bill generation using ReportLab."""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Colours ───────────────────────────────────────────────────────────────────
BLUE = colors.HexColor("#2563EB")
LIGHT_BLUE = colors.HexColor("#EFF6FF")
GRAY = colors.HexColor("#6B7280")
LIGHT_GRAY = colors.HexColor("#F3F4F6")
DARK = colors.HexColor("#111827")
BORDER = colors.HexColor("#E5E7EB")


def _styles():
    return {
        "h1": ParagraphStyle(
            "h1", fontSize=22, fontName="Helvetica-Bold", textColor=BLUE, spaceAfter=2
        ),
        "h2": ParagraphStyle(
            "h2", fontSize=11, fontName="Helvetica-Bold", textColor=DARK, spaceAfter=4
        ),
        "label": ParagraphStyle(
            "label", fontSize=8, fontName="Helvetica", textColor=GRAY, spaceAfter=2
        ),
        "value": ParagraphStyle(
            "value", fontSize=10, fontName="Helvetica", textColor=DARK, spaceAfter=4
        ),
        "value_bold": ParagraphStyle(
            "value_bold", fontSize=10, fontName="Helvetica-Bold", textColor=DARK
        ),
        "right": ParagraphStyle(
            "right", fontSize=10, fontName="Helvetica", textColor=DARK, alignment=TA_RIGHT
        ),
        "right_bold": ParagraphStyle(
            "right_bold", fontSize=10, fontName="Helvetica-Bold", textColor=DARK, alignment=TA_RIGHT
        ),
        "total": ParagraphStyle(
            "total", fontSize=12, fontName="Helvetica-Bold", textColor=BLUE, alignment=TA_RIGHT
        ),
        "footer": ParagraphStyle(
            "footer", fontSize=8, fontName="Helvetica", textColor=GRAY, alignment=TA_CENTER
        ),
        "status": ParagraphStyle(
            "status", fontSize=9, fontName="Helvetica-Bold", textColor=BLUE, alignment=TA_CENTER
        ),
    }


def generate_bill_pdf(bill) -> bytes:
    """Generate a PDF for the given Bill and return as bytes."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    s = _styles()
    story = []
    page_w = A4[0] - 40 * mm  # usable width

    # ── Header ────────────────────────────────────────────────────────────────
    header_data = [
        [
            Paragraph("RentTrack", s["h1"]),
            Paragraph(
                f"BILL #{bill.bill_number}",
                ParagraphStyle(
                    "bn", fontSize=14, fontName="Helvetica-Bold", textColor=DARK, alignment=TA_RIGHT
                ),
            ),
        ]
    ]
    header_table = Table(header_data, colWidths=[page_w * 0.6, page_w * 0.4])
    header_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(header_table)
    story.append(Spacer(1, 2 * mm))

    status_label = bill.get_status_display().upper()
    story.append(Paragraph(f"Status: {status_label}", s["status"]))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=5 * mm))

    # ── From / To ─────────────────────────────────────────────────────────────
    org = bill.organization
    lease = bill.lease
    tenant = lease.tenant

    from_lines = [
        Paragraph("FROM", s["label"]),
        Paragraph(org.name, s["value_bold"]),
        Paragraph(org.primary_email, s["value"]),
    ]
    to_lines = [
        Paragraph("TO", s["label"]),
        Paragraph(
            f"{tenant.first_name} {tenant.last_name}".strip() or tenant.email,
            s["value_bold"],
        ),
        Paragraph(tenant.email, s["value"]),
    ]
    if tenant.phone:
        to_lines.append(Paragraph(str(tenant.phone), s["value"]))

    from_block = [[line] for line in from_lines]
    to_block = [[line] for line in to_lines]

    parties_data = [
        [
            Table(from_block, colWidths=[page_w * 0.45]),
            Table(to_block, colWidths=[page_w * 0.45]),
        ]
    ]
    parties_table = Table(parties_data, colWidths=[page_w * 0.5, page_w * 0.5])
    parties_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(parties_table)
    story.append(Spacer(1, 5 * mm))

    # ── Bill Details ─────────────────────────────────────────────────────────
    bill_type_label = bill.get_bill_type_display()
    details_data = [
        [
            Paragraph("Bill Type", s["label"]),
            Paragraph("Period", s["label"]),
            Paragraph("Issue Date", s["label"]),
            Paragraph("Due Date", s["label"]),
        ],
        [
            Paragraph(bill_type_label, s["value_bold"]),
            Paragraph(
                f"{bill.period_start.strftime('%d %b %Y')} – {bill.period_end.strftime('%d %b %Y')}",
                s["value"],
            ),
            Paragraph(bill.issue_date.strftime("%d %b %Y"), s["value"]),
            Paragraph(bill.due_date.strftime("%d %b %Y"), s["value"]),
        ],
    ]
    col_w = page_w / 4
    details_table = Table(details_data, colWidths=[col_w] * 4)
    details_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GRAY),
                ("BACKGROUND", (0, 1), (-1, 1), LIGHT_BLUE),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(details_table)
    story.append(Spacer(1, 5 * mm))

    # ── Unit Info ─────────────────────────────────────────────────────────────
    unit = lease.unit
    story.append(
        Paragraph(
            f"Unit: {unit.name}, {unit.property.name}",
            ParagraphStyle("unit", fontSize=9, fontName="Helvetica", textColor=GRAY),
        )
    )
    story.append(Spacer(1, 4 * mm))

    # ── Line Items ────────────────────────────────────────────────────────────
    story.append(Paragraph("Line Items", s["h2"]))
    li_header = [
        Paragraph(
            "Description",
            ParagraphStyle("th", fontSize=9, fontName="Helvetica-Bold", textColor=DARK),
        ),
        Paragraph(
            "Qty",
            ParagraphStyle(
                "th_r", fontSize=9, fontName="Helvetica-Bold", textColor=DARK, alignment=TA_RIGHT
            ),
        ),
        Paragraph(
            "Unit Price",
            ParagraphStyle(
                "th_r", fontSize=9, fontName="Helvetica-Bold", textColor=DARK, alignment=TA_RIGHT
            ),
        ),
        Paragraph(
            "Amount",
            ParagraphStyle(
                "th_r", fontSize=9, fontName="Helvetica-Bold", textColor=DARK, alignment=TA_RIGHT
            ),
        ),
    ]
    li_rows = [li_header]
    for item in bill.line_items.all():
        li_rows.append(
            [
                Paragraph(item.description, s["value"]),
                Paragraph(str(item.quantity.normalize()), s["right"]),
                Paragraph(f"₹{item.unit_price:,.2f}", s["right"]),
                Paragraph(f"₹{item.amount:,.2f}", s["right"]),
            ]
        )

    li_table = Table(
        li_rows,
        colWidths=[page_w * 0.5, page_w * 0.14, page_w * 0.18, page_w * 0.18],
    )
    li_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GRAY),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BLUE]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(li_table)
    story.append(Spacer(1, 4 * mm))

    # ── Totals ────────────────────────────────────────────────────────────────
    totals_data = [
        [Paragraph("Subtotal", s["right"]), Paragraph(f"₹{bill.subtotal:,.2f}", s["right"])],
        [Paragraph("Tax", s["right"]), Paragraph(f"₹{bill.tax_amount:,.2f}", s["right"])],
        [
            Paragraph("Total", s["right_bold"]),
            Paragraph(f"₹{bill.total_amount:,.2f}", s["right_bold"]),
        ],
        [Paragraph("Amount Paid", s["right"]), Paragraph(f"₹{bill.amount_paid:,.2f}", s["right"])],
        [Paragraph("Balance Due", s["total"]), Paragraph(f"₹{bill.balance_due:,.2f}", s["total"])],
    ]
    totals_table = Table(totals_data, colWidths=[page_w * 0.75, page_w * 0.25])
    totals_table.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 4), (-1, 4), 1, BLUE),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(totals_table)
    story.append(Spacer(1, 8 * mm))

    # ── QR Code Placeholder ────────────────────────────────────────────────────
    qr_data = [
        [
            Paragraph(
                f"[QR Code — {bill.bill_number}]",
                ParagraphStyle(
                    "qr", fontSize=8, fontName="Helvetica", textColor=GRAY, alignment=TA_CENTER
                ),
            )
        ]
    ]
    qr_table = Table(qr_data, colWidths=[30 * mm], rowHeights=[30 * mm])
    qr_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
            ]
        )
    )
    story.append(qr_table)
    story.append(Spacer(1, 6 * mm))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=3 * mm))
    story.append(
        Paragraph(
            "RentTrack — Automated rent management platform. " "For queries contact your landlord.",
            s["footer"],
        )
    )

    doc.build(story)
    return buffer.getvalue()
