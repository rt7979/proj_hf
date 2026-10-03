"""
************************************

程式九：時間表


************************************
"""

import pandas as pd
from proj_hf.clear import clear
from proj_hf.get_root import get_root

def create_dim_date(date_path):
    # 1. 定義時間範圍（涵蓋 2018 到 2026 全年）
    start_date = '2018-11-01'
    end_date = '2026-09-30'

    # 2. 生成連續的「天」資料數列
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')

    # 3. 建立基礎 DataFrame
    df = pd.DataFrame({'base_date': date_range})

    # 4. 依照需求生成 11 個欄位
    dim_date = pd.DataFrame()

    # [date_id]: 整數型 PK (如 20261001)
    dim_date['date_id'] = df['base_date'].dt.date  # 保持原欄位要求的拼法，2018-11-01
    dim_date['date_label'] = df['base_date'].dt.strftime('%Y年%m月%d日')    # 2018年11月01日

    # 年份欄位
    dim_date['year_key'] = df['base_date'].dt.year  # 2018
    dim_date['year_label'] = df['base_date'].dt.strftime('%Y年') # 2018年

    # 月份欄位
    dim_date['month_key'] = df['base_date'].dt.month # 11
    dim_date['month_label'] = df['base_date'].dt.strftime('%m月')   # 11月

    # 年月欄位 (常用於月度趨勢分析)
    dim_date['y_m_key'] = df['base_date'].dt.strftime('%Y%m').astype(int)   # 201811
    dim_date['y_m_label'] = df['base_date'].dt.strftime('%Y年%m月') # 2018年11月

    # 日期中的「天」欄位
    dim_date['day_key'] = df['base_date'].dt.day # 1
    dim_date['day_label'] = df['base_date'].dt.strftime('%d日') # 01日

    # 5. 輸出成 CSV 檔
    dim_date.to_csv(date_path, index=False, encoding='utf-8-sig')
    print(f"時間維度表建立完成！共 {len(dim_date)} 筆資料（天）。")



if __name__ == "__main__":
    clear() # 螢幕清除魔法
    root = get_root()  # 取得 D:\proj\proj_hf

    date_path = root / 'data' / '9_dim_date.csv'
    create_dim_date(date_path)

