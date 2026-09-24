#  ********************************************
#  *
#  * 回到專案根目錄的魔法
#  * 目標：往上層跑(parent)，跑到專案根目錄為止
#  * 原理：每往上一層(parent)就使用for迴圈掃描過所有檔案和資料夾檔名，
#  *      現在專案都跟git綁定，找到.git代表回到根目錄
#  *
#  ********************************************

from pathlib import Path
from proj_hf.clear import clear

def get_root(start_path: str | Path | None = None) -> Path:
    """
    從指定路徑往上找，直到找到專案根目錄為止。
    這裡以 .git 或 pyproject.toml 當作根目錄標記，
    可兼容 Git 倉庫與 Python 套件專案。
    """
    current = Path(start_path).resolve() if start_path is not None else Path(__file__).resolve().parent

    if not current.exists():
        current = Path.cwd()

    for parent in [current, *current.parents]:
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent

    print("⚠️ 警告：找不到專案根目錄標記，預設回傳目前路徑。")
    return current


# ========================================================================
# 核心關鍵：以下程式碼只有在「直接執行此腳本」時才會跑。
# 當被其他程式 import 時，以下程式碼會被完全忽略！
# ========================================================================

if __name__ == "__main__":
    clear()
    
    # 執行尋找根目錄
    proj_root_dir = get_root()
    print(f"尋找到的專案根目錄: {proj_root_dir}")
