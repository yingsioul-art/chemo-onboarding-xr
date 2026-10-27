/**
 * 新進護理師化療給藥到職訓練｜實體課 2D 互動情境 — 作答接收＋老師圖表資料（Web App）
 * 部署：在「到職訓練情境作答」專用試算表 → 擴充功能 → Apps Script，貼上本檔 → 部署為網頁應用程式（執行身分＝我、存取＝所有人）。
 * 🔴 老師個人版密碼：專案設定 → 指令碼屬性 → 新增 TEACHER_KEY（自訂一組字串）。沒有設定時，個人版一律拒絕。
 * 讀取：
 *   ?mode=summary&since=ISO&until=ISO → 匿名列（無員工編號），給老師圖表頁（until 可省略）
 *   ?mode=detail&since=ISO&key=… → 含員工編號，給老師個人版
 * 訓練成效評估（eval.html，kind＝pre／post／check／lab）、三個月自學站（lab3m.html，kind＝m3）、技術站操作紀錄（lab.html，kind＝labrun）另存「eval」分頁：
 *   ?mode=evalpre&code=…  → 該代碼最近一次前測（後測頁做前後對照用）
 *   ?mode=eval&key=…      → 全部成效資料（老師結果頁）
 *   ?mode=labsum&since=ISO&until=ISO → 技術站自評匿名彙總（只回各站程度＋需協助步驟，不含員工編號），給老師圖表頁開場對焦
 */
var SHEET_NAME = 'responses';
var HEAD = ['收到時間', '員工編號', '開始時間', '送出時間', '作答秒數', '答對', '題數', '不知道題數',
            '很確定卻答錯題數', '很確定卻答錯', '要問老師的步驟', '差距_以為會卻不會', '差距_打算怎麼補',
            'submission_id', '版本', 'UA', '原始JSON'];

function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(20000);
    var p = JSON.parse((e && e.postData && e.postData.contents) || '');
    if (p && EVAL_KINDS.indexOf(p.kind) >= 0) return evalPost_(p);
    if (!p || !p.code || !p.answers) return json_({ ok: false, error: 'missing code/answers' });
    var sh = sheet_();
    if (p.submission_id) {
      var last = sh.getLastRow(), col = HEAD.indexOf('submission_id') + 1;
      if (last >= 2) {
        var ids = sh.getRange(2, col, last - 1, 1).getValues();
        for (var i = 0; i < ids.length; i++) if (String(ids[i][0]) === String(p.submission_id)) return json_({ ok: true, duplicate: true });
      }
    }
    var row = [new Date(), "'" + String(p.code), p.started_at || '', p.submitted_at || '', p.duration_sec || '',
      p.total, p.max, p.unknown, (p.hc_wrong || []).length, (p.hc_wrong || []).join('、'), (p.ask_steps || []).join('、'),
      p.gap1 || '', p.gap2 || '', p.submission_id || '', p.version || '', p.ua || '', JSON.stringify(p)];
    // 每題一欄（10/25）：固定欄之後接 p.cols；表頭沒有的欄位名稱就加在最右邊
    sh.appendRow(row.concat(extraCols_(sh, HEAD.length, p.cols)));
    return json_({ ok: true, row: sh.getLastRow() });
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message || err) });
  } finally { try { lock.releaseLock(); } catch (x) {} }
}

function doGet(e) {
  var q = (e && e.parameter) || {};
  var mode = q.mode || 'ping';
  if (mode === 'ping') return json_({ ok: true, service: 'chemo-onboarding', time: new Date().toISOString() });
  if (mode === 'evalpre' || mode === 'eval') return evalGet_(mode, q);
  if (mode === 'labsum') return labSum_(q);
  var detail = mode === 'detail';
  if (detail) {
    var key = PropertiesService.getScriptProperties().getProperty('TEACHER_KEY');
    if (!key || q.key !== key) return json_({ ok: false, error: 'bad_key' });
  }
  var since = q.since ? new Date(q.since) : new Date(Date.now() - 12 * 3600 * 1000);
  var until = q.until ? new Date(q.until) : null;   // 10/26：老師頁選「日期＋上午／下午」→ 帶結束時間
  var sh = sheet_(), last = sh.getLastRow();
  if (last < 2) return json_({ ok: true, rows: [] });
  var vals = sh.getRange(2, 1, last - 1, HEAD.length).getValues();
  var iRaw = HEAD.indexOf('原始JSON'), rows = [];
  vals.forEach(function (r) {
    if (!(r[0] instanceof Date) || r[0] < since || (until && r[0] >= until)) return;
    var p; try { p = JSON.parse(r[iRaw]); } catch (x) { return; }
    var o = { total: p.total, max: p.max, unknown: p.unknown, answers: p.answers,
              hc_wrong: p.hc_wrong || [], ask_steps: p.ask_steps || [], gap1: p.gap1 || '', gap2: p.gap2 || '' };
    if (detail) { o.code = String(p.code); o.t = r[0].toISOString(); }
    rows.push(o);
  });
  if (!detail) shuffle_(rows);   // 投影版：打亂順序，避免由送出時間對回是誰
  return json_({ ok: true, rows: rows });
}

