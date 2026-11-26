# WCW 2026 · Chaos Daemons 對手指南

Warhammer World Championships 2026（巴塞隆拿，12 月 3–6 日）Chaos Daemons 參賽者情報頁。

## 內容

- **速查卡** — 全場 Daemons 對手一頁式比較（detachment / disposition / Elo）
- **全場分佈** — WCW 2026 faction 比例、Disposition 分佈
- **對手表** — 逐個 Daemons 玩家：BCP 名單、Hutber Elo、近期戰績
- **逐人分析** — tier、打法、注意位
- **資料來源 / 方法** — 數據抓取方式與樣本限制

## 資料來源

- Best Coast Pairings（BCP）報名名單與 list
- Hutber / 40k 統計站 Elo 與賽事紀錄
- listhammer.info WCW 2026 公開名單

## 本機

純靜態：`index.html` + `data.js`（資料）+ `card.html`（速查卡）。
`build.py` 由 BCP / Hutber 原始 JSON 重新生成 `data.js`。

用瀏覽器直接開 `index.html` 即可，無需 build step。