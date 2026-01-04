# 测试组文档

> 📚 **测试组所有文档已迁移到此目录**

---

## ⚠️ 重要提醒

**编写测试脚本前，必须先阅读以下文档：**

1. **[测试脚本开发注意事项](./TEST_SCRIPT_DEVELOPMENT_GUIDELINES.md)** ⭐ **必读**
   - 总结了所有常见错误和最佳实践
   - 包含完整的检查清单
   - **编写测试脚本前必须阅读**

2. **[测试脚本失败原因总结](./TEST_SCRIPT_FAILURE_SUMMARY.md)** ⭐ **必读**
   - 所有失败原因的详细总结
   - 预防措施和修复方法
   - **避免重复犯错**

---

## 📚 文档目录

### ⚠️ 必读文档（编写测试脚本前）

1. **[测试脚本开发注意事项](./TEST_SCRIPT_DEVELOPMENT_GUIDELINES.md)** ⭐ **最重要**
   - 编写测试脚本前必须阅读
   - 总结了所有常见错误和最佳实践
   - 包含完整的检查清单

2. **[测试脚本失败原因总结](./TEST_SCRIPT_FAILURE_SUMMARY.md)** ⭐ **重要**
   - 所有失败原因的详细总结
   - 预防措施和修复方法

3. **[测试脚本快速参考](./TEST_SCRIPT_QUICK_REFERENCE.md)**
   - 快速检查清单
   - 常见错误快速修复

### 📋 配置和执行文档

4. **[测试数据库配置](../数据库组/01-数据库设计文档.md)**
   - 测试数据库配置指南
   - 数据库连接信息

5. **[测试配置说明](../python/tests/test_config.py)**
   - 测试配置和常量定义
   - 测试套件定义

### 📊 测试报告文档

6. **[AttributeGroup 测试错误分析](./ATTRIBUTE_GROUP_TEST_ERROR_ANALYSIS.md)**
   - AttributeGroup 错误分析

7. **[AttributeGroup 测试修复报告](./ATTRIBUTE_GROUP_TEST_FIXES.md)**
   - AttributeGroup 修复详情

8. **[AttributeGroup 测试修复完成报告](./ATTRIBUTE_GROUP_TEST_FIXES_COMPLETE.md)**
   - AttributeGroup 修复完成报告

9. **[AttributeGroup 测试最终总结](./ATTRIBUTE_GROUP_TEST_FINAL_SUMMARY.md)**
   - AttributeGroup 最终总结

10. **[AttributeGroup 测试最终状态](./ATTRIBUTE_GROUP_TEST_FINAL_STATUS.md)**
    - AttributeGroup 最终状态

11. **[422错误分析报告](./422_ERROR_ANALYSIS_REPORT.md)**
    - 422错误详细分析

12. **[422错误总结（给开发组）](./422_ERROR_SUMMARY_FOR_DEV.md)**
    - 422错误总结

---

## 🚀 快速开始

### 编写新模块的测试脚本

1. **阅读注意事项**：
   ```bash
   # 必须首先阅读
   cat "ai task/测试组/TEST_SCRIPT_DEVELOPMENT_GUIDELINES.md"
   ```

2. **检查权限配置**：
   - 在 `python/tests/conftest.py` 的 `test_user_group` fixture 中添加新模块权限

3. **编写测试用例**：
   - 基础校验测试（数据验证）
   - 逻辑校验测试（业务逻辑）
   - API具体业务测试（接口测试）

4. **运行测试**：
   ```bash
   cd python
   python -m pytest tests/test_[module]_api.py -v
   ```

---

## 🔧 测试工具

### 测试套件编排
```bash
cd python
# 列出所有可用测试套件
python scripts/run_test_suite.py --list

# 运行特定测试套件
python scripts/run_test_suite.py smoke
python scripts/run_test_suite.py regression
python scripts/run_test_suite.py attribute_group
```

### Makefile 命令
```bash
cd python
make test-smoke          # 执行冒烟测试
make test-regression     # 执行回归测试
make test-api            # 执行API接口测试
make test-all            # 执行所有测试
make test-module MODULE=attribute_group  # 执行指定模块测试
```

---

## 📝 测试脚本开发流程

1. **阅读注意事项** → `TEST_SCRIPT_DEVELOPMENT_GUIDELINES.md`
2. **检查权限配置** → `python/tests/conftest.py`
3. **编写测试用例** → `python/tests/test_[module]_api.py`
4. **运行测试验证** → `pytest tests/test_[module]_api.py -v`
5. **检查测试报告** → `python/reports/report.html`

---

## ⚠️ 常见错误避免

### 1. 权限配置
- ❌ 忘记在 `conftest.py` 中添加新模块权限
- ✅ 每次添加新模块测试时，先检查并添加权限

### 2. 认证状态码
- ❌ 无认证测试期望 403
- ✅ 无认证测试期望 401

### 3. ORM查询
- ❌ 对复合主键模型使用 `get()` 或 `get_or_none()`
- ✅ 使用 `filter().values()` 方法

### 4. 状态码期望
- ❌ Schema 验证失败期望 400
- ✅ Schema 验证失败期望 422

### 5. 验证错误处理
- ❌ Schema 验证错误捕获 `ValidationException`
- ✅ Schema 验证错误捕获 `ValidationError`

### 6. 测试数据
- ❌ 使用硬编码的测试数据
- ✅ 使用 UUID 生成唯一数据

### 7. 异步测试
- ❌ 对 fixture 使用 `await`
- ✅ 直接使用 fixture，不需要 `await`

**详细说明请参考**：[测试脚本开发注意事项](./TEST_SCRIPT_DEVELOPMENT_GUIDELINES.md)

---

## 📞 联系方式

如有问题，请参考：
1. [测试脚本开发注意事项](./TEST_SCRIPT_DEVELOPMENT_GUIDELINES.md)
2. [测试脚本失败原因总结](./TEST_SCRIPT_FAILURE_SUMMARY.md)
3. [测试脚本快速参考](./TEST_SCRIPT_QUICK_REFERENCE.md)

---

**最后更新**：2024年1月  
**文档位置**：`ai task/测试组/`
