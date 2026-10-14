# -*- coding: utf-8 -*-
r"""新進護理師化療給藥到職訓練｜實體課 2D 互動情境 — 資料建置腳本（可重跑）
單一來源（本腳本只讀不改）：
  腳本 md：D:\Zettelkasten\20_教學\Makar\40_新進護理師到職訓練XR\04_情境腳本_v0.3.md
  圖卡：   D:\Zettelkasten\20_教學\Makar\40_新進護理師到職訓練XR\images\I01.png …（使用者用 ChatGPT 生圖）
產出：docs/data/script.json、docs/images/*.jpg（有圖才複製；沒有圖網頁用佔位）
用法：PYTHONUTF8=1 python _build.py
"""
import json, re, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
SRC = pathlib.Path(r"D:\Zettelkasten\20_教學\Makar\40_新進護理師到職訓練XR")
MD = SRC / "04_情境腳本_v0.3.md"
OUT = HERE / "docs" / "data" / "script.json"

# 題目 → 圖卡（對應 05_ChatGPT生圖prompt_圖卡清單）
IMG = {"intro": "I01", "A1": "I02", "A2a": "I03", "A2b": "I03", "A3": "I04", "A4": "I05", "A5": "I05",
       "A6": "I06", "A7": "I06", "A8": "I05", "A9": "I07", "B3": "I08", "B3b": "I08", "B4": "I09",
       "B5": "I08", "B6": "I08", "B7": "I10", "B8": "I10", "B9": "I08", "B10": "I11", "B11": "I11",
       "B14": "I12", "B15": "I13", "B22": "I14", "C4": "I15", "C5": "I15"}
# 延後後果：答錯 src → 在 target 題目前出現的後果畫面
CONSEQ = [
    {"src": "A1", "target": "B15", "text": "（因為第一幕角針長度選得不合適）角針沒有插到圓盤底部：剛開始還有回血，但組織推擠針具後，回血變得不順。"},
    {"src": "A7", "target": "B15", "text": "（因為第一幕回血不是全血卻繼續接上化療）注射部位開始紅、腫，病人覺得痛。"},
    {"src": "B3b", "target": "B13", "text": "（因為組裝時輸液套管的 Spike 沒有完全沒入 Adapter）開始輸注後，Adapter 接合處出現滲漏。"},
    {"src": "B9", "target": "B10", "text": "（因為換上化療藥後沒有先脫除外層手套）你碰觸幫浦按鍵，手套上的化療藥殘留沾到了幫浦。"},
]
ACT = {"A": "第一幕｜Port-A 角針置放", "B": "第二幕｜化療給藥", "C": "第三幕｜Port-A 角針移除"}
CIRC = "①②③④⑤⑥⑦⑧⑨"

def clean(t):
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    return t.strip()

md = MD.read_text(encoding="utf-8")
intro = re.search(r"## 開場\s*\n+> (.+)", md).group(1).strip()
ACT_DESC = {}
for k, h in (("A", "第一幕"), ("B", "第二幕"), ("C", "第三幕")):
    m = re.search(r"## " + h + r"[^\n]*\n+> 幕說明：(.+)", md)
    ACT_DESC[k] = clean(m.group(1)) if m else ""
if not all(ACT_DESC.values()):
    print("缺幕說明", ACT_DESC); sys.exit(1)
