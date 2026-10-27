# 後台（Apps Script）部署方式

專案：Apps Script「到職訓練作答後台」（綁在試算表〈到職訓練作答（情境站＋成效評估）〉）
scriptId：見 `.clasp.json`　｜　網頁用的部署 ID：`AKfycbzHpVJHrzP-dC0UWTtxjLVG7BKCxPn28-WUCjH69VMhk4u8_SnFYLZkJcPTmvwgMsaA`（index／eval／lab／lab3m 的 ENDPOINT，**不要換**）

## 改完 Code.gs 之後（2026-10-28 起用 clasp，不必開瀏覽器）
```
cd C:\dev\chemo-onboarding-xr\apps-script
clasp push                      # 上傳 Code.gs＋appsscript.json
clasp deploy -i AKfycbzHpVJHrzP-dC0UWTtxjLVG7BKCxPn28-WUCjH69VMhk4u8_SnFYLZkJcPTmvwgMsaA -d "7: 這次改了什麼"
```
- `clasp deploy -i <部署ID>` ＝在同一個部署上建立新版本，網址不變；沒有 `-i` 會另建一個新部署、新網址（網頁會收不到）。
- 驗證：`curl "<ENDPOINT>?mode=ping"`；或 `?mode=evalpre&code=<員編>` 看回傳欄位。
- 歷史：第 5 版 10/26（m3 未部署）→ 第 6 版 2026-10-28 05:30（eval-v2 evalpre 欄位＋labrun＋m3）→ **第 7 版 2026-10-28 05:59**（固定欄「版本說明」，eval 分頁 H 欄已手動插入）；兩版都由瀏覽器手動部署。
- 🔴 clasp 要先在 https://script.google.com/home/usersettings 開「Google Apps Script API」，否則 `clasp push` 回 User has not enabled the Apps Script API。
- 🔴 改 EVAL_HEAD（固定欄）時，試算表插欄與部署新版要緊接著做；中間舊版程式會讀錯欄（10/28 踩過）。

## 注意
- 雲端檔名是「程式碼.gs」，repo 檔名是 `Code.gs`：第一次 `clasp push` 會把雲端檔改名成 Code.gs（內容相同，功能不變）；之後 `clasp pull` 會寫出 `Code.js`，不要和 `Code.gs` 兩份都留。
- `clasp login` 的憑證在 `%USERPROFILE%\.clasprc.json`；過期就重跑 `clasp login`。
- 老師密碼 TEACHER_KEY 在專案設定 → 指令碼屬性，不在程式碼裡。
