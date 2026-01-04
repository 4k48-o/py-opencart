"""
Redis client for JWT token management
"""
import logging
from typing import Optional
try:
    import redis.asyncio as aioredis
except ImportError:
    # Fallback for older redis versions
    try:
        import aioredis
    except ImportError:
        aioredis = None
        logging.warning("Redis客户端未安装，JWT Token撤销功能将不可用")

from app.config import settings

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client = None


async def get_redis_client():
    """
    获取 Redis 客户端实例（单例模式）
    
    Returns:
        Redis客户端实例，如果连接失败返回None
    
    Note:
        如果Redis不可用，返回None，调用者需要检查None值
    """
    global _redis_client
    
    if aioredis is None:
        logger.warning("Redis客户端未安装，JWT Token撤销功能将不可用")
        return None
    
    if _redis_client is None:
        try:
            # 构建Redis连接URL
            if settings.redis_password:
                redis_url = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
            else:
                redis_url = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
            
            _redis_client = aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=settings.redis_decode_responses,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            # 测试连接
            await _redis_client.ping()
            logger.info(f"Redis 连接成功: {settings.redis_host}:{settings.redis_port}")
        except Exception as e:
            logger.error(f"Redis 连接失败: {str(e)}")
            # 不抛出异常，允许应用在没有Redis的情况下运行（JWT撤销功能将不可用）
            _redis_client = None
            return None
    
    return _redis_client


async def close_redis_client():
    """
    关闭 Redis 客户端连接
    """
    global _redis_client
    
    if _redis_client is not None:
        try:
            await _redis_client.close()
            logger.info("Redis 连接已关闭")
        except Exception as e:
            logger.error(f"关闭 Redis 连接失败: {str(e)}")
        finally:
            _redis_client = None


async def redis_health_check() -> bool:
    """
    检查 Redis 连接健康状态
    
    Returns:
        bool: 连接正常返回 True，否则返回 False
    """
    try:
        client = await get_redis_client()
        if client is None:
            return False
        result = await client.ping()
        return result is True
    except Exception as e:
        logger.error(f"Redis 健康检查失败: {str(e)}")
        return False

