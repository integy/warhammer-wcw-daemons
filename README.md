# WCW 2026 · Group 9 對手指南

Warhammer World Championships 2026（巴塞隆拿，12 月 3–6 日）**Group 9 全部 63 人**（你 + 62 個對手）情報頁。

## 內容

- **你張 list** — Khorne Daemons（Daemonic Incursion、Take and Hold、1,995）基準 + 三條主線
- **速查卡** — 62 個對手，按判定排序（難打 → 五五 → 贏），帶 ITC 排名同「先殺」目標
- **組內分佈** — 軍種人數、Force Disposition、熱門 detachment
- **對手表** — 可搜尋／篩選（判定、FD），點行展開：分析 + 完整 list（逐張 datasheet + points）
- **逐人分析** — 每人一張卡，同一排序
- **打印版** — `card.html`：一頁 A4，按 faction 分組

判定（難打／五五／贏）＝ 呢張 Khorne list 對該對手嘅預期結果，唔係對手強弱。

## 資料來源

- BCP：`newprod-api.bestcoastpairings.com/v1/events/ej81ECrIXoRh/players`（groupID 9 = 63 人）
- Army list：listhammer 已公開嘅 WCW 2026 名單（points 總計 1,980–2,000 逐張核對過）
- ITC 排名：listhammer 顯示嘅 Warhammer Global Ranking（`—` = 未收錄）

## 重建

```bash
python3 build.py        # source/g9.json -> data.js
```

純靜態，無 build step，直接開 `index.html`。`source/group9-scout.md` 係完整文字版分析，
`build_daemons.py` 係舊嘅 20 人 Daemons dossier 版本（保留參考）。