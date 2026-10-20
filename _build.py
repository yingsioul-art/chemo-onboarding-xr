# -*- coding: utf-8 -*-
r"""新進護理師化療給藥到職訓練｜實體課 2D 互動情境 — 資料建置腳本（可重跑）
單一來源（本腳本只讀不改）：
  腳本 md：D:\Zettelkasten\20_教學\Makar\40_新進護理師到職訓練XR\04_情境腳本_v0.3.md
  圖卡：   D:\Zettelkasten\20_教學\Makar\40_新進護理師到職訓練XR\images\I01.png …（使用者用 ChatGPT 生圖）
           images\supplies\S01.png…、images\outcomes\…、images\options\A3-A.png…（〔圖卡選項〕題）
產出：docs/data/script.json、docs/images/*.jpg（有圖才複製；沒有圖網頁用佔位）
用法：PYTHONUTF8=1 python _build.py
"""
import json, re, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
SRC = pathlib.Path(r"D:\Zettelkasten\20_教學\Makar\40_新進護理師到職訓練XR")
MD = SRC / "04_情境腳本_v0.3.md"
OUT = HERE / "docs" / "data" / "script.json"

# 題目 → 圖卡（對應 05_ChatGPT生圖prompt_圖卡清單）
IMG = {"intro": "I01", "A1": "I02", "A4b": "", "A2a": "I03", "A2b": "I03", "A3": "I04", "A4": "I05", "A5": "I05",
       "A6": "I17", "A7": "I06", "A8": "I05", "A9": "I07", "B3": "I08", "B3b": "I08", "B4": "I09",
       "B5": "I18", "B6": "I18", "B7": "I10", "B8": "I19", "B9": "I18", "B10": "I11", "B11": "I11",
       "B14": "I12", "B15": "I13", "B22": "I14", "C4": "I15", "C5": "I15"}
# 段落結果的說明附圖（答完後才看到，例如正確樣子的對照）
EXPLAIN_IMG = {"A7": "I16"}
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
intro = clean(re.search(r"## 開場\s*\n+> (.+)", md).group(1))
ACT_DESC = {}   # 幕說明：第一行＝這一幕要做什麼，接著「> - 」條列
for k, h in (("A", "第一幕"), ("B", "第二幕"), ("C", "第三幕")):
    m = re.search(r"## " + h + r"[^\n]*\n+> 幕說明：(.+)((?:\n> - .+)*)", md)
    ACT_DESC[k] = {"do": clean(m.group(1)), "pts": [clean(x) for x in re.findall(r"\n> - (.+)", m.group(2))]} if m else ""
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
    it = {"id": qid, "act": qid[0], "title": clean(title), "ref": ref[0] if ref else "", "stem": "", "explain": "", "opts": [], "img": IMG.get(qid, ""), "explain_img": EXPLAIN_IMG.get(qid, "")}
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
    elif "〔互動：角度動畫〕" in lines[0]:
        it["type"] = "mcq"; it["opts"] = opts; it["anim"] = "angle"
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

# 用物準備（逆向設計，07_逆向設計_完成成果與用物_v0.1.md）：每幕一題，放在該幕第一題之前
# 第一步勾「完成時應該看到的成果」；第二步把用物圖卡拖到每個成果（同一張可拖到多個成果）
CAT = {}   # 用物圖卡目錄：S01… → 名稱（08_用物圖卡_ChatGPT生圖prompt.md）
for sid, nm in re.findall(r"(?m)^\| (S\d\d) \|(?: (?:`[^`]*`|—) \|)? (.+?) \|", (SRC / "08_用物圖卡_ChatGPT生圖prompt.md").read_text(encoding="utf-8")):   # 第二欄「參考圖」可有可無
    CAT[sid] = clean(nm)
ALIAS = {"口罩": "S01", "外科口罩": "S01", "條碼機": "S26", "生理食鹽水或相容輸液": "S24",
         "Port-A 安全角針": "S10", "70–75% 酒精或無菌蒸餾水": "S03", "4\"×4\" Y 型紗布": "S12", "4\"×4\" 紗布": "S11", "2\"×2\" 紗布": "S16", "雙層丁腈膠或乳膠手套": "S18", "CSTD 的 Spike 與 Adapter": "S22", "生理食鹽水點滴袋": "S24", "NS 10 mL 注射器（預充式）": "S33"}
def sid_of(name):
    n = re.sub(r"（依外觀.*?）$", "", name.strip())
    if n in ALIAS: return ALIAS[n]
    for k, v in CAT.items():
        if v == n: return k
    print("用物名稱對不到圖卡：", name); sys.exit(1)
def split_names(t):
    return [x.strip() for x in re.split(r"、(?![^（]*）)", t) if x.strip() and x.strip() != "—"]
