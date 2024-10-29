import os
import nest_asyncio
import uvicorn
import asyncio
import threading

from fastapi import FastAPI


class API:
    def __init__(self):
        nest_asyncio.apply()
        self.app = FastAPI()
        
        # CORS配置
        from fastapi.middleware.cors import CORSMiddleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._include_routers()

    def _include_routers(self):
        from api.app.routes import test, scraper
        self.app.include_router(test.router)
        self.app.include_router(scraper.router)

    def run_server(self, host="0.0.0.0", port=8000, log_level="info"):
        config = uvicorn.Config(self.app, host=host, port=port, log_level=log_level)
        server = uvicorn.Server(config)
        server.run()
    
    def run_in_background(self):
        threading.Thread(target=lambda: asyncio.run(self.run_server()), daemon=True).start()

# 创建实例
api = API()
app = api.app