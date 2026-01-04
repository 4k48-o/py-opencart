.PHONY: help test test-smoke test-regression test-api test-all test-coverage test-parallel clean-reports install-test-deps

# 默认目标
help:
	@echo "OpenCart FastAPI 测试命令"
	@echo ""
	@echo "可用命令:"
	@echo "  make test-smoke          - 执行冒烟测试（快速验证核心功能）"
	@echo "  make test-regression     - 执行回归测试（完整功能测试）"
	@echo "  make test-api            - 执行API接口测试"
	@echo "  make test-all            - 执行所有测试"
	@echo "  make test-coverage       - 生成覆盖率报告"
	@echo "  make test-parallel       - 并行执行所有测试"
	@echo "  make test-module MODULE=store - 执行指定模块测试（store/user/setting/language/currency）"
	@echo "  make clean-reports       - 清理测试报告"
	@echo "  make install-test-deps   - 安装测试依赖"
	@echo ""

# 执行冒烟测试
test-smoke:
	@echo "执行冒烟测试..."
	python scripts/run_test_suite.py smoke

# 执行回归测试
test-regression:
	@echo "执行回归测试..."
	python scripts/run_test_suite.py regression

# 执行API测试
test-api:
	@echo "执行API接口测试..."
	python scripts/run_test_suite.py api

# 执行所有测试
test-all:
	@echo "执行所有测试..."
	python scripts/run_test_suite.py all

# 生成覆盖率报告
test-coverage:
	@echo "生成覆盖率报告..."
	pytest --cov=app --cov-report=html:reports/coverage --cov-report=term-missing
	@echo "覆盖率报告已生成: reports/coverage/index.html"

# 并行执行所有测试
test-parallel:
	@echo "并行执行所有测试..."
	python scripts/run_test_suite.py all --parallel

# 执行指定模块测试
test-module:
	@if [ -z "$(MODULE)" ]; then \
		echo "错误: 请指定模块名称 (MODULE=store/user/setting/language/currency)"; \
		exit 1; \
	fi
	@echo "执行 $(MODULE) 模块测试..."
	python scripts/run_test_suite.py $(MODULE)

# 清理测试报告
clean-reports:
	@echo "清理测试报告..."
	rm -rf reports/*.html reports/*.json reports/coverage reports/coverage_*
	@echo "测试报告已清理"

# 安装测试依赖
install-test-deps:
	@echo "安装测试依赖..."
	pip install -r requirements.txt

# 列出所有可用测试套件
test-list:
	@python scripts/run_test_suite.py --list

# 测试数据库连接
test-db:
	@echo "测试数据库连接..."
	@python scripts/test_db_connection.py

# 测试Redis连接
test-redis:
	@echo "测试Redis连接..."
	@python scripts/test_redis_connection.py

