# 项目名称：飞书小报 API 集成工具

## 项目简介

本项目是一个基于 **FastAPI** 框架的 API 服务，集成了飞书（Feishu）的多个 API 接口（如文档、表格、Wiki、云盘等），并提供了网页抓取功能。通过该项目，用户可以方便地与飞书的各类服务进行交互，同时也可以通过自定义的 URL 规则抓取网页内容。

## 目录结构

```plaintext
api/
│
├── app/
│   ├── dependencies.py          # 依赖项定义，如 API 密钥验证、请求来源验证等
│   ├── __init__.py              # FastAPI 应用初始化
│   ├── handlers/                # 处理飞书 API 的各类处理器
│   │   ├── feishu_app_api.py         # 飞书 API 封装类
│   │   ├── feishu_bitable_api_handler.py  # 飞书多维表格 API 处理器
│   │   ├── feishu_docx_api_handler.py     # 飞书文档 API 处理器
│   │   ├── feishu_drive_api_handler.py    # 飞书云盘 API 处理器
│   ├── models/                  # 数据模型定义
│   ├── routes/                  # API 路由定义
│   │   ├── scraper.py                # 网页抓取 API 路由
│   │   ├── test.py                   # 测试路由
│   ├── utils/                   # 工具类
│   │   ├── web_scraper.py            # 网页抓取工具类
│   └── __init__.py              # FastAPI 应用初始化
│
├── main.py                      # 项目入口，启动 FastAPI 服务器
└── README.md                    # 项目说明文档
```

## 功能模块

### 1. 飞书 API 集成

项目封装了飞书的多个 API 接口，提供了对飞书文档、表格、Wiki、云盘等资源的操作功能。每个功能模块都对应一个处理器类，具体如下：

- **飞书文档 API**：`feishu_docx_api_handler.py`
  - 创建、读取、更新、删除文档中的块（block）。
  - 批量更新文档块。
  
- **飞书多维表格 API**：`feishu_bitable_api_handler.py`
  - 创建表格、获取记录、更新记录、删除记录。
  - 批量操作表格记录。
  
- **飞书云盘 API**：`feishu_drive_api_handler.py`
  - 创建文件夹、获取文件夹中的文件列表。

- **飞书 Wiki API**：`feishu_app_api.py`
  - 获取 Wiki 空间列表、创建空间、获取节点信息等。

### 2. 网页抓取工具

项目提供了一个通用的网页抓取工具，支持根据不同的 URL 规则抓取网页内容。该工具支持自定义请求头和解析规则，适用于小红书、微信公众号等特定网站的内容抓取。

- **网页抓取 API**：`scraper.py`
  - 提供 `/fetch_web_content` 路由，用户可以通过传递 URL 参数来抓取指定网页的内容。
  - 支持自定义 URL 规则和请求头。

### 3. API 密钥验证与请求来源验证

项目通过 `dependencies.py` 文件中的依赖项，提供了 API 密钥验证和请求来源验证功能，确保 API 的安全性。

- **API 密钥验证**：`verify_api_key`
  - 验证请求头中的 API 密钥是否与环境变量中的密钥匹配。
  
- **请求来源验证**：`verify_local_request`
  - 验证请求是否来自本地（`127.0.0.1`、`localhost`、`::1`）。

## 安装与运行

### 1. 克隆项目

```bash
git clone https://github.com/imjszhang/feishu-xiaobao.git
cd feishu-xiaobao
```

### 2. 安装依赖

项目依赖于 `FastAPI`、`requests`、`beautifulsoup4` 等库。你可以通过以下命令安装所有依赖：

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

在项目根目录下创建 `.env` 文件，并配置以下环境变量：

```bash
API_KEY=your_api_key
FEISHU_APP_ID=your_feishu_app_id
FEISHU_APP_SECRET=your_feishu_app_secret
XHS_A1=your_xiaohongshu_a1
XHS_WEB_SESSION=your_xiaohongshu_web_session
```

### 4. 运行项目

#### 通过 `main.py` 启动

项目的入口文件是 `main.py`，它会启动 FastAPI 服务器并在后台运行。

```bash
python main.py
```

`main.py` 的主要功能是：

- 设置日志配置。
- 实例化 `API` 类（从 `api/api.py` 导入）。
- 启动 FastAPI 服务器并在后台运行。
- 保持主线程运行，直到用户手动停止程序。

#### 通过 `uvicorn` 启动

你也可以直接使用 `uvicorn` 启动 FastAPI 应用：

```bash
uvicorn api.app:app --reload
```

应用将会在 `http://127.0.0.1:8000` 运行。

## API 文档

FastAPI 提供了自动生成的 API 文档。启动项目后，你可以通过以下地址访问 Swagger UI：

```
http://127.0.0.1:8000/docs
```

## 示例

### 1. 飞书文档 API 示例

通过以下 API 创建一个新的飞书文档：

```bash
POST /feishu/docx/create
```

请求体：

```json
{
  "title": "新文档标题",
  "folder_token": "your_folder_token"
}
```

### 2. 网页抓取 API 示例

通过以下 API 抓取网页内容：

```bash
GET /fetch_web_content?url=https://www.xiaohongshu.com/explore/your_post_id
```

返回示例：

```json
{
  "title": "小红书帖子标题",
  "content": "帖子内容",
  "images": ["image_url_1", "image_url_2"],
  "likes": 1234,
  "comments": 567
}
```

## 贡献指南

如果你想为本项目做出贡献，请遵循以下步骤：

1. Fork 本仓库。
2. 创建一个新的分支：`git checkout -b feature/your-feature-name`。
3. 提交你的更改：`git commit -m 'Add some feature'`。
4. 推送到分支：`git push origin feature/your-feature-name`。
5. 提交 Pull Request。

## 许可证

本项目使用 [MIT 许可证](LICENSE)。

---

感谢你对本项目的关注！如果你有任何问题或建议，请随时提交 Issue。