"""
************************************

🧬 程式四_：模型參數量(B)

透過 Hugging Face API 查詢模型的總參數量
並將結果填回 4_model_table.csv 檔案中
最後匯出為 4_model_table_with_params.csv
需要安裝 huggingface_hub 套件，並登入 Hugging Face 帳號。

************************************
"""

import json
import pandas as pd
from huggingface_hub import HfApi, HfFileSystem, hf_hub_download
from tqdm import tqdm
from proj_hf.clear import clear
from proj_hf.get_root import get_root





def fetch_params(model_name):
    """查詢 Hugging Face 模型參數量"""
    try:
        # 1. 優先從 safetensors 索引檔取得精準參數量
        index_path = f"{model_name}/model.safetensors.index.json"
        if fs.exists(index_path):
            with fs.open(index_path, "r") as f:
                data = json.load(f)
                total_params = data.get("metadata", {}).get("total_size")
                if total_params:
                    return total_params, f"{total_params / 1e6:.1f}M", f"{total_params / 1e9:.3f}B"

        # 2. 嘗試從 config.json 解析
        config_file = hf_hub_download(repo_id=model_name, filename="config.json")
        with open(config_file, "r") as f:
            config = json.load(f)

            if "total_parameters" in config:
                tp = config["total_parameters"]
                return tp, f"{tp / 1e6:.1f}M", f"{tp / 1e9:.3f}B"

            # 根據架構參數估算 (Encoder/Decoder/Transformer)
            h = config.get("hidden_size") or config.get("d_model")
            l = config.get("num_hidden_layers") or config.get("encoder_layers") or config.get("num_layers")
            v = config.get("vocab_size") or 30522
            if h and l:
                approx = int(12 * l * (h ** 2) + (v * h))
                return approx, f"~{approx / 1e6:.1f}M", f"~{approx / 1e9:.3f}B"

        return None, "未定", "未定"

    except Exception:
        return None, "查詢失敗", "查詢失敗"




if __name__ == "__main__":
    clear() # 螢幕清除魔法
    root = get_root()  # 取得 D:\proj\proj_hf
    
    # 1. 設定原始檔案與輸出檔案的完整路徑
    input_path = root / 'data' / '4_dim_model.csv'
    out_path = root / 'data' / '4_dim_model_with_params.csv'
    
    df = pd.read_csv(input_path)
    api = HfApi()
    fs = HfFileSystem()

    # 批次查詢 236 個模型
    param_str_list = []
    param_b_list = []

    print(f"開始查詢 {len(df)} 個模型參數量...")
    for _, row in tqdm(df.iterrows(), total=len(df)):
        model_name = row["model_name"]
        _, p_m, p_b = fetch_params(model_name)
        param_str_list.append(p_m)
        param_b_list.append(p_b)

    # 填回 DataFrame 欄位，不要跟舊欄位名稱衝突
    df["總參數量"] = param_str_list
    df["總參數量_b"] = param_b_list

    # 匯出為新檔案
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n全數查詢完成！結果已儲存至：{out_path}")