#!/usr/bin/env python3
"""檢查 Notion 資料庫的欄位結構"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# 載入環境變數
env_path = os.path.expanduser("~/.gemini/antigravity/scratch/financial_assistant/.env")
load_dotenv(env_path, override=True)

# 取得 Notion Token
notion_token = os.getenv("NOTION_TOKEN")
if not notion_token:
    print("❌ 找不到 NOTION_TOKEN")
    sys.exit(1)

# Notion API 設定
NOTION_VERSION = "2022-06-28"
HEADERS = {
    "Authorization": f"Bearer {notion_token}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json"
}

# 信用卡帳單資料庫 ID
DATABASE_ID = "3062895b-b1ee-8191-85a4-edf62dfd06a7"

def get_database_schema():
    """取得資料庫結構"""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"❌ API 錯誤 ({response.status_code}): {response.text}")
        sys.exit(1)
    
    return response.json()

def get_first_page():
    """取得第一筆資料"""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {"page_size": 1}
    response = requests.post(url, headers=HEADERS, json=payload)
    
    if response.status_code != 200:
        print(f"❌ API 錯誤 ({response.status_code}): {response.text}")
        sys.exit(1)
    
    data = response.json()
    results = data.get("results", [])
    return results[0] if results else None

def main():
    print("🔍 查詢資料庫結構...")
    
    # 取得資料庫結構
    db_schema = get_database_schema()
    properties = db_schema.get("properties", {})
    
    print("\n📊 資料庫欄位結構:")
    print("=" * 80)
    for prop_name, prop_info in properties.items():
        prop_type = prop_info.get("type")
        print(f"  • {prop_name}: {prop_type}")
    
    # 取得第一筆資料並顯示其屬性
    print("\n📋 第一筆資料的屬性值:")
    print("=" * 80)
    page = get_first_page()
    
    if page:
        props = page.get("properties", {})
        for prop_name, prop_data in props.items():
            prop_type = prop_data.get("type")
            print(f"\n【{prop_name}】({prop_type}):")
            print(f"  完整資料: {json.dumps(prop_data, indent=2, ensure_ascii=False)}")
    else:
        print("  ⚠️  沒有找到任何資料")
    
    print("\n✅ 檢查完成！")

if __name__ == "__main__":
    main()
