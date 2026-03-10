#!/usr/bin/env python3
"""檢查 Notion 信用卡帳單資料庫的資料（使用正確的欄位名稱）"""

import os
import sys
import json
import requests
import re
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
DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "3062895b-b1ee-8191-85a4-edf62dfd06a7")

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

def extract_billing_month_from_name(name):
    """從 Name 欄位提取帳單月份（格式：YYYY-MM 銀行名稱）"""
    match = re.match(r'^(\d{4}-\d{2})', name)
    return match.group(1) if match else None

def extract_bank_from_name(name):
    """從 Name 欄位提取銀行名稱（移除日期前綴）"""
    match = re.match(r'^\d{4}-\d{2}\s+(.+)$', name)
    return match.group(1) if match else name

def extract_bill_info(page):
    """從 Notion 頁面提取帳單資訊"""
    props = page.get("properties", {})
    
    # 提取各個欄位
    bill_info = {
        "id": page.get("id"),
        "created_time": page.get("created_time"),
    }
    
    # Name (title) - 包含帳單月份和銀行資訊
    if "Name" in props:
        name_prop = props["Name"]
        if name_prop["type"] == "title":
            full_name = "".join([t["plain_text"] for t in name_prop["title"]])
            bill_info["full_name"] = full_name
            bill_info["billing_month"] = extract_billing_month_from_name(full_name)
            bill_info["bank_from_name"] = extract_bank_from_name(full_name)
    
    # 銀行名稱（select）
    if "銀行名稱" in props:
        bank_prop = props["銀行名稱"]
        if bank_prop["type"] == "select" and bank_prop.get("select"):
            bill_info["bank"] = bank_prop["select"]["name"]
    
    # 金額
    if "金額" in props:
        amount_prop = props["金額"]
        if amount_prop["type"] == "number":
            bill_info["amount"] = amount_prop.get("number")
    if bill_info.get("amount") is None and "本期應繳總金額" in props:
        amount_prop = props["本期應繳總金額"]
        if amount_prop["type"] == "number":
            bill_info["amount"] = amount_prop.get("number")
    
    # 日期（繳款截止日）
    if "日期" in props:
        date_prop = props["日期"]
        if date_prop["type"] == "date" and date_prop.get("date"):
            bill_info["due_date"] = date_prop["date"]["start"]
    if not bill_info.get("due_date") and "繳費截止日" in props:
        date_prop = props["繳費截止日"]
        if date_prop["type"] == "date" and date_prop.get("date"):
            bill_info["due_date"] = date_prop["date"]["start"]
    
    # 狀態
    if "狀態" in props:
        status_prop = props["狀態"]
        if status_prop["type"] == "select" and status_prop.get("select"):
            bill_info["status"] = status_prop["select"]["name"]

    if not bill_info.get("billing_month") and "帳單月份" in props:
        month_prop = props["帳單月份"]
        if month_prop["type"] == "rich_text" and month_prop.get("rich_text"):
            bill_info["billing_month"] = "".join([t["plain_text"] for t in month_prop["rich_text"]])
    
    # 剩餘天數（formula）
    if "⏰ 剩餘天數" in props:
        days_prop = props["⏰ 剩餘天數"]
        if days_prop["type"] == "formula" and days_prop.get("formula"):
            formula_result = days_prop["formula"]
            if formula_result.get("type") == "number":
                bill_info["days_remaining"] = formula_result.get("number")
    
    return bill_info


def is_credit_balance_bill(bill):
    """負數金額代表溢繳或退款，不視為異常帳單。"""
    amount = bill.get("amount")
    return isinstance(amount, (int, float)) and amount < 0


def format_amount(amount):
    """格式化金額，負數帳單額外標示為溢繳/退款。"""
    if not isinstance(amount, (int, float)):
        return "未設定"
    if amount < 0:
        return f"${amount:,.0f}（溢繳/退款）"
    return f"${amount:,.0f}"

