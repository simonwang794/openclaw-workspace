#!/usr/bin/env python3
"""檢查 Notion 信用卡帳單資料庫的資料"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
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

def query_all_bills():
    """查詢資料庫中的所有帳單"""
    bills = []
    start_cursor = None
    
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    
    while True:
        payload = {"page_size": 100}
        if start_cursor:
            payload["start_cursor"] = start_cursor
        
        response = requests.post(url, headers=HEADERS, json=payload)
        
        if response.status_code != 200:
            print(f"❌ API 錯誤 ({response.status_code}): {response.text}")
            sys.exit(1)
        
        data = response.json()
        bills.extend(data.get("results", []))
        
        if not data.get("has_more"):
            break
        start_cursor = data.get("next_cursor")
    
    return bills

def extract_bill_info(page):
    """從 Notion 頁面提取帳單資訊"""
    props = page.get("properties", {})
    
    # 提取各個欄位
    bill_info = {
        "id": page.get("id"),
        "created_time": page.get("created_time"),
    }
    
    # 銀行名稱（通常是 select 或 title）
    if "銀行" in props:
        bank_prop = props["銀行"]
        if bank_prop["type"] == "select" and bank_prop.get("select"):
            bill_info["bank"] = bank_prop["select"]["name"]
        elif bank_prop["type"] == "title":
            bill_info["bank"] = "".join([t["plain_text"] for t in bank_prop["title"]])
    elif "名稱" in props or "Name" in props:
        name_prop = props.get("名稱") or props.get("Name")
        if name_prop["type"] == "title":
            bill_info["bank"] = "".join([t["plain_text"] for t in name_prop["title"]])
    
    # 金額
    if "金額" in props:
        amount_prop = props["金額"]
        if amount_prop["type"] == "number":
            bill_info["amount"] = amount_prop.get("number")
    
    # 帳單月份
    if "帳單月份" in props:
        month_prop = props["帳單月份"]
        if month_prop["type"] == "date" and month_prop.get("date"):
            bill_info["billing_month"] = month_prop["date"]["start"]
    
    # 繳款截止日
    if "繳款截止日" in props or "截止日" in props:
        due_prop = props.get("繳款截止日") or props.get("截止日")
        if due_prop["type"] == "date" and due_prop.get("date"):
            bill_info["due_date"] = due_prop["date"]["start"]
    
    # 狀態
    if "狀態" in props or "Status" in props:
        status_prop = props.get("狀態") or props.get("Status")
        if status_prop["type"] == "select" and status_prop.get("select"):
            bill_info["status"] = status_prop["select"]["name"]
        elif status_prop["type"] == "status" and status_prop.get("status"):
            bill_info["status"] = status_prop["status"]["name"]
    
    return bill_info

def validate_bill(bill, all_bills):
    """驗證帳單資料的正確性"""
    issues = []
    
    # 檢查金額是否合理（0-100000 之間）
    amount = bill.get("amount")
    if amount is None:
        issues.append("缺少金額資料")
    elif amount < 0 or amount > 100000:
        issues.append(f"金額異常: {amount}")
    
    # 檢查繳款截止日是否在合理範圍（今天到 60 天內）
    due_date = bill.get("due_date")
    if due_date:
        try:
            due_dt = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
            now = datetime.now(due_dt.tzinfo)
            days_diff = (due_dt - now).days
            
            if days_diff < -30:  # 超過 30 天前
                issues.append(f"繳款截止日已過期: {due_date}")
            elif days_diff > 60:  # 超過 60 天後
                issues.append(f"繳款截止日過遠: {due_date}")
        except:
            issues.append(f"繳款截止日格式錯誤: {due_date}")
    else:
        issues.append("缺少繳款截止日")
    
    # 檢查帳單月份
    billing_month = bill.get("billing_month")
    if not billing_month:
        issues.append("缺少帳單月份")
    
    # 檢查是否有重複（相同銀行 + 相同帳單月份）
    duplicates = [
        b for b in all_bills 
        if b.get("bank") == bill.get("bank") 
        and b.get("billing_month") == billing_month
        and b.get("id") != bill.get("id")
    ]
    if duplicates:
        issues.append(f"可能重複: 相同銀行 ({bill.get('bank')}) 和帳單月份 ({billing_month})")
    
    return issues

def main():
    print("🔍 查詢 Notion 信用卡帳單資料庫...")
    print(f"📊 資料庫 ID: {DATABASE_ID}\n")
    
    try:
        # 查詢所有帳單
        pages = query_all_bills()
        print(f"✅ 查詢成功，找到 {len(pages)} 筆帳單\n")
        
        # 提取帳單資訊
        bills = [extract_bill_info(page) for page in pages]
        
        # 篩選最近新增的 8 筆（根據創建時間排序）
        bills.sort(key=lambda x: x.get("created_time", ""), reverse=True)
        recent_bills = bills[:8]
        
        print("=" * 80)
        print("📋 帳單詳細資料（最近 8 筆）")
        print("=" * 80)
        
        for i, bill in enumerate(recent_bills, 1):
            print(f"\n【帳單 #{i}】")
            print(f"  🏦 銀行名稱: {bill.get('bank', '未設定')}")
            print(f"  💰 金額: ${bill.get('amount', 0):,.0f}")
            print(f"  📅 帳單月份: {bill.get('billing_month', '未設定')}")
            print(f"  ⏰ 繳款截止日: {bill.get('due_date', '未設定')}")
            print(f"  📌 狀態: {bill.get('status', '未設定')}")
            print(f"  🕐 建立時間: {bill.get('created_time', '未知')}")
            
            # 檢查資料正確性
            issues = validate_bill(bill, recent_bills)
            if issues:
                print(f"  ⚠️  問題:")
                for issue in issues:
                    print(f"     - {issue}")
        
        print("\n" + "=" * 80)
        print("📊 統計資料")
        print("=" * 80)
        
        # 統計
        total_count = len(recent_bills)
        paid_count = sum(1 for b in recent_bills if b.get("status") in ["已繳", "已付款", "Paid", "已完成"])
        pending_count = sum(1 for b in recent_bills if b.get("status") in ["待繳", "未繳", "Pending", "待處理"])
        total_amount = sum(b.get("amount", 0) for b in recent_bills)
        
        print(f"  📦 總筆數: {total_count}")
        print(f"  ✅ 已繳: {paid_count}")
        print(f"  ⏳ 待繳: {pending_count}")
        print(f"  💵 總金額: ${total_amount:,.0f}")
        
        # 按銀行分組統計
        print(f"\n  🏦 按銀行分組:")
        bank_stats = {}
        for bill in recent_bills:
            bank = bill.get("bank", "未知")
            if bank not in bank_stats:
                bank_stats[bank] = {"count": 0, "amount": 0}
            bank_stats[bank]["count"] += 1
            bank_stats[bank]["amount"] += bill.get("amount", 0)
        
        for bank, stats in sorted(bank_stats.items()):
            print(f"     • {bank}: {stats['count']} 筆, ${stats['amount']:,.0f}")
        
        # 整體資料正確性總結
        print("\n" + "=" * 80)
        print("✅ 資料正確性總結")
        print("=" * 80)
        
        all_issues = []
        for i, bill in enumerate(recent_bills, 1):
            issues = validate_bill(bill, recent_bills)
            if issues:
                all_issues.append((i, bill.get("bank"), issues))
        
        if all_issues:
            print("⚠️  發現以下問題:")
            for bill_num, bank, issues in all_issues:
                print(f"\n  帳單 #{bill_num} ({bank}):")
                for issue in issues:
                    print(f"    - {issue}")
        else:
            print("✅ 所有帳單資料檢查通過，無明顯問題！")
        
        print("\n✅ 檢查完成！")
        
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
