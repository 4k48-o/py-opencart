# OpenCart Python API

基于 FastAPI 和 Tortoise ORM 的 OpenCart 数据模型转换项目。

## 项目结构

```
python/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # Tortoise ORM 数据库连接配置
│   └── models/              # Tortoise ORM 模型（按业务域分类）
├── scripts/
│   └── generate_models.py    # 模型生成脚本
├── requirements.txt
└── README.md
```

## 环境设置

### 1. 激活虚拟环境

```bash
# 从项目根目录
source ../venv/bin/activate  # macOS/Linux
# 或
..\venv\Scripts\activate      # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置数据库

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的数据库信息。

详细设置说明请参考 [SETUP.md](./SETUP.md)

## 运行

```bash
uvicorn app.main:app --reload
```

## 生成模型

运行模型生成脚本：

```bash
python scripts/generate_models.py
```

## 业务域分类

模型按以下业务域分类组织：

- **system** - 系统业务
- **localisation** - 本地化业务
- **customer** - 客户业务
- **catalog** - 商品业务
- **order** - 订单业务
- **marketing** - 营销业务
- **cms** - CMS业务
- **design** - 设计业务
- **report** - 报表业务

