#!/bin/bash
# 信用卡帳單自動化部署腳本

set -e

echo "🚀 開始部署信用卡帳單自動化系統..."

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 基礎路徑
BASE_DIR="$HOME/.gemini/antigravity/scratch/financial_assistant"
WORKSPACE_DIR="$HOME/.openclaw/workspace"
LAUNCHAGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_TARGET="$LAUNCHAGENTS_DIR/com.simon.financial-assistant.plist"
PYTHON_BIN="$BASE_DIR/venv/bin/python3"

# 1. 檢查環境
echo -e "\n${YELLOW}[1/6] 檢查環境...${NC}"

if [ ! -d "$BASE_DIR" ]; then
    echo -e "${RED}❌ 找不到 financial_assistant 目錄${NC}"
    exit 1
fi

if [ ! -f "$BASE_DIR/.env" ]; then
    echo -e "${RED}❌ 找不到 .env 檔案${NC}"
    exit 1
fi

# 檢查 Python
if [ ! -x "$PYTHON_BIN" ]; then
    echo -e "${RED}❌ 找不到專案虛擬環境 Python：$PYTHON_BIN${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 環境檢查通過${NC}"

# 2. 建立必要目錄
echo -e "\n${YELLOW}[2/6] 建立目錄結構...${NC}"

mkdir -p "$BASE_DIR/logs"
mkdir -p "$BASE_DIR/logs/archive"
mkdir -p "$BASE_DIR/scripts"

echo -e "${GREEN}✅ 目錄建立完成${NC}"

# 3. 檢查 .env 設定
echo -e "\n${YELLOW}[3/6] 檢查 .env 設定...${NC}"

if ! grep -q "TELEGRAM_BOT_TOKEN" "$BASE_DIR/.env"; then
    echo -e "${YELLOW}⚠️  未設定 TELEGRAM_BOT_TOKEN${NC}"
    echo "請在 .env 中新增："
    echo "TELEGRAM_BOT_TOKEN=你的_BOT_TOKEN"
    echo "TELEGRAM_CHAT_ID=你的_CHAT_ID"
    echo ""
    read -p "是否繼續？ (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}✅ 設定檢查完成${NC}"

# 4. 設定腳本權限
echo -e "\n${YELLOW}[4/6] 設定腳本權限...${NC}"

chmod +x "$BASE_DIR/scripts"/*.sh
chmod +x "$BASE_DIR/scripts"/*.py
chmod +x "$BASE_DIR/main.py"
chmod +x "$BASE_DIR/main_enhanced.py"

echo -e "${GREEN}✅ 權限設定完成${NC}"

# 5. 安裝 launchd
echo -e "\n${YELLOW}[5/6] 安裝 launchd 服務...${NC}"

PLIST_FILE="$WORKSPACE_DIR/com.simon.financial-assistant.plist"

if [ ! -f "$PLIST_FILE" ]; then
    echo -e "${RED}❌ 找不到 plist 檔案${NC}"
    exit 1
fi

# 檢查 plist 語法
if ! plutil -lint "$PLIST_FILE" > /dev/null; then
    echo -e "${RED}❌ plist 檔案格式錯誤${NC}"
    exit 1
fi

# 複製到 LaunchAgents
cp "$PLIST_FILE" "$PLIST_TARGET"
chmod 644 "$PLIST_TARGET"

# 卸載舊服務（如果存在）
launchctl bootout "gui/$(id -u)" "$PLIST_TARGET" 2>/dev/null || true

# 載入新服務
launchctl bootstrap "gui/$(id -u)" "$PLIST_TARGET"

echo -e "${GREEN}✅ launchd 服務已安裝${NC}"

# 6. 驗證安裝
echo -e "\n${YELLOW}[6/6] 驗證安裝...${NC}"

if launchctl list | grep -q "com.simon.financial-assistant"; then
    echo -e "${GREEN}✅ 服務運行正常${NC}"
else
    echo -e "${RED}❌ 服務未啟動${NC}"
    exit 1
fi

# 測試腳本
echo -e "\n${YELLOW}測試 Telegram 通知...${NC}"
cd "$BASE_DIR"
"$PYTHON_BIN" -c "from modules.telegram_notifier import send_telegram_message; send_telegram_message('🎉 財務助手自動化部署成功！')" || echo -e "${YELLOW}⚠️ Telegram 通知測試失敗（可能未設定）${NC}"

# 完成
echo -e "\n${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 部署完成！${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo "📅 排程設定："
echo "  • 每日 09:10 自動掃描"
echo "  • 每日 21:00 自動掃描"
echo ""
echo "📂 檔案位置："
echo "  • 日誌：$BASE_DIR/logs/"
echo "  • 腳本：$BASE_DIR/scripts/"
echo ""
echo "🔧 常用指令："
echo "  • 手動測試：$PYTHON_BIN $BASE_DIR/main.py scan"
echo "  • 檢查狀態：launchctl list | grep financial-assistant"
echo "  • 查看日誌：tail -f $BASE_DIR/logs/stdout.log"
echo "  • 停止服務：launchctl bootout gui/$(id -u) $PLIST_TARGET"
echo ""
echo "📖 完整文件：~/.openclaw/workspace/信用卡帳單自動化完整方案.md"
echo ""
