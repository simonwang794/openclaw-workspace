#!/usr/bin/env python3
import subprocess
import os
import sys

# 定義核心專案路徑
# 使用 openclaw workspace 中的現有腳本
BASE_DIR = os.path.expanduser("~/.openclaw/workspace")
VENV_PYTHON = "/usr/bin/python3" # 或者使用系統 python，因為這個腳本主要是 api 呼叫

def check_status():
    print("🔍 正在從 Notion 獲取最新帳單狀態...")
    
    try:
        # 使用現有的 check_credit_card_bills_final.py
        result = subprocess.run(
            ["python3", "check_credit_card_bills_final.py"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            # 擷取摘要部分
            output = result.stdout
            if "📋 帳單詳細資料" in output:
                summary = output.split("📋 帳單詳細資料")[1]
                print(f"📋 目前帳單摘要：{summary}")
            else:
                print(output)
        else:
            print("❌ 查詢失敗")
            if result.stdout.strip():
                print(result.stdout)
            if result.stderr.strip():
                print(result.stderr)
            
    except Exception as e:
        print(f"❌ 系統錯誤: {e}")

if __name__ == "__main__":
    check_status()