blocks = re.split(r"(?m)^(?=\*\*[ABC]\d+[a-c]?　)", md)[1:]
items = []
for b in blocks:
    b = b.split("\n---")[0].split("\n## ")[0]
    lines = [l.rstrip() for l in b.strip().split("\n")]
    m = re.match(r"\*\*([ABC]\d+[a-c]?)　(.+?)\*\*(.*)", lines[0])
    qid, title, rest = m.group(1), m.group(2), m.group(3)
    ref = re.findall(r"（([^）]*#[^）]*)）", rest)
    it = {"id": qid, "act": qid[0], "title": clean(title), "ref": ref[0] if ref else "", "stem": "", "explain": "", "opts": [], "img": IMG.get(qid, "")}
    stem, opts, order, multi_inline = [], [], [], None
    for l in lines[1:]:
        if not l.strip():
            continue
        if l.startswith("- 說明："):
            it["explain"] = clean(l[5:]); continue
        if l.startswith("- ⏩") or l.startswith("- 判定："):
            if l.startswith("- 判定："): it["rule"] = clean(l[5:])
            continue
        if l.startswith("- 正解："):
            it["answer_order"] = [CIRC.index(c) for c in l[5:].strip() if c in CIRC]; continue
        mo = re.match(r"- ([A-D])\. (.+)", l)
        if mo:
            txt = mo.group(2); ok = txt.endswith("✅")
            opts.append({"k": mo.group(1), "t": clean(txt.rstrip("✅ ").rstrip()), "ok": ok}); continue
        mc = re.match(r"- ([①-⑨]) (.+)", l)
        if mc:
            order.append(clean(mc.group(2))); continue
        if l.startswith("- "):
            txt = l[2:]; ok = txt.endswith("✅")
            opts.append({"k": None, "t": clean(txt.rstrip("✅ ").rstrip()), "ok": ok}); continue
        if "：" in l and "／" in l and l.startswith("勾出"):
            head, tail = l.split("：", 1); stem.append(clean(head) + "：")
            for x in tail.split("／"):
                ok = x.strip().endswith("✅")
                opts.append({"k": None, "t": clean(x.replace("✅", "")), "ok": ok})
            continue
        stem.append(clean(l.lstrip("> ")))
    it["stem"] = "\n".join(stem)
    if order:
        it["type"] = "order"; it["steps"] = order
    elif "〔互動" in lines[0] + it["stem"] or qid == "A2c":
        it["type"] = "paint"
    elif opts and all(o["k"] for o in opts):
        it["type"] = "mcq"; it["opts"] = opts
    else:
        it["type"] = "multi"; it["opts"] = opts
    # 「不知道」固定最後
    if it.get("opts"):
        unk = [o for o in it["opts"] if o["t"] == "不知道"]
        it["opts"] = [o for o in it["opts"] if o["t"] != "不知道"] + (unk or [{"k": None, "t": "不知道", "ok": False}])
        for o in it["opts"]:
            o["unknown"] = o["t"] == "不知道"
    items.append(it)

# 檢查
errs = []
for it in items:
    if it["type"] == "mcq" and sum(o["ok"] for o in it["opts"]) != 1: errs.append(f"{it['id']} 正解數 != 1")
    if it["type"] == "multi" and sum(o["ok"] for o in it["opts"]) < 1: errs.append(f"{it['id']} 複選沒有正解")
    if it["type"] == "order" and sorted(it.get("answer_order", [])) != list(range(len(it["steps"]))): errs.append(f"{it['id']} 排序正解不完整")
    if it["type"] in ("mcq", "multi") and not any(o["unknown"] for o in it["opts"]): errs.append(f"{it['id']} 沒有不知道")
if errs:
    print("\n".join(errs)); sys.exit(1)

# 用物準備（06_用物準備清單_v0.1.md）：每幕一題，放在該幕第一題之前；先勾用物、再配用途
SUP = SRC / "06_用物準備清單_v0.1.md"
sup_md = SUP.read_text(encoding="utf-8")
for act, h in (("A", "第一幕"), ("B", "第二幕"), ("C", "第三幕")):
    sec = re.search(r"## " + h + r"[^\n]*\n(.*?)(?=\n## |\Z)", sup_md, re.S).group(1)
    need, distract = [], []
    for row in re.findall(r"(?m)^\| *([A-C]-\d+|✗) *\| *(.+?) *\| *(.+?) *\| *(.+?) *\|$", sec):
        key, name, purpose = row[0], clean(row[1]), clean(row[2])
        if key == "✗":
            distract.append({"t": name, "why": purpose})
        else:
            need.append({"t": name, "p": purpose})
    if not need: print("用物清單解析失敗", act); sys.exit(1)
    first = next(i for i, x in enumerate(items) if x["act"] == act)
    items.insert(first, {"id": act + "0", "act": act, "type": "supply", "title": "用物準備",
                         "stem": "開始之前，先備齊用物。第一步：勾出這一幕需要的用物；第二步：替每個用物選出它的使用目的。",
                         "ref": {"A": "Port-A 角針置放查核表", "B": "化療靜脈給藥查核表", "C": "Port-A 角針移除查核表"}[act],
                         "explain": "", "img": "", "need": need, "distract": distract})

# 圖卡
imgdir = HERE / "docs" / "images"; have = {}
try:
    from PIL import Image
    for p in sorted((SRC / "images").glob("I*.*")):
        if p.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"): continue
        im = Image.open(p).convert("RGB"); im.thumbnail((1600, 1600))
        dst = imgdir / (p.stem + ".jpg"); im.save(dst, "JPEG", quality=82, optimize=True); have[p.stem] = dst.name
except ImportError:
    pass

data = {"ver": "v0.3", "intro": intro, "intro_img": IMG["intro"], "acts": ACT, "act_desc": ACT_DESC, "items": items, "conseq": CONSEQ, "images": have}
OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
from collections import Counter
print("items", len(items), Counter(i["type"] for i in items), "images", len(have))
for it in items:
    ans = [o["t"][:14] for o in it.get("opts", []) if o["ok"]]
    print(f"  {it['id']:4} {it['type']:5} {it['title'][:16]:16} {ans if ans else it.get('answer_order', '')}")
