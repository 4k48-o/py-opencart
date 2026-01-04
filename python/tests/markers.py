"""
测试标记定义和使用规范

本模块定义了项目中使用的所有 pytest 标记常量，用于测试用例的分类和管理。
"""

# 模块标记
MARK_STORE = "store"
MARK_USER = "user"
MARK_SETTING = "setting"
MARK_LANGUAGE = "language"
MARK_CURRENCY = "currency"
MARK_AUTH = "auth"
MARK_OPTION = "option"
MARK_OPTION_VALUE = "option_value"
MARK_CATEGORY = "category"
MARK_PRODUCT = "product"
MARK_PERMISSION = "permission"
MARK_SERVICE = "service"
MARK_BUSINESS = "business"

# 测试类型标记
MARK_SMOKE = "smoke"
MARK_REGRESSION = "regression"
MARK_API = "api"
MARK_MODEL = "model"
MARK_INTEGRATION = "integration"
MARK_PERFORMANCE = "performance"

# 优先级标记
MARK_CRITICAL = "critical"
MARK_HIGH = "high"
MARK_MEDIUM = "medium"
MARK_LOW = "low"

# 其他标记
MARK_SLOW = "slow"

# 测试套件组合标记（用于快速选择测试套件）
TEST_SUITES = {
    "smoke": {
        "markers": [MARK_SMOKE, MARK_CRITICAL],
        "description": "冒烟测试 - 快速验证核心功能",
        "expected_time": "< 5分钟"
    },
    "regression": {
        "markers": [MARK_REGRESSION],
        "description": "回归测试 - 完整功能测试",
        "expected_time": "< 30分钟"
    },
    "api": {
        "markers": [MARK_API],
        "description": "API接口测试",
        "expected_time": "< 20分钟"
    },
    "integration": {
        "markers": [MARK_INTEGRATION],
        "description": "集成测试 - 验证模块间集成",
        "expected_time": "< 15分钟"
    },
    "model": {
        "markers": [MARK_MODEL],
        "description": "数据模型测试",
        "expected_time": "< 10分钟"
    },
    "performance": {
        "markers": [MARK_PERFORMANCE],
        "description": "性能测试",
        "expected_time": "根据测试规模而定"
    }
}

# 模块测试套件
MODULE_SUITES = {
    "store": {
        "markers": [MARK_STORE],
        "description": "Store模块测试"
    },
    "user": {
        "markers": [MARK_USER],
        "description": "User模块测试"
    },
    "setting": {
        "markers": [MARK_SETTING],
        "description": "Setting模块测试"
    },
    "language": {
        "markers": [MARK_LANGUAGE],
        "description": "Language模块测试"
    },
    "currency": {
        "markers": [MARK_CURRENCY],
        "description": "Currency模块测试"
    },
    "auth": {
        "markers": [MARK_AUTH],
        "description": "认证授权模块测试"
    },
    "attribute_group": {
        "markers": ["attribute_group"],
        "description": "AttributeGroup模块测试"
    },
    "option": {
        "markers": [MARK_OPTION],
        "description": "Option模块测试"
    },
    "option_value": {
        "markers": [MARK_OPTION_VALUE],
        "description": "OptionValue模块测试"
    },
    "category": {
        "markers": [MARK_CATEGORY],
        "description": "Category模块测试"
    },
    "product": {
        "markers": [MARK_PRODUCT],
        "description": "Product模块测试"
    }
}


def get_suite_markers(suite_name: str) -> list:
    """
    获取测试套件的标记列表
    
    Args:
        suite_name: 测试套件名称
        
    Returns:
        标记列表
    """
    if suite_name in TEST_SUITES:
        return TEST_SUITES[suite_name]["markers"]
    elif suite_name in MODULE_SUITES:
        return MODULE_SUITES[suite_name]["markers"]
    else:
        return []


def get_suite_description(suite_name: str) -> str:
    """
    获取测试套件的描述
    
    Args:
        suite_name: 测试套件名称
        
    Returns:
        套件描述
    """
    if suite_name == "all":
        return "执行所有测试"
    elif suite_name in TEST_SUITES:
        return TEST_SUITES[suite_name]["description"]
    elif suite_name in MODULE_SUITES:
        return MODULE_SUITES[suite_name]["description"]
    else:
        return f"未知测试套件: {suite_name}"

