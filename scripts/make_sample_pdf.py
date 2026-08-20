"""Generate data/manuals/aquaflow-200-manual.pdf: a synthetic sample manual
for the rag-tfm demo corpus. Pure stdlib (raw PDF syntax), no external deps.

Usage: python scripts/make_sample_pdf.py [output_path]
"""

import textwrap

TITLE = "AquaFlow 200 Water Filter Pitcher - User Manual"

SECTIONS = [
    (
        "1. Overview",
        """
The AquaFlow 200 is a countertop water filter pitcher with a 2.5 liter
capacity and a replaceable 3-stage carbon filter cartridge. It removes
chlorine taste and odor, sediment, and reduces trace levels of lead and
mercury. Each filter cartridge is rated for approximately 150 liters or
two months of typical household use, whichever comes first.
""",
    ),
    (
        "2. Setup Instructions",
        """
Before first use, remove the filter cartridge from its plastic wrapping
and soak it in cold water for 15 minutes. Rinse the cartridge under
running tap water for 30 seconds to clear any loose carbon dust. Insert
the cartridge into the funnel housing until it clicks into place. Run
two full pitcher cycles of tap water through the filter and discard
this water before drinking any filtered water, as the first cycles may
contain residual carbon fines.
""",
    ),
    (
        "3. Daily Operation",
        """
Fill the upper reservoir with tap water up to the marked fill line. Do
not use water from an unregulated well or water that has not been
tested for microbiological safety, as the AquaFlow 200 is not certified
to remove bacteria or viruses. A full reservoir takes approximately 8 to
10 minutes to filter completely into the lower pitcher. The lower
pitcher holds 2.5 liters. Do not force the reservoir lid closed while
filtering is in progress, as this can cause overflow.
""",
    ),
    (
        "4. Filter Replacement",
        """
The filter status indicator on the lid turns from green to red when
replacement is due. To replace the cartridge, twist it counterclockwise
a quarter turn and lift it out of the funnel housing. Dispose of the
old cartridge according to local recycling guidelines; do not puncture
or burn it. Follow the same soak-and-rinse procedure from Section 2 for
the new cartridge before reinserting it. Reset the status indicator by
holding the reset button on the lid for 3 seconds until it blinks green
twice.
""",
    ),
    (
        "5. Cleaning and Maintenance",
        """
Wash the pitcher, lid, and reservoir by hand with warm water and mild
dish soap every two weeks. Do not use abrasive scouring pads, as they
can scratch the plastic and harbor bacteria. The pitcher body is not
dishwasher safe; the lid and reservoir top rack are dishwasher safe.
Never immerse the filter cartridge itself in soapy water. Wipe the
cartridge housing with a damp cloth only.
""",
    ),
    (
        "6. Troubleshooting",
        """
If water filters slower than usual, the cartridge may be nearing the
end of its life or may be clogged with sediment; try rinsing it under
running water for one minute. If filtered water has a plastic taste
after setup, repeat the two discard cycles described in Section 2. If
the status indicator does not light up at all, check that the two AAA
batteries in the lid compartment are inserted with correct polarity. If
water leaks from the base, confirm the lower pitcher is fully seated
and the gasket ring is not twisted.
""",
    ),
    (
        "7. Safety Warnings",
        """
Do not use hot or carbonated water in the AquaFlow 200; it is rated for
cold tap water only, between 4 and 30 degrees Celsius. Keep the unit
out of direct sunlight to prevent algae growth in the reservoir. This
product is not a substitute for emergency water disinfection during a
boil-water advisory. Keep small parts, including the filter cartridge
wrapping, away from children.
""",
    ),
]


def esc(s: str) -> str:
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def build_page_content(lines: list[str]) -> bytes:
    ops = ["BT", "/F1 11 Tf", "12 TL", "72 760 Td"]
    for line in lines:
        ops.append(f"({esc(line)}) Tj")
        ops.append("0 -12 Td")
    ops.append("ET")
    return ("\n".join(ops)).encode("latin-1")


def wrap_text() -> list[list[str]]:
    pages: list[list[str]] = []
    current: list[str] = [TITLE, ""]
    max_lines = 58

    def flush():
        nonlocal current
        pages.append(current)
        current = []

    for heading, body in SECTIONS:
        block = [heading, ""]
        for para_line in textwrap.wrap(" ".join(body.split()), width=90):
            block.append(para_line)
        block.append("")
        if len(current) + len(block) > max_lines:
            flush()
            current = []
        current.extend(block)
    if current:
        flush()
    return pages


def build_pdf(pages_lines: list[list[str]]) -> bytes:
    font_obj = 3
    page_obj_ids = []
    content_obj_ids = []
    next_id = 4
    for _ in pages_lines:
        page_obj_ids.append(next_id)
        next_id += 1
        content_obj_ids.append(next_id)
        next_id += 1

    pages_root_id = 2
    catalog_id = 1

    kids = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
    objects_by_id = {}
    objects_by_id[catalog_id] = (
        f"{catalog_id} 0 obj\n<< /Type /Catalog /Pages {pages_root_id} 0 R >>\nendobj\n"
    )
    objects_by_id[pages_root_id] = (
        f"{pages_root_id} 0 obj\n<< /Type /Pages /Kids [{kids}] "
        f"/Count {len(page_obj_ids)} >>\nendobj\n"
    )
    objects_by_id[font_obj] = (
        f"{font_obj} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    )

    for lines, page_id, content_id in zip(pages_lines, page_obj_ids, content_obj_ids, strict=True):
        content_bytes = build_page_content(lines)
        objects_by_id[page_id] = (
            f"{page_id} 0 obj\n<< /Type /Page /Parent {pages_root_id} 0 R "
            f"/Resources << /Font << /F1 {font_obj} 0 R >> >> "
            f"/MediaBox [0 0 612 792] /Contents {content_id} 0 R >>\nendobj\n"
        )
        objects_by_id[content_id] = (
            (f"{content_id} 0 obj\n<< /Length {len(content_bytes)} >>\nstream\n").encode("latin-1")
            + content_bytes
            + b"\nendstream\nendobj\n"
        )

    info_id = next_id
    objects_by_id[info_id] = (
        f"{info_id} 0 obj\n<< /Title ({esc(TITLE)}) "
        "/Subject (Synthetic sample manual generated for the rag-tfm demo corpus; "
        "fictional product, no real-world source, no license restrictions.) "
        "/Producer (rag-tfm make_sample_pdf.py) >>\nendobj\n"
    )
    max_id = info_id

    header = b"%PDF-1.4\n"
    buf = bytearray()
    buf += header
    offsets = {}
    for oid in range(1, max_id + 1):
        offsets[oid] = len(buf)
        obj = objects_by_id[oid]
        buf += obj if isinstance(obj, bytes) else obj.encode("latin-1")

    xref_offset = len(buf)
    buf += f"xref\n0 {max_id + 1}\n".encode("latin-1")
    buf += b"0000000000 65535 f \n"
    for oid in range(1, max_id + 1):
        buf += f"{offsets[oid]:010d} 00000 n \n".encode("latin-1")

    buf += (
        f"trailer\n<< /Size {max_id + 1} /Root {catalog_id} 0 R /Info {info_id} 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF"
    ).encode("latin-1")

    return bytes(buf)


if __name__ == "__main__":
    import sys
    from pathlib import Path

    out_path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/manuals/aquaflow-200-manual.pdf")
    pages = wrap_text()
    pdf_bytes = build_pdf(pages)
    out_path.write_bytes(pdf_bytes)
    print(f"Wrote {out_path} ({len(pdf_bytes)} bytes, {len(pages)} pages)")
