/**
 * 新進護理師化療給藥到職訓練｜實體課 2D 互動情境 — 作答接收＋老師圖表資料（Web App）
 * 部署：在「到職訓練情境作答」專用試算表 → 擴充功能 → Apps Script，貼上本檔 → 部署為網頁應用程式（執行身分＝我、存取＝所有人）。
 * 🔴 老師個人版密碼：專案設定 → 指令碼屬性 → 新增 TEACHER_KEY（自訂一組字串）。沒有設定時，個人版一律拒絕。
 * 讀取：
 *   ?mode=summary&since=ISO   → 匿名列（無員工編號），給大螢幕投影版
 *   ?mode=detail&since=ISO&key=… → 含員工編號，給老師個人版
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
    if (!p || !p.code || !p.answers) return json_({ ok: false, error: 'missing code/answers' });
    var sh = sheet_();
    if (p.submission_id) {
      var last = sh.getLastRow(), col = HEAD.indexOf('submission_id') + 1;
      if (last >= 2) {
        var ids = sh.getRange(2, col, last - 1, 1).getValues();
        for (var i = 0; i < ids.length; i++) if (String(ids[i][0]) === String(p.submission_id)) return json_({ ok: true, duplicate: true });
      }
    }
    sh.appendRow([new Date(), "'" + String(p.code), p.started_at || '', p.submitted_at || '', p.duration_sec || '',
      p.total, p.max, p.unknown, (p.hc_wrong || []).length, (p.hc_wrong || []).join('、'), (p.ask_steps || []).join('、'),
      p.gap1 || '', p.gap2 || '', p.submission_id || '', p.version || '', p.ua || '', JSON.stringify(p)]);
    return json_({ ok: true, row: sh.getLastRow() });
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message || err) });
  } finally { try { lock.releaseLock(); } catch (x) {} }
}

function doGet(e) {
  var q = (e && e.parameter) || {};
  var mode = q.mode || 'ping';
  if (mode === 'ping') return json_({ ok: true, service: 'chemo-onboarding', time: new Date().toISOString() });
  var detail = mode === 'detail';
  if (detail) {
    var key = PropertiesService.getScriptProperties().getProperty('TEACHER_KEY');
    if (!key || q.key !== key) return json_({ ok: false, error: 'bad_key' });
  }
  var since = q.since ? new Date(q.since) : new Date(Date.now() - 12 * 3600 * 1000);
  var sh = sheet_(), last = sh.getLastRow();
  if (last < 2) return json_({ ok: true, rows: [] });
  var vals = sh.getRange(2, 1, last - 1, HEAD.length).getValues();
  var iRaw = HEAD.indexOf('原始JSON'), rows = [];
  vals.forEach(function (r) {
    if (!(r[0] instanceof Date) || r[0] < since) return;
    var p; try { p = JSON.parse(r[iRaw]); } catch (x) { return; }
    var o = { total: p.total, max: p.max, unknown: p.unknown, answers: p.answers,
              hc_wrong: p.hc_wrong || [], ask_steps: p.ask_steps || [], gap1: p.gap1 || '', gap2: p.gap2 || '' };
    if (detail) { o.code = String(p.code); o.t = r[0].toISOString(); }
    rows.push(o);
  });
  if (!detail) shuffle_(rows);   // 投影版：打亂順序，避免由送出時間對回是誰
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
