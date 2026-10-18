import pptx
from pptx.oxml.ns import qn

prs = pptx.Presentation("RDC3_EdgeShield_Final.pptx")
print("=== VERIFYING RDC3_EdgeShield_Final.pptx ===\n")

# 1. Slides 11-15 Decor
print("--- 1. Checking Decor on Slides 11-15 ---")
for s_idx in range(10, 15):
    slide = prs.slides[s_idx]
    title_sh = [sh for sh in slide.shapes if sh.has_text_frame and sh.top < 1500000][0]
    title = title_sh.text_frame.text.strip()
    pics = [sh for sh in slide.shapes if sh.shape_type == pptx.enum.shapes.MSO_SHAPE_TYPE.PICTURE]
    decor_pics = [p for p in pics if p.width == 4118443 and p.height == 3654183]
    broken = [sh for sh in slide.shapes if sh.shape_type == pptx.enum.shapes.MSO_SHAPE_TYPE.FREEFORM]
    print(f"Slide {s_idx+1} ('{title[:30]}...'): decor_pics={len(decor_pics)}, broken_freeform={len(broken)}")
    assert len(decor_pics) == 2, f"Slide {s_idx+1} expected 2 decor pictures, got {len(decor_pics)}"
    assert len(broken) == 0, f"Slide {s_idx+1} still has broken freeforms"

# 2. Slide 18 Title & Body
print("\n--- 2. Checking Slide 18 (Conclusion) Layout ---")
s18 = prs.slides[17]
title_sh = s18.shapes[0]
body_sh = s18.shapes[1]
print(f"Title: '{title_sh.text_frame.text.strip()}', top={title_sh.top}, h={title_sh.height}, w={title_sh.width}")
print(f"Body: top={body_sh.top}, h={body_sh.height}, paragraphs={len(body_sh.text_frame.paragraphs)}")
clearance = body_sh.top - (title_sh.top + title_sh.height)
print(f"Clearance between Title and Body: {clearance} dxa ({clearance/914400:.2f} inches)")
assert clearance > 300000, "Collision still exists between title and body!"

# 3. Slide 4 Table font size
print("\n--- 3. Checking Slide 4 Table Font Sizes ---")
s4 = prs.slides[3]
tbl = [sh for sh in s4.shapes if sh.has_table][0].table
for r in range(len(tbl.rows)):
    sizes = []
    for c in range(len(tbl.columns)):
        cell = tbl.cell(r, c)
        run_sz = cell.text_frame.paragraphs[0].runs[0].font.size.pt if cell.text_frame.paragraphs[0].runs else "no_run"
        sizes.append(f"C{c}:{run_sz}")
    print(f"  Row {r}: {', '.join(sizes)}")
assert tbl.cell(1, 1).text_frame.paragraphs[0].runs[0].font.size.pt == 20.0

# 4. Slides 7, 8, 9, 10 Bullet Formatting
print("\n--- 4. Checking Bullet Formatting on Slides 7, 8, 9, 10 ---")
for s_idx in [6, 7, 8, 9]:
    slide = prs.slides[s_idx]
    title = slide.shapes[0].text_frame.text.strip()
    body = slide.shapes[1]
    bullets = []
    for p_idx, p in enumerate(body.text_frame.paragraphs):
        pPr = p._p.find(qn('a:pPr'))
        buChar = pPr.find(qn('a:buChar')) if pPr is not None else None
        char = buChar.get('char') if buChar is not None else "NONE"
        bullets.append(f"p{p_idx}(lvl{p.level})")
        assert buChar is not None, f"Slide {s_idx+1} paragraph {p_idx} missing bullet char!"
    print(f"Slide {s_idx+1} ('{title[:25]}...'): bullets_count={len(bullets)}")

# 5. Slide 16 Timeline Table vs Title
print("\n--- 5. Checking Slide 16 (Timeline) Separation ---")
s16 = prs.slides[15]
title_16 = s16.shapes[0]
tbl_16 = s16.shapes[3]
print(f"Title: '{title_16.text_frame.text.strip()}', top={title_16.top}, h={title_16.height}, w={title_16.width}")
print(f"Table: top={tbl_16.top}, h={tbl_16.height}")
gap_16 = tbl_16.top - (title_16.top + title_16.height)
print(f"Clearance between Title and Table: {gap_16} dxa ({gap_16/914400:.2f} inches)")
assert gap_16 > 300000, "Table is still colliding with Title on Slide 16!"

# 6. Slide 19 References List
print("\n--- 6. Checking Slide 19 Single Column References ---")
s19 = prs.slides[18]
title_19 = s19.shapes[0]
ref_boxes = [sh for sh in s19.shapes if sh.has_text_frame and sh != title_19]
print(f"Reference text boxes count: {len(ref_boxes)}")
assert len(ref_boxes) == 1, f"Expected exactly 1 text box for single-column list, got {len(ref_boxes)}"
ref_box = ref_boxes[0]
print(f"Box dims: left={ref_box.left}, top={ref_box.top}, w={ref_box.width}, h={ref_box.height}")
print(f"Paragraphs count: {len(ref_box.text_frame.paragraphs)}")
assert len(ref_box.text_frame.paragraphs) == 25, f"Expected 25 references, got {len(ref_box.text_frame.paragraphs)}"
print(f"First ref: {ref_box.text_frame.paragraphs[0].text[:60]}")
print(f"Last ref: {ref_box.text_frame.paragraphs[24].text[:60]}")

print("\n>>> ALL VERIFICATION CHECKS PASSED PERFECTLY! <<<")
