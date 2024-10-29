import logging
from api.api import API  # 确保导入路径正确

# 设置日志配置
logging.basicConfig(level=logging.INFO)

# 实例化 API 类
api = API()

# 在后台运行 FastAPI 服务器
api.run_in_background()

# 保持主线程运行
try:
    while True:
        pass  # 主线程保持运行，避免程序退出
except KeyboardInterrupt:
    logging.info("服务器已停止")