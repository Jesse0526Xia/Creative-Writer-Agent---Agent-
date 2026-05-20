# Creative Writer Agent - 多Agent协作写作系统

智能创意写作助手，基于大语言模型的多Agent协作系统，支持小说、文案、论文等多种文体创作。

## 核心特性

- **多Agent协作**: Planner-Writer-Reviewer-Iterator 四阶段架构
- **角色定制**: 自定义角色身份、性格、说话方式
- **RAG增强**: 支持私有素材向量化检索
- **文档解析**: Word/PDF文档自动提取角色特点
- **多轮迭代**: 智能评审与精细化修改

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# LLM API配置 (二选一)
DOUBAO_API_KEY=your_api_key_here
# 或
KIMI_API_KEY=your_api_key_here

# 数据库配置
DATABASE_URL=sqlite:///data/db/writer.db

# Embedding模型
EMBEDDING_MODEL=all-MiniLM-L6-v2

# 服务器配置
HOST=0.0.0.0
PORT=8000
```

### 3. 启动服务

```bash
# 直接运行
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Docker部署
docker-compose up --build
```

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                     API 层 (FastAPI)                     │
├─────────────────────────────────────────────────────────┤
│              Multi-Agent 协作引擎                        │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐        │
│  │Planner │→ │ Writer │→ │Reviewer│→ │Iterator│        │
│  └────────┘  └────────┘  └────────┘  └────────┘        │
├─────────────────────────────────────────────────────────┤
│                    RAG 检索引擎                          │
│              (FAISS + 角色档案 + 素材库)                 │
├─────────────────────────────────────────────────────────┤
│                  LLM 调用层 (豆包/Kimi)                  │
└─────────────────────────────────────────────────────────┘
```

## API接口

### 写作接口
```bash
POST /api/write
{
    "task_type": "novel",
    "topic": "一段都市爱情故事",
    "style": "文艺清新",
    "character_ids": ["char_001"],
    "iterations": 3
}
```

### 角色管理
```bash
# 创建角色
POST /api/character/create

# 从文档提取角色
POST /api/character/from-document
```

### 素材管理
```bash
# 上传素材
POST /api/material/upload

# 检索相似素材
GET /api/material/search?query=关键词
```

## 项目结构

```
creative-writer-agent/
├── app/                    # FastAPI应用
│   ├── api/routes/        # API路由
│   └── main.py            # 应用入口
├── core/                  # 核心模块
│   ├── agents/           # 多Agent系统
│   ├── rag/               # RAG检索
│   ├── character/         # 角色系统
│   ├── parser/            # 文档解析
│   └── llm/               # LLM调用
├── models/                # 数据模型
├── data/                  # 数据存储
└── static/                # 静态文件
```

## License

MIT
