"""
************************************

🧬 程式四_：追加硬體需求欄位

最基礎的推算公式如下：
VRAM需求(GB) ≒ 模型參數量(B) * ( 量化位元數(Bits) / 8 ) * 1.2預留緩衝

模型參數量(B)：模型的總參數數量，以十億為單位，[param_size_b]欄位

量化位元數(Bits)：模型的量化位元數，根據模型名稱與標籤判斷，[model_name]和[tags]欄位
    1. 16bit / 16-bit / fp16 / bf16 / bfloat16
    2. 8bit / 8-bit / int8 / fp8 / gptq-int8 / q8_0 / q8_k / q8_m
    3. 4bit / 4-bit / int4 / nf4 / awq / gptq / q4_ / q4- / w4a / nvfp4
    4. GGUF 格式：q3_ / q5_ / q6_

預留緩衝：為了避免 VRAM 不足，通常會預留 20% 的緩衝空間，因此乘以 1.2。

再者，為了方便使用者快速了解模型對應的 VRAM 需求
我們將 VRAM 需求分為八個等級，[vram_rank]欄位
並給予繁體中文標籤描述，[vram_tier]欄位

************************************
"""




import pandas as pd
import numpy as np  # 引入 np.inf 代表無限大
from proj_hf.clear import clear
from proj_hf.get_root import get_root

def read_csv(csv_path):
    try:
        return pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"❌ 錯誤：找不到原始檔案，請確認路徑：{csv_path}")
        return None


def detect_bits(model_row):
    model_name = "" if pd.isna(model_row.get("model_name")) else str(model_row["model_name"])
    model_tags = "" if pd.isna(model_row.get("tags")) else str(model_row["tags"])
    model_text = f"{model_name} | {model_tags}".lower()

    if any(marker in model_text for marker in ["16bit", "16-bit", "fp16", "bf16", "bfloat16"]):
        return 16.0

    if any(
        marker in model_text
        for marker in ["8bit", "8-bit", "int8", "fp8", "gptq-int8", "q8_0", "q8_k", "q8_m"]
    ):
        return 8.0

    if any(
        marker in model_text
        for marker in ["4bit", "4-bit", "int4", "nf4", "awq", "gptq", "q4_", "q4-", "w4a", "nvfp4"]
    ):
        return 4.5

    if "gguf" in model_text:
        if "q5_" in model_text: return 5.5
        if "q6_" in model_text: return 6.5
        if "q3_" in model_text: return 3.5
        return 4.5

    return 16.0

def add_vram(model_csv_path):
    models_df = read_csv(model_csv_path)
    if models_df is None:
        return

    required_columns = ["model_name", "tags", "param_size_b"]
    missing_columns = [column for column in required_columns if column not in models_df.columns]
    if missing_columns:
        print(f"⚠️ 模型表缺少必要欄位：{missing_columns}")
        return

    models_df["param_size_b"] = pd.to_numeric(models_df["param_size_b"], errors="coerce")
    precision_bits = models_df.apply(detect_bits, axis=1)
    
    # 1. 計算 VRAM 欄位
    models_df["vram"] = (
        models_df["param_size_b"].fillna(0) * precision_bits / 8 * 1.2
    ).round(1)

    # 2. 定義切分區間
    bins = [-0.1, 1.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0, np.inf]
    
    # 3. 建立 vram_rank 欄位 (代碼)
    rank_labels = ["v01", "v02", "v03", "v04", "v05", "v06", "v07", "v08"]
    models_df["vram_rank"] = pd.cut(models_df["vram"], bins=bins, labels=rank_labels)

    # 4. 建立 vram_tier 欄位 (繁體中文標籤描述)
    tier_labels = [
        "極輕量 (微型嵌入式)",
        "手機端 (旗艦手機/平板)",
        "輕薄本 (入門電競筆電)",
        "入門級 (主流筆電/8G顯卡)",
        "進階級 (12G中階顯卡)",
        "主流級 (16G高階硬體)",
        "發燒友 (24G旗艦單卡)",
        "工作站 (多卡/企業級)"
    ]
    models_df["vram_tier"] = pd.cut(models_df["vram"], bins=bins, labels=tier_labels)

    # 5. 儲存並印出結果
    models_df.to_csv(model_csv_path, index=False, encoding="utf-8-sig")
    print(f"🎉 VRAM、vram_rank 與 vram_tier 欄位更新完成：{model_csv_path}")
    print(f"📊 共更新 {len(models_df)} 筆模型資料。")
    
    # 預覽新增加的雙欄位結構
    print(models_df[["model_name", "vram", "vram_rank", "vram_tier"]].head(5))

if __name__ == "__main__":
    clear()
    project_root = get_root()
    model_csv_path = project_root / "data" / "4_dim_model.csv"
    add_vram(model_csv_path)
