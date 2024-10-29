from fastapi import FastAPI,Request, HTTPException, Header, Depends
import asyncio

import os
from dotenv import load_dotenv


load_dotenv()
API_KEY = os.getenv('API_KEY')

# 创建一个依赖项，用于验证API密钥
def verify_api_key(request: Request, authorization: str = Header(...)):
    # 检查请求的来源 IP 地址是否是本地地址
    if request.client.host in ["127.0.0.1", "localhost", "::1"]:
        return  
    # 对于外部访问，验证API密钥    
    if authorization != "Bearer "+API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
# 创建一个依赖项，用于验证请求是否来自本地
def verify_local_request(request: Request):
    # 检查请求的来源 IP 地址是否是本地地址
    if request.client.host not in ["127.0.0.1", "localhost", "::1"]:
        raise HTTPException(status_code=403, detail="Access forbidden: Local access only")

# 创建一个事件用于通知刷新任务停止
stop_event = asyncio.Event()

# 创建一个生命周期依赖项，用于在应用启动和关闭时执行代码
async def lifespan(app: FastAPI):
    # 简化生命周期管理
    yield