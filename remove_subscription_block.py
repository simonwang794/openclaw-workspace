#!/usr/bin/env python3
"""移除 Notion 頁面中的「訂閱服務追蹤」區塊"""

import os
import sys
import json
from dotenv import load_dotenv
from notion_client import Client

# 載入環境變數（使用 financial_assistant 的配置）
env_path = os.path.expanduser("~/.gemini/antigravity/scratch/financial_assistant/.env")
load_dotenv(env_path, override=True)

# 初始化 Notion 客戶端
notion_token = os.getenv("NOTION_TOKEN")
if not notion_token:
    print("❌ 找不到 NOTION_TOKEN")
    sys.exit(1)

notion = Client(auth=notion_token)

# 目標頁面 ID
PAGE_ID = "2f62895bb1ee801f945ada25181e517f"

def get_all_blocks(block_id):
    """遞迴獲取所有區塊"""
    blocks = []
    start_cursor = None
    
    while True:
        params = {"page_size": 100}
        if start_cursor:
            params["start_cursor"] = start_cursor
            
        response = notion.blocks.children.list(block_id, **params)
        blocks.extend(response.get("results", []))
        
        if not response.get("has_more"):
            break
        start_cursor = response.get("next_cursor")
    
    return blocks

def find_subscription_blocks(blocks):
    """找到訂閱服務追蹤相關的區塊 ID"""
    target_blocks = []
    found_heading = False
    
    # 先列出所有標題區塊用於 debug
    print("\n🔍 DEBUG: 列出所有標題區塊:")
    for block in blocks:
        block_type = block.get("type")
        if block_type in ["heading_1", "heading_2", "heading_3"]:
            heading_data = block.get(block_type, {})
            rich_text = heading_data.get("rich_text", [])
            text = "".join([t.get("plain_text", "") for t in rich_text])
            print(f"  {block_type}: {text}")
    print()
    
    for i, block in enumerate(blocks):
        block_type = block.get("type")
        block_id = block.get("id")
        
        # 檢查是否為標題區塊包含「訂閱服務追蹤」
        if block_type in ["heading_1", "heading_2", "heading_3"]:
            heading_data = block.get(block_type, {})
            rich_text = heading_data.get("rich_text", [])
            text = "".join([t.get("plain_text", "") for t in rich_text])
            
            if "訂閱" in text or "訂閱服務追蹤" in text:
                print(f"✅ 找到標題區塊: {text}")
                target_blocks.append(block_id)
                found_heading = True
                continue
        
        # 如果已找到標題，收集後續相關區塊（直到下一個標題）
        if found_heading:
            # 如果遇到新的標題，停止收集
            if block_type in ["heading_1", "heading_2", "heading_3"]:
                break
            
            # 收集段落、表格等內容區塊
            if block_type in ["paragraph", "table", "bulleted_list_item", "numbered_list_item", "callout"]:
                print(f"  ├─ 相關區塊: {block_type} (ID: {block_id})")
                target_blocks.append(block_id)
    
    return target_blocks

def delete_blocks(block_ids):
    """刪除指定的區塊"""
    deleted = []
    failed = []
    
    for block_id in block_ids:
        try:
            notion.blocks.delete(block_id)
            deleted.append(block_id)
            print(f"  ✓ 已刪除: {block_id}")
        except Exception as e:
            failed.append((block_id, str(e)))
            print(f"  ✗ 刪除失敗: {block_id} - {e}")
    
    return deleted, failed

def main():
    print(f"🔍 讀取頁面 {PAGE_ID} 的區塊...")
    
    try:
        # 獲取所有區塊
        blocks = get_all_blocks(PAGE_ID)
        print(f"📦 共找到 {len(blocks)} 個區塊\n")
        
        # 找到訂閱服務追蹤區塊
        target_blocks = find_subscription_blocks(blocks)
        
        if not target_blocks:
            print("⚠️  未找到「訂閱服務追蹤」相關區塊")
            return
        
        print(f"\n🎯 找到 {len(target_blocks)} 個需要刪除的區塊")
        print("=" * 50)
        
        # 刪除區塊
        deleted, failed = delete_blocks(target_blocks)
        
        print("\n" + "=" * 50)
        print(f"✅ 成功刪除: {len(deleted)} 個區塊")
        if failed:
            print(f"❌ 刪除失敗: {len(failed)} 個區塊")
            for block_id, error in failed:
                print(f"   - {block_id}: {error}")
        
        # 確認刪除後的結果
        print(f"\n🔄 重新檢查頁面結構...")
        remaining_blocks = get_all_blocks(PAGE_ID)
        print(f"📦 剩餘 {len(remaining_blocks)} 個區塊")
        
        # 列出剩餘的主要區塊
        print("\n📋 頁面結構概覽:")
        for block in remaining_blocks[:10]:  # 只顯示前 10 個
            block_type = block.get("type")
            if block_type in ["heading_1", "heading_2", "heading_3"]:
                heading_data = block.get(block_type, {})
                rich_text = heading_data.get("rich_text", [])
                text = "".join([t.get("plain_text", "") for t in rich_text])
                print(f"  • {text}")
        
        print("\n✅ 任務完成！")
        
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
