"""
测试配置和常量定义
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 测试报告目录
REPORTS_DIR = PROJECT_ROOT / "reports"
COVERAGE_DIR = REPORTS_DIR / "coverage"

# 确保报告目录存在
REPORTS_DIR.mkdir(exist_ok=True)
COVERAGE_DIR.mkdir(exist_ok=True)

# 测试数据库配置
TEST_DB_NAME_SUFFIX = "_test"

# 测试数据配置
TEST_USER_USERNAME = "testadmin"
TEST_USER_PASSWORD = "testpass123"
TEST_USER_EMAIL = "testadmin@example.com"

# 测试超时配置（秒）
TEST_TIMEOUT = 300  # 5分钟

# 并行测试配置
DEFAULT_WORKERS = 4

# 测试标记配置
from tests.markers import (
    TEST_SUITES,
    MODULE_SUITES,
    get_suite_markers,
    get_suite_description
)

__all__ = [
    "PROJECT_ROOT",
    "REPORTS_DIR",
    "COVERAGE_DIR",
    "TEST_DB_NAME_SUFFIX",
    "TEST_USER_USERNAME",
    "TEST_USER_PASSWORD",
    "TEST_USER_EMAIL",
    "TEST_TIMEOUT",
    "DEFAULT_WORKERS",
    "TEST_SUITES",
    "MODULE_SUITES",
    "get_suite_markers",
    "get_suite_description",
]

