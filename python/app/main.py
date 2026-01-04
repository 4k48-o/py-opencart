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
    attribute_group, attribute, option, option_value, category, product
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


@app.on_event("startup")
async def startup_event():
    """Initialize database and Redis on startup"""
    await init_db()
    
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