OUT_MD = (SRC / "07_逆向設計_完成成果與用物_v0.1.md").read_text(encoding="utf-8")
for act, h in (("A", "第一幕"), ("B", "第二幕"), ("C", "第三幕")):
    sec = re.search(r"## " + h + r"[^\n]*\n(.*?)(?=\n## |\Z)", OUT_MD, re.S).group(1)
    outs, douts = [], []
    for key, txt, short, sup, ref in re.findall(r"(?m)^\| ([A-C]-O\d+|✗) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \|$", sec):
        if key == "✗": douts.append({"id": f"{act}-X{len(douts)+1}", "t": clean(txt), "s": clean(short), "why": clean(ref)})
        else: outs.append({"id": key, "t": clean(txt), "s": clean(short), "sup": [sid_of(n) for n in split_names(sup)]})
    keys = []
    for kid, kt, inc in re.findall(r"(?m)^\| ([A-C]-K\d+) \| (.+?) \| (.+?) \|$", sec):
        mem = [x.strip() for x in inc.split("、")]
        sup = []
        for o in outs:
            if o["id"] in mem:
                for x in o["sup"]:
                    if x not in sup: sup.append(x)
        keys.append({"id": kid, "t": clean(kt), "mem": mem, "sup": sup})
    if len(keys) > 5 or sorted(m for k in keys for m in k["mem"]) != sorted(o["id"] for o in outs):
        print("關鍵成果解析失敗或沒涵蓋全部細項", act); sys.exit(1)
    dsup = []
    m = re.search(r"\*\*干擾用物\*\*(?:（不該拖）)?：(.+)", sec)
    for n in split_names(m.group(1)):
        mm = re.match(r"(.+?)（(.+)）$", n)
        dsup.append({"s": sid_of(mm.group(1) if mm else n), "why": mm.group(2) if mm else ""})
    if not outs or not douts: print("成果解析失敗", act); sys.exit(1)
    first = next(i for i, x in enumerate(items) if x["act"] == act)
    items.insert(first, {"id": act + "0", "act": act, "type": "outcome", "title": "用物準備：先想完成的樣子",
                         "stem": "開始之前，先想像這一幕「做完時」應該是什麼樣子。第一步（發散）：勾出你想到的完成成果，可以多勾、也可以自己寫；第二步（收斂）：看看歸成 5 個關鍵成果後，你漏了什麼、勾錯什麼；第三步：把用物圖卡拖到 5 個關鍵成果底下。",
                         "ref": {"A": "Port-A 角針置放查核表", "B": "化療靜脈給藥查核表", "C": "Port-A 角針移除查核表"}[act],
                         "explain": "", "img": "", "outs": outs, "douts": douts, "keys": keys, "dsup": dsup})

# 圖卡選項（腳本題目標題後標〔圖卡選項〕）：A2a、A2b 用用物圖卡（08 清單），其餘用 images\options\<題號>-<選項>.png
OPT_SUP = {"生理食鹽水": "S08"}   # 選項文字和 08 用物名稱不同時的對照
for it in items:
    blk = next((b for b in blocks if b.startswith(f"**{it['id']}　")), "")
    if "〔圖卡選項〕" not in blk.split("\n")[0]: continue
    it["imgopts"] = True
    for o in it["opts"]:
        if o["unknown"]: continue
        if it["id"] in ("A2a", "A2b"):
            n = re.sub(r"（.*?）$", "", o["t"]).strip()
            sid = OPT_SUP.get(n) or ALIAS.get(n) or next((k for k, v in CAT.items() if v == n), None)
            if not sid: print("圖卡選項對不到用物：", it["id"], o["t"]); sys.exit(1)
            o["img"], o["ph"] = "sup/" + sid, "🧴"
        else:
            o["img"], o["ph"] = f"opt/{it['id']}-{o['k']}", "💉"

# 圖卡
imgdir = HERE / "docs" / "images"; have = {}
try:
    from PIL import Image
    for p in sorted((SRC / "images").glob("I*.*")):
        if p.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"): continue
        if not re.fullmatch(r"I\d{2}", p.stem): continue  # 只收 I01 這種編號檔名，畫風參考圖不上網
        im = Image.open(p).convert("RGB"); im.thumbnail((1600, 1600))
        dst = imgdir / (p.stem + ".jpg"); im.save(dst, "JPEG", quality=82, optimize=True); have[p.stem] = dst.name
    supdir = imgdir / "supplies"; supdir.mkdir(exist_ok=True)
    for p in sorted((SRC / "images" / "supplies").glob("S*.*")):
        if p.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"): continue
        im = Image.open(p).convert("RGB"); im.thumbnail((1024, 1024))
        dst = supdir / (p.stem + ".jpg"); im.save(dst, "JPEG", quality=82, optimize=True); have["sup/" + p.stem] = "supplies/" + dst.name
    outdir = imgdir / "outcomes"; outdir.mkdir(exist_ok=True)
    for p in sorted((SRC / "images" / "outcomes").glob("*.*")):
        if p.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"): continue
        im = Image.open(p).convert("RGB"); im.thumbnail((1024, 1024))
        dst = outdir / (p.stem + ".jpg"); im.save(dst, "JPEG", quality=82, optimize=True); have["out/" + p.stem] = "outcomes/" + dst.name
    optdir = imgdir / "options"; optdir.mkdir(exist_ok=True)   # 題目選項圖卡（A3-A.png…）
    for p in sorted((SRC / "images" / "options").glob("*.*")):
        if p.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"): continue
        im = Image.open(p).convert("RGB"); im.thumbnail((1024, 1024))
        dst = optdir / (p.stem + ".jpg"); im.save(dst, "JPEG", quality=82, optimize=True); have["opt/" + p.stem] = "options/" + dst.name
except ImportError:
    pass

data = {"ver": "v0.3", "intro": intro, "intro_img": IMG["intro"], "acts": ACT, "act_desc": ACT_DESC, "items": items, "conseq": CONSEQ, "images": have, "catalog": CAT}
OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
from collections import Counter
print("items", len(items), Counter(i["type"] for i in items), "images", len(have))
for it in items:
    ans = [o["t"][:14] for o in it.get("opts", []) if o["ok"]]
    print(f"  {it['id']:4} {it['type']:5} {it['title'][:16]:16} {ans if ans else it.get('answer_order', '')}")
