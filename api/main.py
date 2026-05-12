# api/main.py
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

app = FastAPI(title="跨境经营数据API", description="为Dify工作流提供模拟数据")

# 允许Dify跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

def load_and_merge_data(target_date: str):
    """加载三个平台的CSV并合并，只返回指定日期的数据"""
    dfs = []
    for platform, filename in [("amazon", "amazon.csv"), ("tiktok", "tiktok.csv"), ("1688", "1688.csv")]:
        file_path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(file_path):
            print(f"警告：文件 {file_path} 不存在")
            continue
        df = pd.read_csv(file_path)
        df["platform"] = platform
        dfs.append(df)
    
    if not dfs:
        return pd.DataFrame()
    
    merged = pd.concat(dfs, ignore_index=True)
    # 确保order_date列是字符串，统一格式 YYYY-MM-DD
    merged["order_date"] = pd.to_datetime(merged["order_date"]).dt.strftime("%Y-%m-%d")
    # 按目标日期过滤
    merged = merged[merged["order_date"] == target_date]
    # 转换为字典列表，方便JSON序列化
    return merged.to_dict(orient="records")

@app.get("/api/daily_data")
def get_daily_data(date: str = None):
    """
    获取指定日期的经营数据
    - date: 可选，格式 YYYY-MM-DD。若不提供，默认使用系统当前日期。
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # 简单校验日期格式
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    
    data = load_and_merge_data(date)
    
    return {
        "date": date,
        "total_orders": len(data),
        "orders": data
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