def validate_bill(bill, all_bills):
    """驗證帳單資料的正確性"""
    issues = []
    is_credit_balance = is_credit_balance_bill(bill)
    
    # 檢查金額是否合理（溢繳/退款允許為負數）
    amount = bill.get("amount")
    if amount is None:
        issues.append("缺少金額資料")
    elif amount > 100000:
        issues.append(f"金額異常: {amount}")
    
    # 溢繳/退款帳單不需要再檢查逾期與缺少截止日
    due_date = bill.get("due_date")
    if due_date:
        try:
            due_dt = datetime.fromisoformat(due_date)
            now = datetime.now()
            days_diff = (due_dt - now).days
            
            if not is_credit_balance and days_diff < -30:  # 超過 30 天前
                issues.append(f"繳款截止日已過期超過 30 天: {due_date}")
            elif not is_credit_balance and days_diff > 90:  # 超過 90 天後
                issues.append(f"繳款截止日過遠（超過 90 天）: {due_date}")
        except:
            issues.append(f"繳款截止日格式錯誤: {due_date}")
    elif not is_credit_balance:
        issues.append("缺少繳款截止日")
    
    # 檢查帳單月份
    billing_month = bill.get("billing_month")
    if not billing_month:
        issues.append("缺少帳單月份資訊")
    else:
        # 驗證月份格式是否合理（YYYY-MM）
        try:
            month_dt = datetime.strptime(billing_month, "%Y-%m")
            # 檢查月份是否在合理範圍（過去 6 個月到未來 1 個月）
            now = datetime.now()
            months_diff = (month_dt.year - now.year) * 12 + (month_dt.month - now.month)
            if months_diff < -6:
                issues.append(f"帳單月份過舊（超過 6 個月）: {billing_month}")
            elif months_diff > 1:
                issues.append(f"帳單月份過新（超過 1 個月後）: {billing_month}")
        except:
            issues.append(f"帳單月份格式錯誤: {billing_month}")
    
    # 檢查是否有重複（相同銀行 + 相同帳單月份）
    bank = bill.get("bank") or bill.get("bank_from_name")
    duplicates = [
        b for b in all_bills 
        if (b.get("bank") or b.get("bank_from_name")) == bank
        and b.get("billing_month") == billing_month
        and b.get("id") != bill.get("id")
    ]
    if duplicates:
        issues.append(f"可能重複: 相同銀行和帳單月份")
    
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
        recent_bills = bills[:min(8, len(bills))]
        
        print("=" * 90)
        print(f"📋 帳單詳細資料（最近 {len(recent_bills)} 筆）")
        print("=" * 90)
        
        for i, bill in enumerate(recent_bills, 1):
            bank = bill.get("bank") or bill.get("bank_from_name", "未知")
            amount = bill.get("amount")
            amount_text = format_amount(amount)
            print(f"\n【帳單 #{i}】")
            print(f"  📝 完整名稱: {bill.get('full_name', '未設定')}")
            print(f"  🏦 銀行名稱: {bank}")
            print(f"  💰 金額: {amount_text}")
            print(f"  📅 帳單月份: {bill.get('billing_month', '未設定')}")
            print(f"  ⏰ 繳款截止日: {bill.get('due_date', '未設定')}")
            if bill.get("days_remaining") is not None:
                days = bill.get("days_remaining")
                print(f"  ⏱️  剩餘天數: {days:.0f} 天")
            print(f"  📌 狀態: {bill.get('status', '未設定')}")
            print(f"  🕐 建立時間: {bill.get('created_time', '未知')}")
            
            # 檢查資料正確性
            issues = validate_bill(bill, recent_bills)
            if issues:
                print(f"  ⚠️  問題:")
                for issue in issues:
                    print(f"     - {issue}")
        
        print("\n" + "=" * 90)
        print("📊 統計資料")
        print("=" * 90)
        
        # 統計
        numeric_amounts = [b.get("amount") for b in recent_bills if isinstance(b.get("amount"), (int, float))]
        total_count = len(recent_bills)
        paid_count = sum(1 for b in recent_bills if "已繳" in (b.get("status") or "") or "已付" in (b.get("status") or ""))
        credit_count = sum(1 for b in recent_bills if is_credit_balance_bill(b))
        pending_count = sum(
            1
            for b in recent_bills
            if not is_credit_balance_bill(b)
            and ("待繳" in (b.get("status") or "") or "未繳" in (b.get("status") or ""))
        )
        total_amount = sum(numeric_amounts)
        payable_amount = sum(amount for amount in numeric_amounts if amount > 0)
        credit_amount = sum(abs(amount) for amount in numeric_amounts if amount < 0)
        
        print(f"  📦 總筆數: {total_count}")
        print(f"  ✅ 已繳: {paid_count}")
        print(f"  ⏳ 待繳: {pending_count}")
        print(f"  🔁 溢繳/退款: {credit_count}")
        print(f"  💵 淨金額: ${total_amount:,.0f}")
        print(f"  📤 待繳總額: ${payable_amount:,.0f}")
        print(f"  📥 溢繳總額: ${credit_amount:,.0f}")
        
        # 按銀行分組統計
        print(f"\n  🏦 按銀行分組:")
        bank_stats = {}
        for bill in recent_bills:
            bank = bill.get("bank") or bill.get("bank_from_name", "未知")
            if bank not in bank_stats:
                bank_stats[bank] = {"count": 0, "amount": 0}
            bank_stats[bank]["count"] += 1
            bank_stats[bank]["amount"] += bill.get("amount") or 0
        
        for bank, stats in sorted(bank_stats.items()):
            print(f"     • {bank}: {stats['count']} 筆, ${stats['amount']:,.0f}")
        
        # 按月份分組統計
        print(f"\n  📅 按帳單月份分組:")
        month_stats = {}
        for bill in recent_bills:
            month = bill.get("billing_month") or "未知"
            if month not in month_stats:
                month_stats[month] = {"count": 0, "amount": 0}
            month_stats[month]["count"] += 1
            month_stats[month]["amount"] += bill.get("amount") or 0
        
        for month, stats in sorted(month_stats.items(), reverse=True):
            print(f"     • {month}: {stats['count']} 筆, ${stats['amount']:,.0f}")
        
        # 整體資料正確性總結
        print("\n" + "=" * 90)
        print("✅ 資料正確性總結")
        print("=" * 90)
        
        all_issues = []
        for i, bill in enumerate(recent_bills, 1):
            issues = validate_bill(bill, recent_bills)
            if issues:
                bank = bill.get("bank") or bill.get("bank_from_name", "未知")
                all_issues.append((i, bank, bill.get("billing_month"), issues))
        
        if all_issues:
            print("⚠️  發現以下問題:\n")
            for bill_num, bank, month, issues in all_issues:
                print(f"  帳單 #{bill_num} ({month} {bank}):")
                for issue in issues:
                    print(f"    - {issue}")
                print()
        else:
            print("✅ 所有帳單資料檢查通過，無明顯問題！")
        
        print("✅ 檢查完成！")
        
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
