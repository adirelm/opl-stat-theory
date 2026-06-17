#!/usr/bin/env python3
"""
Build the Stage-1 (mid-presentation) deck as a native .pptx.

Hebrew is right-to-left, set per paragraph via the OOXML attribute a:pPr rtl="1"
(python-pptx has no RTL property). Figures from ../figures; deck to ../presentation.
Open in Google Slides / PowerPoint / LibreOffice. Hebrew strings = slide content.
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = str(ROOT / "figures")
FONT = "Arial"
NAVY, BLUE, INK, GREY = RGBColor(0x1F,0x38,0x64), RGBColor(0x2E,0x86,0xC1), RGBColor(0x22,0x22,0x22), RGBColor(0x70,0x70,0x70)
HL = RGBColor(0xC0,0x53,0x1B)
SW, SH = 13.333, 7.5
LEFT, BODYW = 0.6, 12.13

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

def rule(slide, top, l=LEFT, w=BODYW, color=BLUE, h=0.045):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(top), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = color; s.line.fill.background(); s.shadow.inherit = False

def footer(slide):
    n = len(list(prs.slides))
    line(textbox(slide, LEFT, 7.08, BODYW, 0.3), f"תאוריה סטטיסטית · פרויקט סוף · OpenPowerlifting · {n}/9",
         9, GREY, align="r", space_after=0, first=True)

def header(slide, title):
    line(textbox(slide, LEFT, 0.45, BODYW, 0.95), title, 30, NAVY, bold=True, first=True)
    rule(slide, 1.45); footer(slide)

def content(title, bullets, lead=None, lead_size=22):
    s = prs.slides.add_slide(BLANK); header(s, title)
    tf = textbox(s, LEFT, 1.8, BODYW, 5.0, anchor=MSO_ANCHOR.TOP); first = True
    if lead:
        line(tf, lead, lead_size, BLUE, bold=True, space_after=18, first=True); first = False
    for b in bullets:
        sub = b.startswith("\t")
        line(tf, ("◦  " if sub else "•  ") + b.lstrip("\t"), 18 if sub else 19.5, INK, space_after=14, first=first)
        first = False
    return s

def fig_slide(title, lead, img, aspect, max_w):
    s = prs.slides.add_slide(BLANK); header(s, title)
    line(textbox(s, LEFT, 1.6, BODYW, 1.15), lead, 18, INK, space_after=0, first=True)
    top = 2.78; avail_h = 6.95 - top
    w = min(max_w, avail_h*aspect); h = w/aspect
    s.shapes.add_picture(f"{DIR}/{img}", Inches((SW-w)/2), Inches(top), width=Inches(w), height=Inches(h))
    return s

# ---- Slide 1: title (cover identity + hook number) ----
s = prs.slides.add_slide(BLANK)
band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(SW), Inches(0.55))
band.fill.solid(); band.fill.fore_color.rgb = NAVY; band.line.fill.background(); band.shadow.inherit = False
tf = textbox(s, 1.0, 1.9, 11.33, 4.0, anchor=MSO_ANCHOR.TOP)
line(tf, 'איך מתחרי הרמת-כוח "משחקים" עם המספרים', 38, NAVY, bold=True, align="ctr", space_after=10, first=True)
line(tf, "ניתוח סטטיסטי של OpenPowerlifting: מה הנתונים חושפים על גבולות הכוח", 19, GREY, align="ctr", space_after=22)
line(tf, 'פי כ-6.8 יותר מתחרים נשקלים ממש מתחת לסף מחלקת-המשקל מאשר ממש מעליו', 21, HL, bold=True, align="ctr", space_after=26)
line(tf, "אדיר אלמקייס · דוד לוין", 22, INK, bold=True, align="ctr", space_after=6)
line(tf, "תאוריה סטטיסטית · פרויקט סוף · מצגת אמצע", 16, GREY, align="ctr")
rule(s, 6.05, l=4.4, w=4.5)

# ---- Slide 2: research data ----
content("נתוני המחקר", [
    "מקור: OpenPowerlifting, מאגר פתוח של תוצאות תחרויות הרמת-כוח (רישיון CC0).",
    "היקף: כ-3.94 מיליון תוצאות (שורה לכל מתחרה בכל תחרות), 42 משתנים.",
    "משתנים רציפים: משקל-גוף, משקלי-ניסיון, Total, Dots. משתנים קטגוריים: מין, ציוד, פדרציה, קטגוריית-משקל, Tested.",
    "אתגרים וטיפול: אותו מתחרה מופיע בכמה תחרויות (תלות בין שורות), ולכן המבחנים הפורמליים ירוצו עם שורה אחת לכל מתחרה; התוצאות הראשוניות כאן הן ברמת ניסיון בודד. שומרים גרסת-נתונים קבועה לשחזור.",
])

# ---- Slide 3: overview (two-numbers tagline + contribution) ----
content("עיקרי העבודה", [
    "רקע: בהרמת-כוח שלוש הרמות (סקוואט, בנץ', דדליפט), שלושה ניסיונות לכל הרמה, והתחרות בתוך קטגוריות משקל-גוף.",
    "מתחרה שולט בדיוק בשני מספרים: המשקל על המוט (בחירת ניסיונות) ומשקל הגוף (בשקילה).",
    "התרומה: לא רק לתאר, אלא מודל-הסתברות מקורי לרשת-המשקלים, ומבחן-מניפולציה עם נקודת-בקרה וניקוי-עיגול.",
], lead="הרעיון: שני המספרים שהמתחרה שולט בהם, המוט והמאזניים")

# ---- Slide 4: research question + hypotheses ----
content("שאלת החקר", [
    'כיצד מתבטאת בנתונים ההתנהגות ה"מחושבת" של מתחרים בבחירת המשקל על המוט ובמשקל הגוף?',
    "\tH1: משקלי הניסיון אינם רציפים אלא נופלים רק על רשת 2.5 ק\"ג.",
    "\tH2: הצטברות משקל-גוף ממש מתחת לסף קטגוריית-המשקל (עקבי עם חיתוך-משקל).",
    "\tH3: קנה-המידה האלומטרי (כוח מול משקל-גוף) שונה בין המינים.",
    "\tH4 (לעבודה הסופית): כמה מהכוח ניתן לנבא ממשתני-השליטה (משקל, ציוד, מין, גיל)?",
], lead="ארבע השערות, סיפור אחד: H1/H2 הם \"שני המספרים\", H3/H4 הם גבולות-הכוח והניבוי")

# ---- Slide 5: methods (1:1 with results + named course tools + ML) ----
content("שיטות החקר", [
    "H1: מודל נראות עם עיגול-רשת (rounded-likelihood MLE) + מבחן יחס-נראות מוכלל (GLRT, דחיית H0 לערכים גדולים).",
    "H2: מבחן אי-רציפות-צפיפות (McCrary) + מערך-הפרכה (נקודת-בקרה, פלצבו, de-heaping).",
    "H3: רגרסיה log-log + מבחן Wald מול 2/3, עם SE חסין ואיבר-אינטראקציה Sex×log(BW).",
    "H4 (לעבודה הסופית): רגרסיה מרובה + Random Forest (+ סיווג logistic ל-made-weight), הערכה ב-R²/RMSE ו-CV מקובץ לפי-מתחרה.",
    'תיקון להשוואות מרובות: Bonferroni/Holm/Šidák (FWER) + Benjamini-Hochberg (FDR). בגלל n≈3.94M (עוצמה גבוהה → כמעט הכל "מובהק") מדגישים גודל-אפקט ו-CI, לא p.',
], lead_size=20)

# ---- Slide 6: results H1 ----
fig_slide('תוצאות ראשוניות (1): רשת ה-2.5 ק"ג',
          'משקלי הניסיון אינם רציפים: 96.2% מתוך 13.4 מיליון ניסיונות בדיוק על רשת ה-2.5 ק"ג ‎(95% CI [96.19%, 96.21%])‎.',
          "fig_quantization.png", 8.2/4.4, 9.4)

# ---- Slide 7: results H2 ----
fig_slide("תוצאות ראשוניות (2): חיתוך-משקל",
          'מתחת לסף 83 ק"ג (IPF+USAPL, גברים; סכמת-מחלקות אחידה) הצטברות חדה: יחס-לוג לאחר ניקוי-עיגול (כבר הוחל) ‎+1.92 ± 0.04‎, כלומר פי כ-6.8 ממש-מתחת לעומת ממש-מעל. בבקרה שאינה סף (91 ק"ג): ‎−0.21 ± 0.03‎. עקבי עם חיתוך-משקל; אישוש פורמלי (McCrary) בהמשך.',
          "fig_bunching.png", 9.8/4.3, 11.2)

# ---- Slide 8: results H3 (allometry) ----
fig_slide("תוצאות ראשוניות (3): קנה-מידה אלומטרי",
          'קנה-המידה שונה בין המינים: ‎b≈0.72 (R²=0.36)‎ גברים / ‎0.49 (R²=0.19)‎ נשים, מול 2/3 האיזומטרי (רווח-הסמך ל-b צר מאוד, ‎±<0.01‎, בגלל n עצום). ייבדק פורמלית במבחן Wald (SE חסין); ‎b<0.5‎ לנשים הוא אומדן ראשוני, ייתכן אפקט טווח-משקל.',
          "fig_allometry.png", 9.0/4.6, 10.0)

# ---- Slide 9: conclusions + payoff close ----
s = prs.slides.add_slide(BLANK); header(s, "מסקנות ראשוניות וסיכום")
tf = textbox(s, LEFT, 1.75, BODYW, 4.6)
bullets = [
    'שני המספרים שהמתחרה שולט בהם נראים בבירור: רשת ה-2.5 ק"ג (המוט), והצטברות מתחת לספים (משקל גוף).',
    "ההצטברות שורדת ניקוי-עיגול ונעדרת בנקודת-בקרה: אינדיקציה ראשונית מעודדת (טרם מבוססת).",
    "הצעדים הבאים: McCrary פורמלי + הפרכה, אלומטריה (Wald), ומודל ניבוי-כוח (רגרסיה + Random Forest, R²/CV).",
    "כל התוצאות יוצגו עם גודל-אפקט, רווחי-סמך, ותיקון להשוואות מרובות (FWER/FDR).",
]
for i, b in enumerate(bullets):
    line(tf, "•  " + b, 19, INK, space_after=13, first=(i == 0))
line(tf, "המסקנה: האסטרטגיה מותירה עקבות מדידים בנתונים, ואנחנו עוברים מתיאור, למבחן, לניבוי.", 19, NAVY, bold=True, space_after=14)
line(tf, "תודה! שאלות?", 24, BLUE, bold=True, align="ctr", space_after=0)

out = str(ROOT / "presentation" / "mid_presentation_OpenPowerlifting.pptx")
prs.save(out)
print("saved:", out, "|", len(list(prs.slides)), "slides")
