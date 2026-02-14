# MEMORY.md - 龍蝦的長期記憶 🦞

## Simon
- 台灣工程師，時區 GMT+8
- 給我自主權：「只要是對我好的，你直接處理就好」
- Telegram user id: 8096564897

## 核心系統

### financial_assistant
- 位置：`~/.gemini/antigravity/scratch/financial_assistant/`
- 功能：Gmail → PDF 解密 → 解析 → Notion
- 排程：每天 09:10 自動執行 (launchd)
- 支援銀行：台北富邦、中國信託、玉山、永豐、國泰世華、新光、台新、星展

### Notion 結構
```
我的財務總管
├── 💳 信用卡帳單管理中心 (ed9cef8e-72ab-48ca-9c8e-7e1f5d21d439)
├── 📋 消費明細 (2ff2895b-b1ee-8131-82af-da875e50ab86)
└── 📁 資料庫存放區
```

### 重要路徑
- launchd plist: `~/Library/LaunchAgents/com.simon.financial-assistant.plist`
- 日誌: `/tmp/financial-assistant.log`
- Excel 檔案專區: Google Drive

## 技術筆記

### 銀行 PDF 密碼格式
- 大部分：身分證字號（大寫）
- 台新：身分證後2碼 + 生日MMDD
- 星展：身分證後4碼 + 生日MMDD
- 新光：需網銀查看

### 民國年轉換
- 3位數 (100-200)：+1911 → 西元年
- 例：115 → 2026

### Notion API 限制
- 無法直接移動 inline database
- 無法直接調整欄位順序
- 需手動在 UI 操作

---
*建立於 2026-02-07*