// ---------- 訓練成效評估 ----------
var EVAL_SHEET = 'eval';
var EVAL_KINDS = ['pre', 'post', 'check', 'lab', 'm3', 'labrun'];   // lab＝技術站自評（上課前，ZPD）；m3＝三個月自學站 lab3m.html（10/26：計畫、練前練後把握度、各站做錯項次，老師在 lab3m.html#/teacher 用 mode=eval 讀）；labrun＝五天版技術站 lab.html 的操作紀錄（10/28：一站一筆，做錯／出事次數、出錯步驟、秒數，欄名「操作_」開頭）
var EVAL_HEAD = ['收到時間', '類型', '代碼', '梯次日期', '知識答對', 'submission_id', '版本', '原始JSON'];

function evalSheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(EVAL_SHEET) || ss.insertSheet(EVAL_SHEET);
  if (sh.getLastRow() === 0) { sh.appendRow(EVAL_HEAD); sh.getRange(1, 1, 1, EVAL_HEAD.length).setFontWeight('bold'); sh.setFrozenRows(1); }
  return sh;
}
function evalRows_() {
  var sh = evalSheet_(), last = sh.getLastRow();
  if (last < 2) return [];
  var iRaw = EVAL_HEAD.indexOf('原始JSON'), out = [];
  sh.getRange(2, 1, last - 1, EVAL_HEAD.length).getValues().forEach(function (r) {
    try { out.push(JSON.parse(r[iRaw])); } catch (x) {}
  });
  return out;
}
function evalPost_(p) {
  if (!p.code) return json_({ ok: false, error: 'missing code' });
  var sh = evalSheet_(), col = EVAL_HEAD.indexOf('submission_id') + 1, last = sh.getLastRow();
  if (p.submission_id && last >= 2) {
    var ids = sh.getRange(2, col, last - 1, 1).getValues();
    for (var i = 0; i < ids.length; i++) if (String(ids[i][0]) === String(p.submission_id)) return json_({ ok: true, duplicate: true });
  }
  // 每題一欄（10/25）：網頁送來的 p.cols＝{欄位名稱: 答案}；表頭沒有的欄位名稱就加在最右邊
  var row = [new Date(), p.kind, "'" + String(p.code), p.session || '', p.know == null ? '' : p.know,
             p.submission_id || '', p.version || '', JSON.stringify(p)];
  sh.appendRow(row.concat(extraCols_(sh, EVAL_HEAD.length, p.cols)));
  return json_({ ok: true, row: sh.getLastRow() });
}
// 固定欄（前 n 欄）之後的每題欄：依表頭名稱對值，缺的表頭補在最右邊
function extraCols_(sh, n, cols) {
  cols = cols || {};
  var head = sh.getRange(1, 1, 1, Math.max(sh.getLastColumn(), n)).getValues()[0].map(String);
  Object.keys(cols).forEach(function (k) {
    if (head.indexOf(k) < 0) { head.push(k); sh.getRange(1, head.length).setValue(k).setFontWeight('bold'); }
  });
  return head.slice(n).map(function (h) {
    var v = cols[h];
    return v == null ? '' : (typeof v === 'string' && /^[=+\-@]/.test(v) ? "'" + v : v);   // 避免開放題被當成公式
  });
}
// 10/26 使用者：開場對焦用老師圖表頁（/t/）→ 依收到時間篩選上課時段，打亂順序、不回員工編號
function labSum_(q) {
  var since = q.since ? new Date(q.since) : new Date(Date.now() - 12 * 3600 * 1000);
  var until = q.until ? new Date(q.until) : null;
  var sh = evalSheet_(), last = sh.getLastRow(), rows = [];
  if (last >= 2) {
    var iRaw = EVAL_HEAD.indexOf('原始JSON');
    sh.getRange(2, 1, last - 1, EVAL_HEAD.length).getValues().forEach(function (r) {
      if (!(r[0] instanceof Date) || r[0] < since || (until && r[0] >= until)) return;
      var p; try { p = JSON.parse(r[iRaw]); } catch (x) { return; }
      if (p.kind === 'lab') rows.push({ zpd: p.zpd || [], need: p.need || '' });
    });
  }
  shuffle_(rows);
  return json_({ ok: true, rows: rows });
}
function evalGet_(mode, q) {
  var rows = evalRows_();
  if (mode === 'evalpre') {
    // 只回分數與作答，不回開放題
    var pre = null;
    rows.forEach(function (p) { if (p.kind === 'pre' && String(p.code) === String(q.code) && (!pre || p.submitted_at > pre.submitted_at)) pre = p; });
    // 10/28 eval-v2：多回版本、選項順序、進階題（舊資料沒有這些欄位就是 undefined，網頁會自己處理）
    return json_({ ok: true, pre: pre ? { se: pre.se, answers: pre.answers, know: pre.know, version: pre.version, order: pre.order, adv_answers: pre.adv_answers, adv: pre.adv, adv_order: pre.adv_order } : null });
  }
  var key = PropertiesService.getScriptProperties().getProperty('TEACHER_KEY');
  if (!key || q.key !== key) return json_({ ok: false, error: 'bad_key' });
  return json_({ ok: true, rows: rows });
}

function sheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
  if (sh.getLastRow() === 0) { sh.appendRow(HEAD); sh.getRange(1, 1, 1, HEAD.length).setFontWeight('bold'); sh.setFrozenRows(1); }
  return sh;
}
function shuffle_(a) { for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; } }
function json_(obj) { return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON); }
