#!/usr/bin/env python3
"""
Build the Stage-1 (mid-presentation) deck as a native .pptx.

Hebrew is right-to-left, set per paragraph via the OOXML attribute a:pPr rtl="1"
(python-pptx has no RTL property). Figures are read from ../figures; the deck is
written to ../presentation. Open in Google Slides / PowerPoint / LibreOffice.

The Hebrew strings below are the slide content and must stay in Hebrew.
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
DIR = str(ROOT / "figures")          # figures produced by make_figures.py
FONT = "Arial"
NAVY, BLUE, INK, GREY = RGBColor(0x1F,0x38,0x64), RGBColor(0x2E,0x86,0xC1), RGBColor(0x22,0x22,0x22), RGBColor(0x60,0x60,0x60)
SW, SH = 13.333, 7.5
LEFT, BODYW = 0.6, 12.13   # align body to header/accent

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(SW), Inches(SH)
BLANK = prs.slide_layouts[6]

def _set(p, align="r", rtl=True):
    pPr = p._p.get_or_add_pPr()
    if rtl: pPr.set("rtl", "1")
    pPr.set("algn", {"r":"r","l":"l","ctr":"ctr"}.get(align,"r"))

def textbox(slide, l, t, w, h, anchor=None):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    if anchor: tf.vertical_anchor = anchor
    return tf

def line(tf, text, size, color=INK, bold=False, align="r", space_after=8, first=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.space_after = Pt(space_after)
    r = p.add_run(); r.text = text
    r.font.size, r.font.bold, r.font.name = Pt(size), bold, FONT
    r.font.color.rgb = color
    _set(p, align)
    return p

def accent(slide, top=1.45):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(LEFT), Inches(top), Inches(BODYW), Inches(0.045))
    s.fill.solid(); s.fill.fore_color.rgb = BLUE; s.line.fill.background(); s.shadow.inherit = False

def header(slide, title):
    line(textbox(slide, LEFT, 0.45, BODYW, 0.95), title, 30, NAVY, bold=True, first=True)
    accent(slide)

def content(title, bullets, lead=None):
    s = prs.slides.add_slide(BLANK); header(s, title)
    tf = textbox(s, LEFT, 1.75, BODYW, 5.3); first = True
    if lead:
        line(tf, lead, 22, BLUE, bold=True, space_after=16, first=True); first = False
    for b in bullets:
        sub = b.startswith("\t")
        line(tf, ("◦  " if sub else "•  ") + b.lstrip("\t"), 17 if sub else 19, INK, space_after=12, first=first)
        first = False
    return s

def fig_slide(title, lead, img, aspect, max_w):
    s = prs.slides.add_slide(BLANK); header(s, title)
    line(textbox(s, LEFT, 1.62, BODYW, 1.15), lead, 19, INK, space_after=0, first=True)
    top = 2.7; avail_h = SH - top - 0.15
    w = min(max_w, avail_h*aspect); h = w/aspect
    s.shapes.add_picture(f"{DIR}/{img}", Inches((SW-w)/2), Inches(top), width=Inches(w), height=Inches(h))
    return s

# ---- Slide 1: title ----
s = prs.slides.add_slide(BLANK)
tf = textbox(s, 1.0, 2.0, 11.33, 3.5, anchor=MSO_ANCHOR.MIDDLE)
line(tf, 'איך מתחרי הרמת-כוח "משחקים" עם המספרים', 40, NAVY, bold=True, align="ctr", space_after=14, first=True)
line(tf, "ניתוח סטטיסטי של OpenPowerlifting - ומה הנתונים חושפים על גבולות הכוח באוכלוסיית המתחרים", 20, GREY, align="ctr", space_after=28)
line(tf, "אדיר אלמקייס · דוד לוין", 22, INK, bold=True, align="ctr", space_after=6)
line(tf, "תאוריה סטטיסטית · פרויקט סוף - מצגת אמצע", 17, GREY, align="ctr")

# ---- Slide 2: research data ----
content("נתוני המחקר", [
    "מקור: OpenPowerlifting - מאגר פתוח של תוצאות תחרויות הרמת-כוח (רישיון CC0).",
    "היקף: כ-3.94 מיליון תוצאות (שורה לכל מתחרה בכל תחרות), 41 משתנים.",
    "משתנים: רציפים - משקל-גוף, משקלי-ניסיון, Total, Dots; קטגוריים - מין, ציוד, פדרציה, מקטע-משקל, Tested.",
    "הנתונים כבר הורדו ועובדו - כל המספרים בהמשך הם תוצאות אמת ראשוניות.",
])

# ---- Slide 3: overview ----
content("עיקרי העבודה", [
    "מתחרה שולט בשני מספרים בלבד: המשקל על המוט (בחירת הניסיונות) ומשקל הגוף (בשקילה).",
    'אנחנו בוחנים איך הוא "משחק" עם שניהם - ומה ניתן ללמוד מכך על גבולות הכוח באוכלוסיית המתחרים.',
], lead="הרעיון: שני המספרים שהמתחרה שולט בהם - והמחיר שהוא משלם עליהם")

# ---- Slide 4: research question ----
content("שאלת החקר", [
    'כיצד מתבטאת בנתונים ההתנהגות ה"מחושבת" של מתחרים - בבחירת המשקל על המוט ובמשקל הגוף?',
    "ומה ניתן ללמוד מכך (וממגבלות הנתונים) על מבנה הכוח וגבולותיו באוכלוסיית המתחרים?",
    "השערות מרכזיות:",
    '\tH1 - משקלי הניסיון אינם רציפים אלא נופלים רק על כפולות של 2.5 ק"ג (רשת הפלטות).',
    '\tH2 - מתחרים "חותכים משקל" כדי לנחות בדיוק מתחת לסף מקטע-המשקל.',
    "\tמשניות: מבנה התפלגות הכוח, וקנה-המידה האלומטרי.",
])

# ---- Slide 5: methods ----
content("שיטות המחקר", [
    "H1 (רשת המשקלים): מודל נראות עם עיגול-רשת (rounded-likelihood MLE) + מבחן יחס-נראות מקונן (GLRT).",
    'H2 (חיתוך-משקל): מבחן אי-רציפות-צפיפות (McCrary) סביב הסף + בדיקות הפרכה - פלצבו, de-heaping, ומינון-תגובה.',
    "כלים תומכים: רגרסיה אלומטרית (מבחן Wald), מתאמים, וערכי-קיצון (EVT).",
    'דגש: בגלל n≈3.9M כמעט הכל "מובהק" - לכן מובילים בגודל-אפקט וברווח-סמך, לא ב-p.',
])

# ---- Slide 6: results (1) - 2.5 kg grid ----
fig_slide('תוצאות ראשוניות (1): רשת ה-2.5 ק"ג',
          'משקלי הניסיון אינם רציפים: 96.2% מתוך 13.4 מיליון ניסיונות יושבים בדיוק על רשת ה-2.5 ק"ג.',
          "fig_quantization.png", 8.2/4.4, 9.5)

# ---- Slide 7: results (2) - weight-cutting ----
fig_slide("תוצאות ראשוניות (2): חיתוך-משקל",
          'מתחת לסף 83 ק"ג (מחלקת IPF) הצטברות בולטת (יחס-לוג +1.92, שורד ניקוי מספרים-עגולים); בנקודת-בקרה שאינה סף (91 ק"ג) אין עודף (≈ -0.21). אינדיקציה ראשונית לחיתוך-משקל; אישוש פורמלי (McCrary, de-heaping) בהמשך.',
          "fig_bunching.png", 9.6/4.3, 11.0)

# ---- Slide 8: extra results - allometry ----
fig_slide("תוצאות נוספות: קנה-מידה אלומטרי",
          'קנה-המידה שונה בין המינים: b≈0.72 (גברים) / 0.49 (נשים) - הנשים הרבה מתחת ל-2/3 האיזומטרי. אומדן ראשוני (OLS); מבחן פורמלי מול 2/3 בהמשך.',
          "fig_allometry.png", 9.0/4.5, 10.0)

# ---- Slide 9: conclusions & wrap-up ----
s = prs.slides.add_slide(BLANK); header(s, "מסקנות ראשוניות וסיכום")
tf = textbox(s, LEFT, 1.75, BODYW, 5.3)
bullets = [
    'שני המספרים שהמתחרה שולט בהם נראים בבירור: רשת ה-2.5 ק"ג (המוט), והצטברות מתחת לספים (משקל גוף).',
    "ההצטברות מתחת לסף שורדת ניקוי-עיגול ונעדרת בנקודת-בקרה - אינדיקציה ראשונית מעודדת (טרם מבוססת).",
    "הצעדים הבאים: מבחן McCrary פורמלי + de-heaping, מבנה התפלגות הכוח, ואומדן תקרת-כוח (EVT).",
    "כל התוצאות יוצגו עם גודל-אפקט, רווחי-סמך, ותיקון לבדיקות מרובות.",
]
for i, b in enumerate(bullets):
    line(tf, "•  " + b, 19, INK, space_after=12, first=(i==0))
line(tf, "תודה! שאלות?", 24, BLUE, bold=True, align="ctr", space_after=0)

out = str(ROOT / "presentation" / "mid_presentation_OpenPowerlifting.pptx")
prs.save(out)
print("saved:", out, "|", len(list(prs.slides)), "slides")
