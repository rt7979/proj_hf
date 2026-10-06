"""
資料清洗，大數據全資料表空值與特徵動態檢查 (修正版)
"""

import pandas as pd
from pathlib import Path
from proj_hf.clear import clear
from proj_hf.get_root import get_root


def modified_date(file_path):
    df = pd.read_csv(file_path)

    date_columns = [
        column for column in df.columns
        if 'date' in column.lower()
        or column.lower() in {'created_at', 'last_modified', 'updated_at', 'modified_at'}
    ]
    if not date_columns:
        print(f"ℹ️ {file_path} 沒有日期欄位，無需修改。")
        return

    parsed_dates = {}
    for column in date_columns:
        values = df[column].astype('string')
        normalized_values = (
            values
            .str.replace(r'年|月', '-', regex=True)
            .str.replace('日', '', regex=False)
        )
        parsed = pd.to_datetime(normalized_values, format='mixed', errors='coerce')
        invalid_dates = df[column].notna() & parsed.isna()
        if invalid_dates.any():
            examples = df.loc[invalid_dates, column].head(5).tolist()
            print(
                f"⚠️ {file_path} 的 {column} 有 "
                f"{invalid_dates.sum()} 個無法解析的日期，未修改此檔案。"
            )
            print(f"   範例：{examples}")
            return
        parsed_dates[column] = parsed.dt.strftime('%Y-%m-%d')

    for column, formatted_dates in parsed_dates.items():
        df[column] = formatted_dates

    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    print(f"✅ 已將 {file_path} 的日期欄位 {date_columns} 統一為 yyyy-mm-dd。")

if __name__ == '__main__':
    clear()  # 螢幕清除魔法
    root = get_root()  # 取得 D:\proj\proj_hf

    # 定義所有資料表路徑
    csv_list = [
        'data/1_dim_author.csv',
        'data/2_dim_pipeline_tag.csv',
        'data/3_dim_library.csv',
        'data/4_dim_model_table.csv',
        'data/6_fact_snapshot.csv',
        'data/7_fact_model_totals.csv',
        # 'data/9_dim_date.csv'
    ]

    for relative_path in csv_list:
        file_path = root / relative_path
        if file_path.is_file():
            modified_date(file_path)
        else:
            print(f"⚠️ 提示：找不到檔案 {file_path}，跳過檢查。\n")