"""
FastAPI application entry point
"""
import logging
from fastapi import FastAPI
from app.config import settings
from app.database import init_db, close_db
from app.core.redis_client import close_redis_client
from app.routers import (
    store, user, auth, api_key, setting, language, currency,
    attribute_group, attribute, option, option_value, category, product, manufacturer
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="OpenCart API - FastAPI + Tortoise ORM",
)

# Register routers
app.include_router(auth.router)  # 认证路由（登录、登出等，不需要认证）
app.include_router(store.router)  # Store API
app.include_router(user.router)  # User API
app.include_router(api_key.router)  # API Key API
app.include_router(setting.router)  # Setting API
app.include_router(language.router)  # Language API
app.include_router(currency.router)  # Currency API

# Phase 2 - 第一优先级API
app.include_router(attribute_group.router)  # AttributeGroup API
app.include_router(attribute.router)  # Attribute API
app.include_router(option.router)  # Option API
app.include_router(option_value.router)  # OptionValue API
app.include_router(category.router)  # Category API

# Phase 2 - 第二优先级API（商品核心API）
app.include_router(product.router)  # Product API

# Phase 2 - 中优先级API
app.include_router(manufacturer.router)  # Manufacturer API


@app.on_event("startup")
async def startup_event():
    """Initialize database and Redis on startup
    
    注意：在测试环境中，db_setup fixture已经初始化了Tortoise ORM。
    为了统一数据库连接，避免双重连接导致的事务隔离问题，测试环境跳过init_db()。
    这是架构组推荐方案2的实现：测试环境禁用init_db()，确保测试和API使用同一个连接。
    """
    import os
    
    # 在测试环境中，db_setup已经初始化了数据库，跳过init_db()
    # 使用环境变量判断是否在测试环境
    # 注意：TESTING环境变量在pytest会话开始时通过set_testing_env fixture设置
    testing_env = os.getenv("TESTING")
    pytest_current = os.getenv("PYTEST_CURRENT_TEST")
    pytest_env = os.getenv("PYTEST")
    
    logger.info(f"startup_event环境变量检查: TESTING={testing_env}, PYTEST_CURRENT_TEST={pytest_current}, PYTEST={pytest_env}")
    
    is_testing = (
        pytest_current is not None or 
        testing_env == "1" or
        pytest_env == "1"
    )
    
    logger.info(f"startup_event is_testing={is_testing}")
    
    if is_testing:
        logger.info("✅ 测试环境，跳过数据库初始化（使用db_setup的连接）")
        # 测试环境不调用init_db()，使用db_setup创建的连接
    else:
        logger.info("FastAPI startup事件触发，开始初始化数据库...")
        await init_db()
        logger.info("FastAPI startup事件完成，数据库初始化完成")
    
    # 初始化Redis连接（测试连接）
    try:
        from app.core.redis_client import get_redis_client, redis_health_check
        health = await redis_health_check()
        if health:
            logger.info("Redis连接正常")
        else:
            logger.warning("Redis连接异常，JWT Token撤销功能可能不可用")
    except Exception as e:
        logger.warning(f"Redis初始化失败: {str(e)}，JWT Token撤销功能将不可用")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database and Redis connections on shutdown"""
    await close_db()
    await close_redis_client()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "OpenCart API",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

