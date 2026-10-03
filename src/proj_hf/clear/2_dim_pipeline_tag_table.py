"""
************************************

🧱 程式二：處理模型類別，導出模型類別表
從原始資料中提煉出不重複的 pipeline_tag，生成唯一的類別 ID，並導出類別維度表。
pipeline_tag：將指定的[圖片]、[文字描述]、[影片]，產出[圖片]、[文字描述]、[影片]
例如image-text-to-video，代表以圖片 and 文字描述，產生影片

************************************
"""



import pandas as pd
from proj_hf.clear import clear
from proj_hf.get_root import get_root


def create_pipeline_table(input_path, out_path):
    """
    讀取原始 CSV，提取 Pipeline 類別資訊並匯出
    """
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        print(f"❌ 錯誤：找不到原始檔案，請確認路徑：{input_path}")
        return

    # 2. 檢查欄位是否存在
    required_cols = ['pipeline_tag']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        print(f"⚠️ 警告：原始檔案中找不到欄位 {missing_cols}，請確認欄位名稱是否正確。")
    else:
        # 3. 提取類別欄位，去除重複值，並依 pipeline_name 英文字母排序
        pipeline_df = (
            df[required_cols]
            .drop_duplicates()
            .dropna(subset=['pipeline_tag'])
            .rename(columns={'pipeline_tag': 'pipeline_name'})
            .sort_values(by='pipeline_name', key=lambda s: s.str.lower())
            .reset_index(drop=True)
        )
        
        # 4. 自動生成主鍵 pipeline_id，格式為 cat001、cat002、cat003...
        pipeline_df.insert(0, 'pipeline_id', [f"cat{str(i).zfill(3)}" for i in (pipeline_df.index + 1)])
        
        # 5. 匯出成新的 CSV 檔案
        pipeline_df.to_csv(out_path, index=False, encoding='utf-8-sig')
        
        print(f"🎉 [類別csv] 還原成功！")
        print(f"📁 檔案已儲存為：{out_path}")
        print(f"📊 總共成功提取了 {len(pipeline_df)} 種模型類別。")
        
        # 顯示前 5 筆資料確認外觀
        print("\n👀 產出的資料前 5 筆範例：")
        print(pipeline_df.head())


if __name__ == "__main__":
    clear() # 螢幕清除魔法
    root = get_root()  # 取得 D:\proj\proj_hf
    
    # 1. 設定原始檔案與輸出檔案的完整路徑
    input_path = root / 'data' / 'origin_csv' / 'hf_c.csv'
    out_path = root / 'data' / '2_dim_pipeline_tag.csv'
    
    # 2. 呼叫函數並把路徑傳進去
    create_pipeline_table(input_path, out_path)
