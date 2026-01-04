"""
Authentication service
"""
import logging
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, List
from app.models.system.user import User
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token
)
from app.core.permissions import get_user_permissions
from app.core.redis_client import get_redis_client
from app.config import settings
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务"""
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        验证用户
        
        Args:
            username: 用户名
            password: 明文密码
            
        Returns:
            Optional[User]: 验证成功返回User实例，失败返回None
        """
        logger.info(f"开始验证用户: username={username}")
        try:
            # 使用 filter().first() 代替 get_or_none()，避免 Multiple objects returned 错误
            user = await User.filter(username=username, status=1).first()
            if not user:
                logger.warning(f"用户不存在或已禁用: username={username}")
                return None
            
            # 验证密码
            # 兼容旧数据（如果密码是明文，第一次登录时应该更新为哈希）
            password_valid = False
            try:
                # 尝试使用bcrypt验证
                password_valid = verify_password(password, user.password)
            except Exception:
                # 如果验证失败，可能是旧数据（明文密码）
                # 这里为了向后兼容，暂时允许明文密码，但应该尽快迁移
                if user.password == password:
                    logger.warning(f"用户使用明文密码（应尽快迁移）: username={username}")
                    password_valid = True
            
            if not password_valid:
                logger.warning(f"密码错误: username={username}")
                return None
            
            logger.info(f"用户验证成功: user_id={user.user_id}, username={username}")
            return user
        except Exception as e:
            logger.error(f"验证用户失败: username={username}, error={str(e)}")
            return None
    
    async def create_tokens(
        self,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, str]:
        """
        创建Token（Access Token和Refresh Token）
        
        Args:
            user: User模型实例
            ip_address: IP地址（可选，用于安全审计）
            user_agent: 用户代理（可选，用于安全审计）
            
        Returns:
            Dict[str, str]: 包含access_token和refresh_token的字典
        """
        logger.info(f"开始创建Token: user_id={user.user_id}")
        try:
            # 获取用户权限
            permissions = await get_user_permissions(user)
            
            # 创建 Access Token（添加 jti 确保每次生成的 token 都不同）
            access_token_data = {
                "sub": str(user.user_id),
                "username": user.username or "",
                "email": user.email or "",
                "user_group_id": user.user_group_id or 0,
                "permissions": permissions,
                "jti": str(uuid.uuid4())  # JWT ID，确保每次生成的 token 都不同
            }
            access_token = create_access_token(access_token_data)
            
            # 创建 Refresh Token
            token_id = str(uuid.uuid4())
            refresh_token_data = {
                "sub": str(user.user_id),
                "token_id": token_id
            }
            refresh_token = create_refresh_token(refresh_token_data)
            
            # 将Refresh Token存储到Redis（使用Hash结构存储更多元数据）
            await self._store_refresh_token_to_redis(token_id, user.user_id, ip_address, user_agent)
            
            logger.info(f"Token创建成功: user_id={user.user_id}")
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
        except Exception as e:
            logger.error(f"创建Token失败: user_id={user.user_id}, error={str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create tokens"
            )
    
    async def refresh_access_token(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, str]:
        """
        刷新Access Token
        
        Args:
            refresh_token: Refresh Token字符串
            ip_address: IP地址（可选，用于安全审计）
            user_agent: 用户代理（可选，用于安全审计）
            
        Returns:
            Dict[str, str]: 包含新的access_token和refresh_token的字典
            
        Raises:
            HTTPException: Token无效或过期
        """
        logger.info("开始刷新Access Token")
        try:
            payload = verify_token(refresh_token)
            
            if payload.get("type") != "refresh":
                logger.warning("Refresh Token类型错误")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token type",
                )
            
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token missing user ID",
                )
            
            # 验证Refresh Token是否在Redis中存在（未撤销）
            token_id = payload.get("token_id")
            if token_id:
                is_valid = await self._verify_refresh_token_in_redis(token_id, user_id)
                if not is_valid:
                    logger.warning(f"Refresh Token不存在或已撤销: token_id={token_id}, user_id={user_id}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Refresh token not found or expired",
                    )
            
            # 撤销旧的Refresh Token（滚动刷新）
            if token_id:
                await self._revoke_refresh_token(token_id, user_id)
            
            user = await User.get_or_none(user_id=int(user_id), status=1)
            if not user:
                logger.warning(f"用户不存在或已禁用: user_id={user_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or disabled",
                )
            
            # 创建新的Token（传递IP和User-Agent用于安全审计）
            logger.info(f"Access Token刷新成功: user_id={user_id}")
            return await self.create_tokens(user, ip_address=ip_address, user_agent=user_agent)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"刷新Access Token失败: error={str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to refresh token"
            )
    
    async def revoke_token(self, refresh_token: str) -> bool:
        """
        撤销Token（登出）
        
        Args:
            refresh_token: Refresh Token字符串
            
        Returns:
            bool: 是否撤销成功
        """
        logger.info("开始撤销Token")
        try:
            payload = verify_token(refresh_token)
            token_id = payload.get("token_id")
            user_id = payload.get("sub")
            
            if token_id:
                return await self._revoke_refresh_token(token_id, user_id)
            return False
        except Exception as e:
            logger.error(f"撤销Token失败: error={str(e)}")
            return False
    
    async def revoke_all_user_tokens(self, user_id: int) -> int:
        """
        撤销用户的所有Refresh Token（用于修改密码、管理员操作等场景）
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 撤销的Token数量
        """
        logger.info(f"开始撤销用户所有Token: user_id={user_id}")
        try:
            redis_client = await get_redis_client()
            if not redis_client:
                logger.warning("Redis不可用，无法撤销Token")
                return 0
            
            # 获取用户的所有token_id
            token_ids = await redis_client.smembers(f"user:{user_id}:tokens")
            if not token_ids:
                logger.info(f"用户没有活跃的Token: user_id={user_id}")
                return 0
            
            # 批量删除token
            deleted_count = 0
            for token_id in token_ids:
                if await self._revoke_refresh_token(token_id, str(user_id)):
                    deleted_count += 1
            
            # 删除用户token索引
            await redis_client.delete(f"user:{user_id}:tokens")
            
            logger.info(f"用户所有Token撤销完成: user_id={user_id}, count={deleted_count}")
            return deleted_count
        except Exception as e:
            logger.error(f"撤销用户所有Token失败: user_id={user_id}, error={str(e)}")
            return 0
    
    # ==================== 私有方法：Redis Token管理 ====================
    
    async def _store_refresh_token_to_redis(
        self,
        token_id: str,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        将Refresh Token存储到Redis（使用Hash结构存储元数据）
        
        Args:
            token_id: Token唯一标识
            user_id: 用户ID
            ip_address: IP地址（可选）
            user_agent: 用户代理（可选）
            
        Returns:
            bool: 是否存储成功
        """
        try:
            redis_client = await get_redis_client()
            if not redis_client:
                logger.warning("Redis不可用，Refresh Token未存储，撤销功能将不可用")
                return False
            
            expire_seconds = settings.refresh_token_expire_days * 24 * 60 * 60
            created_at = datetime.utcnow().isoformat()
            
            # 使用Hash结构存储更多元数据
            token_key = f"refresh_token:{token_id}"
            token_data = {
                "user_id": str(user_id),
                "created_at": created_at,
                "ip_address": ip_address or "",
                "user_agent": user_agent or ""
            }
            
            # 存储token元数据
            await redis_client.hset(token_key, mapping=token_data)
            await redis_client.expire(token_key, expire_seconds)
            
            # 将token_id添加到用户的token集合中（用于批量撤销）
            user_tokens_key = f"user:{user_id}:tokens"
            await redis_client.sadd(user_tokens_key, token_id)
            await redis_client.expire(user_tokens_key, expire_seconds)
            
            logger.info(f"Refresh Token已存储到Redis: token_id={token_id}, user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"存储Refresh Token到Redis失败: {str(e)}")
            # 如果Redis不可用，仍然返回Token（降级处理）
            logger.warning("Redis不可用，Refresh Token未存储，撤销功能将不可用")
            return False
    
    async def _verify_refresh_token_in_redis(self, token_id: str, user_id: str) -> bool:
        """
        验证Refresh Token是否在Redis中存在且有效
        
        Args:
            token_id: Token唯一标识
            user_id: 用户ID
            
        Returns:
            bool: Token是否有效
        """
        try:
            redis_client = await get_redis_client()
            if not redis_client:
                # 如果Redis不可用，降级处理：仅验证JWT有效性
                logger.debug("Redis不可用，跳过Refresh Token验证")
                return True
            
            # 从Hash中获取user_id
            token_key = f"refresh_token:{token_id}"
            stored_user_id = await redis_client.hget(token_key, "user_id")
            
            if not stored_user_id or stored_user_id != str(user_id):
                return False
            
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"验证Refresh Token失败: {str(e)}")
            # 如果Redis不可用，降级处理：仅验证JWT有效性
            logger.warning("Redis不可用，跳过Refresh Token验证")
            return True
    
    async def _revoke_refresh_token(self, token_id: str, user_id: Optional[str] = None) -> bool:
        """
        撤销单个Refresh Token
        
        Args:
            token_id: Token唯一标识
            user_id: 用户ID（可选，用于从用户token集合中删除）
            
        Returns:
            bool: 是否撤销成功
        """
        try:
            redis_client = await get_redis_client()
            if not redis_client:
                logger.warning("Redis不可用，无法撤销Token")
                return False
            
            # 如果提供了user_id，先从用户token集合中删除
            if user_id:
                user_tokens_key = f"user:{user_id}:tokens"
                await redis_client.srem(user_tokens_key, token_id)
            
            # 删除token
            token_key = f"refresh_token:{token_id}"
            deleted = await redis_client.delete(token_key)
            
            if deleted:
                logger.info(f"Token撤销成功: token_id={token_id}")
                return True
            else:
                logger.warning(f"Token不存在或已过期: token_id={token_id}")
                return False
        except Exception as e:
            logger.error(f"撤销Token失败: {str(e)}")
            return False

