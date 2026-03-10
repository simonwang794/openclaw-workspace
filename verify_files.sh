#!/bin/bash
# 檔案完整性驗證腳本

echo "🔍 驗證所有檔案..."
echo ""

MISSING=0
TOTAL=0

check_file() {
    TOTAL=$((TOTAL + 1))
    if [ -f "$1" ]; then
        SIZE=$(ls -lh "$1" | awk '{print $5}')
        echo "✅ $1 ($SIZE)"
    else
        echo "❌ 缺少: $1"
        MISSING=$((MISSING + 1))
    fi
}

echo "📂 文件與設定檔："
check_file "$HOME/.openclaw/workspace/信用卡帳單自動化完整方案.md"
check_file "$HOME/.openclaw/workspace/快速啟動指南.md"
check_file "$HOME/.openclaw/workspace/部署總結.md"
check_file "$HOME/.openclaw/workspace/com.simon.financial-assistant.plist"
check_file "$HOME/.openclaw/workspace/com.simon.financial-assistant.reminders.plist"
check_file "$HOME/.openclaw/workspace/deploy_automation.sh"

echo ""
echo "📂 模組："
check_file "$HOME/.gemini/antigravity/scratch/financial_assistant/modules/telegram_notifier.py"
check_file "$HOME/.gemini/antigravity/scratch/financial_assistant/modules/dashboard_updater.py"

echo ""
echo "📂 腳本："
check_file "$HOME/.gemini/antigravity/scratch/financial_assistant/scripts/check_overdue.py"
check_file "$HOME/.gemini/antigravity/scratch/financial_assistant/scripts/payment_reminder.py"
check_file "$HOME/.gemini/antigravity/scratch/financial_assistant/scripts/check_duplicates.py"
check_file "$HOME/.gemini/antigravity/scratch/financial_assistant/scripts/generate_monthly_report.py"
check_file "$HOME/.gemini/antigravity/scratch/financial_assistant/scripts/rotate_logs.sh"
check_file "$HOME/.gemini/antigravity/scratch/financial_assistant/scripts/check_logs.sh"
check_file "$HOME/.gemini/antigravity/scratch/financial_assistant/scripts/run_reminders.sh"

echo ""
echo "📂 主程式："
check_file "$HOME/.gemini/antigravity/scratch/financial_assistant/main_enhanced.py"

echo ""
echo "══════════════════════════════════════"
if [ $MISSING -eq 0 ]; then
    echo "✅ 完整性檢查通過！"
    echo "📦 所有 $TOTAL 個檔案都已正確建立"
    echo ""
    echo "🚀 下一步："
    echo "   cd ~/.openclaw/workspace"
    echo "   ./deploy_automation.sh"
else
    echo "⚠️ 發現 $MISSING 個檔案缺失"
    echo "請檢查並重新建立缺失的檔案"
fi
echo "══════════════════════════════════════"
