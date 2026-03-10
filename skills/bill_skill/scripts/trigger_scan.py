#!/usr/bin/env python3
import subprocess
import os
import sys

# 定義核心專案路徑
BASE_DIR = os.path.expanduser("~/.gemini/antigravity/scratch/financial_assistant")
VENV_PYTHON = os.path.join(BASE_DIR, "venv/bin/python3")

def run_scan():
    print("🚀 啟動信用卡帳單掃描自動化流程...")
    
    # 執行 scan 指令
    try:
        result = subprocess.run(
            [VENV_PYTHON, "main.py", "scan"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(result.stdout)
            print("✅ 掃描與同步完成！請檢查 Notion 儀表板。")
        else:
            print(f"❌ 執行出錯 (代碼 {result.returncode}):")
            if result.stdout.strip():
                print(result.stdout)
            if result.stderr.strip():
                print(result.stderr)
            
    except Exception as e:
        print(f"❌ 系統錯誤: {e}")

if __name__ == "__main__":
    run_scan()
