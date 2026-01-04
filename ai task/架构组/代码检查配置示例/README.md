# 代码检查配置示例

本目录包含代码检查工具的配置文件示例。

## 文件说明

- **pyproject.toml**: Black、MyPy、Pytest、Coverage 的综合配置
- **.flake8**: Flake8 代码检查配置
- **.pre-commit-config.yaml**: Pre-commit 钩子配置
- **.gitignore**: Git 忽略文件配置

## 使用方法

### 1. 复制配置文件到项目根目录

```bash
# 复制到项目根目录
cp pyproject.toml /path/to/project/
cp .flake8 /path/to/project/
cp .pre-commit-config.yaml /path/to/project/
cp .gitignore /path/to/project/
```

### 2. 安装工具

```bash
# 安装开发依赖
pip install black flake8 mypy pytest pre-commit

# 或使用 requirements-dev.txt
pip install -r requirements-dev.txt
```

### 3. 安装 Pre-commit 钩子

```bash
pre-commit install
```

### 4. 运行检查

```bash
# 格式化代码
black app/

# 检查代码
flake8 app/

# 类型检查
mypy app/

# 运行测试
pytest

# 运行所有检查（通过 pre-commit）
pre-commit run --all-files
```

## 编辑器配置

### VS Code

安装扩展：
- Python
- Black Formatter
- Pylance

配置 `.vscode/settings.json`：
```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  }
}
```

### PyCharm

1. 配置 Black 为代码格式化工具
2. 启用 Flake8 和 MyPy 检查
3. 配置自动格式化

## CI/CD 集成

在 CI/CD 流水线中添加：

```yaml
# .gitlab-ci.yml 示例
lint:
  stage: test
  script:
    - black --check app/
    - flake8 app/
    - mypy app/
  only:
    - merge_requests
```

## 注意事项

1. 配置文件需要根据项目实际情况调整
2. 某些第三方库可能缺少类型提示，需要在 mypy 配置中忽略
3. Pre-commit 钩子会在每次提交时自动运行，确保代码质量

