import os
import nest_asyncio
import uvicorn
import asyncio
import threading

from fastapi import FastAPI, Request, HTTPException, Header, Depends
from api.app.dependencies import lifespan
from mangum import Mangum

class API:
    def __init__(self):

        # 允许在 Jupyter Notebook 中使用异步循环
        nest_asyncio.apply()

        # 初始化 FastAPI 应用
        self.app = FastAPI(lifespan=lifespan)

        # 引入各个路由模块
        self._include_routers()

    def _include_routers(self):
        from .app.routes import test, scraper

        self.app.include_router(test.router)
        self.app.include_router(scraper.router)

    def run_server(self, host="0.0.0.0", port=8000, log_level="info"):
        config = uvicorn.Config(self.app, host=host, port=port, log_level=log_level)
        server = uvicorn.Server(config)
        server.run()
    
    def run_in_background(self):

        # 在新的线程中启动FastAPI应用，但不启动新的事件循环，而是使用现有的循环
        threading.Thread(target=lambda: asyncio.run(self.run_server()), daemon=True).start()

# 暴露 FastAPI 实例，供 Vercel 使用
api_instance = API()
app = api_instance.app

# 添加 handler 用于 Vercel 部署
handler = Mangum(app)