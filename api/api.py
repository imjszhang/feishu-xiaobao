from fastapi import FastAPI
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware

class API:
    def __init__(self):
        self.app = FastAPI()
        
        # CORS 配置
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._include_routers()

    def _include_routers(self):
        try:
            from api.app.routes import test, scraper
            self.app.include_router(test.router)
            self.app.include_router(scraper.router)
        except Exception as e:
            print(f"Error importing routes: {e}")

# 创建实例
api = API()
app = api.app

# 配置 handler
handler = Mangum(app, lifespan="off")