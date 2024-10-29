from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# 使用特定版本的配置
handler = Mangum(app, lifespan="off", api_gateway_base_path="/")