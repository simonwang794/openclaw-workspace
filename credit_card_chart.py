import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非互動式後端
import numpy as np
from datetime import datetime

# 設置中文字體支持
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 信用卡帳單數據
categories = ['餐飲', '購物', '交通', '娛樂', '日用品', '其他']
amounts = [3200, 5800, 1200, 2100, 1500, 800]
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#C7CEEA']

# 創建圖表
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('信用卡帳單分析報表', fontsize=16, fontweight='bold')

# 左側：圓餅圖
wedges, texts, autotexts = ax1.pie(amounts, labels=categories, colors=colors,
                                     autopct='%1.1f%%', startangle=90,
                                     textprops={'fontsize': 10})
ax1.set_title('消費分類占比')

# 右側：柱狀圖
bars = ax2.bar(categories, amounts, color=colors, alpha=0.8, edgecolor='black')
ax2.set_title('各類別消費金額')
ax2.set_ylabel('金額 (NT$)', fontsize=11)
ax2.set_xlabel('消費類別', fontsize=11)
ax2.grid(axis='y', alpha=0.3, linestyle='--')

# 在柱狀圖上顯示數值
for bar in bars:
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             f'NT${height:,.0f}',
             ha='center', va='bottom', fontsize=9)

# 添加總計信息
total = sum(amounts)
fig.text(0.5, 0.02, f'本期總消費：NT${total:,.0f} | 帳單日期：{datetime.now().strftime("%Y-%m-%d")}',
         ha='center', fontsize=11, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout(rect=[0, 0.03, 1, 0.96])
plt.savefig('credit_card_bill.png', dpi=300, bbox_inches='tight')
print("圖表已生成：credit_card_bill.png")
