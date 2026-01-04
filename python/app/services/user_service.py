"""
User service - 用户服务层
"""
import json
import logging
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from tortoise.exceptions import DoesNotExist, IntegrityError

try:
    from app.models.system.user import User
    from app.models.system.user_group import UserGroup
    from app.models.system.user_login import UserLogin
except (ImportError, AttributeError):
    import importlib
    user_module = importlib.import_module('app.models.system.user')
    User = user_module.User
    user_group_module = importlib.import_module('app.models.system.user_group')
    UserGroup = user_group_module.UserGroup
    user_login_module = importlib.import_module('app.models.system.user_login')
    UserLogin = user_login_module.UserLogin

from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse,
    UserGroupCreate, UserGroupUpdate, UserGroupResponse,
    PermissionUpdate, PermissionListResponse, UserActivityResponse
)
from app.services.base_service import BaseService
from app.exceptions import NotFoundException, ConflictException, ValidationException
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)


class UserService(BaseService):
    """用户服务"""
    
    # ==================== 用户管理 ====================
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[int] = None,
        user_group_id: Optional[int] = None
    ) -> List[UserResponse]:
        """
        获取用户列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            status: 状态筛选（可选，0=禁用，1=启用）
            user_group_id: 用户组ID筛选（可选）
            
        Returns:
            List[UserResponse]: 用户列表
        """
        logger.info(f"开始获取用户列表: skip={skip}, limit={limit}")
        try:
            query = User.all()
            
            if status is not None:
                query = query.filter(status=status)
            if user_group_id is not None:
                query = query.filter(user_group_id=user_group_id)
            
            users = await query.offset(skip).limit(limit)
            result = [UserResponse.model_validate(user) for user in users]
            
            logger.info(f"用户列表获取完成: count={len(result)}")
            return result
        except Exception as e:
            logger.error(f"获取用户列表失败: {str(e)}")
            raise
    
    async def get_user(self, user_id: int) -> UserResponse:
        """
        根据ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            UserResponse: 用户信息
            
        Raises:
            NotFoundException: 用户不存在
        """
        logger.info(f"开始获取用户信息: user_id={user_id}")
        try:
            user = await User.get_or_none(user_id=user_id)
            if not user:
                raise NotFoundException("用户", user_id)
            
            logger.info(f"用户信息获取完成: user_id={user_id}")
            return UserResponse.model_validate(user)
        except NotFoundException:
            raise
        except DoesNotExist:
            raise NotFoundException("用户", user_id)
        except Exception as e:
            logger.error(f"获取用户信息失败: user_id={user_id}, error={str(e)}")
            raise
    
    async def create_user(self, data: UserCreate) -> UserResponse:
        """
        创建新用户
        
        Args:
            data: 用户创建数据
            
        Returns:
            UserResponse: 创建的用户信息
            
        Raises:
            ConflictException: 用户名或邮箱已存在
            ValidationException: 验证失败
        """
        logger.info(f"开始创建用户: username={data.username}")
        try:
            # 验证用户名唯一性
            if not await self._validate_username_uniqueness(data.username):
                raise ConflictException(f"用户名 {data.username} 已存在")
            
            # 验证邮箱唯一性
            existing_email = await User.filter(email=data.email).first()
            if existing_email:
                raise ConflictException(f"邮箱 {data.email} 已存在")
            
            # 验证邮箱格式
            if not await self._validate_email(data.email):
                raise ValidationException(f"无效的邮箱格式: {data.email}")
            
            # 检查用户组是否存在
            user_group = await UserGroup.get_or_none(user_group_id=data.user_group_id)
            if not user_group:
                raise ValidationException(f"用户组ID {data.user_group_id} 不存在")
            
            # 创建用户（密码哈希处理）
            user_dict = data.model_dump(exclude={'password'})
            user_dict['password'] = get_password_hash(data.password)
            user_dict['date_added'] = datetime.now()
            
            user = await User.create(**user_dict)
            logger.info(f"用户创建完成: user_id={user.user_id}, username={data.username}")
            return UserResponse.model_validate(user)
        except (ConflictException, ValidationException, NotFoundException):
            raise
        except IntegrityError as e:
            logger.error(f"创建用户失败（完整性错误）: {str(e)}")
            raise ConflictException(f"创建用户失败: {str(e)}")
        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}")
            raise
    
    async def update_user(
        self,
        user_id: int,
        data: UserUpdate
    ) -> UserResponse:
        """
        更新用户
        
        Args:
            user_id: 用户ID
            data: 用户更新数据
            
        Returns:
            UserResponse: 更新后的用户信息
            
        Raises:
            NotFoundException: 用户不存在
            ConflictException: 用户名或邮箱冲突
            ValidationException: 验证失败
        """
        logger.info(f"开始更新用户: user_id={user_id}")
        try:
            user = await User.get_or_none(user_id=user_id)
            if not user:
                raise NotFoundException("用户", user_id)
            
            update_data = data.model_dump(exclude_unset=True, exclude={'password'})
            
            if not update_data and not data.password:
                raise ValidationException("没有需要更新的字段")
            
            # 如果更新用户名，检查是否重复
            if 'username' in update_data and update_data['username'] != user.username:
                if not await self._validate_username_uniqueness(update_data['username'], exclude_id=user_id):
                    raise ConflictException(f"用户名 {update_data['username']} 已存在")
            
            # 如果更新邮箱，检查是否重复并验证格式
            if 'email' in update_data and update_data['email'] != user.email:
                existing_email = await User.filter(email=update_data['email']).first()
                if existing_email and existing_email.user_id != user_id:
                    raise ConflictException(f"邮箱 {update_data['email']} 已存在")
                
                if not await self._validate_email(update_data['email']):
                    raise ValidationException(f"无效的邮箱格式: {update_data['email']}")
            
            # 如果更新用户组，检查用户组是否存在
            if 'user_group_id' in update_data:
                user_group = await UserGroup.get_or_none(user_group_id=update_data['user_group_id'])
                if not user_group:
                    raise ValidationException(f"用户组ID {update_data['user_group_id']} 不存在")
            
            # 更新字段
            for key, value in update_data.items():
                setattr(user, key, value)
            
            # 如果更新密码，需要哈希处理
            if data.password:
                user.password = get_password_hash(data.password)
            
            await user.save()
            logger.info(f"用户更新完成: user_id={user_id}")
            return UserResponse.model_validate(user)
        except (NotFoundException, ConflictException, ValidationException):
            raise
        except DoesNotExist:
            raise NotFoundException("用户", user_id)
        except Exception as e:
            logger.error(f"更新用户失败: user_id={user_id}, error={str(e)}")
            raise
    
    async def delete_user(self, user_id: int) -> None:
        """
        删除用户
        
        Args:
            user_id: 用户ID
            
        Raises:
            NotFoundException: 用户不存在
            ConflictException: 用户被使用，无法删除
        """
        logger.info(f"开始删除用户: user_id={user_id}")
        try:
            user = await User.get_or_none(user_id=user_id)
            if not user:
                raise NotFoundException("用户", user_id)
            
            # 检查是否被使用
            if await self._check_user_usage(user_id):
                raise ConflictException(
                    "用户正在被使用，无法删除",
                    details={"user_id": user_id}
                )
            
            await user.delete()
            logger.info(f"用户删除完成: user_id={user_id}")
        except (NotFoundException, ConflictException):
            raise
        except DoesNotExist:
            raise NotFoundException("用户", user_id)
        except Exception as e:
            logger.error(f"删除用户失败: user_id={user_id}, error={str(e)}")
            raise
    
    # ==================== 用户组管理 ====================
    
    async def list_user_groups(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserGroupResponse]:
        """
        获取用户组列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            
        Returns:
            List[UserGroupResponse]: 用户组列表
        """
        logger.info(f"开始获取用户组列表: skip={skip}, limit={limit}")
        try:
            groups = await UserGroup.all().offset(skip).limit(limit)
            result = []
            for group in groups:
                group_dict = await self._build_user_group_response(group)
                result.append(UserGroupResponse(**group_dict))
            
            logger.info(f"用户组列表获取完成: count={len(result)}")
            return result
        except Exception as e:
            logger.error(f"获取用户组列表失败: {str(e)}")
            raise
    
    async def get_user_group(self, user_group_id: int) -> UserGroupResponse:
        """
        根据ID获取用户组
        
        Args:
            user_group_id: 用户组ID
            
        Returns:
            UserGroupResponse: 用户组信息
            
        Raises:
            NotFoundException: 用户组不存在
        """
        logger.info(f"开始获取用户组信息: user_group_id={user_group_id}")
        try:
            group = await UserGroup.get_or_none(user_group_id=user_group_id)
            if not group:
                raise NotFoundException("用户组", user_group_id)
            
            group_dict = await self._build_user_group_response(group)
            logger.info(f"用户组信息获取完成: user_group_id={user_group_id}")
            return UserGroupResponse(**group_dict)
        except NotFoundException:
            raise
        except DoesNotExist:
            raise NotFoundException("用户组", user_group_id)
        except Exception as e:
            logger.error(f"获取用户组信息失败: user_group_id={user_group_id}, error={str(e)}")
            raise
    
    async def create_user_group(self, data: UserGroupCreate) -> UserGroupResponse:
        """
        创建新用户组
        
        Args:
            data: 用户组创建数据
            
        Returns:
            UserGroupResponse: 创建的用户组信息
            
        Raises:
            ConflictException: 用户组名称已存在
        """
        logger.info(f"开始创建用户组: name={data.name}")
        try:
            # 检查名称是否已存在
            existing_group = await UserGroup.filter(name=data.name).first()
            if existing_group:
                raise ConflictException(f"用户组名称 {data.name} 已存在")
            
            # 准备权限JSON
            permission_json = None
            if data.permission:
                permission_json = await self._serialize_permissions(data.permission)
            
            group = await UserGroup.create(
                name=data.name,
                permission=permission_json
            )
            logger.info(f"用户组创建完成: user_group_id={group.user_group_id}, name={data.name}")
            
            # 构建响应数据
            group_dict = {
                "user_group_id": group.user_group_id,
                "name": group.name,
                "permission": data.permission or {}
            }
            return UserGroupResponse(**group_dict)
        except ConflictException:
            raise
        except IntegrityError as e:
            logger.error(f"创建用户组失败（完整性错误）: {str(e)}")
            raise ConflictException(f"创建用户组失败: {str(e)}")
        except Exception as e:
            logger.error(f"创建用户组失败: {str(e)}")
            raise
    
    async def update_user_group(
        self,
        user_group_id: int,
        data: UserGroupUpdate
    ) -> UserGroupResponse:
        """
        更新用户组
        
        Args:
            user_group_id: 用户组ID
            data: 用户组更新数据
            
        Returns:
            UserGroupResponse: 更新后的用户组信息
            
        Raises:
            NotFoundException: 用户组不存在
            ConflictException: 用户组名称冲突
            ValidationException: 验证失败
        """
        logger.info(f"开始更新用户组: user_group_id={user_group_id}")
        try:
            group = await UserGroup.get_or_none(user_group_id=user_group_id)
            if not group:
                raise NotFoundException("用户组", user_group_id)
            
            update_data = data.model_dump(exclude_unset=True, exclude={'permission'})
            
            if not update_data and data.permission is None:
                raise ValidationException("没有需要更新的字段")
            
            # 如果更新名称，检查是否重复
            if 'name' in update_data and update_data['name'] != group.name:
                existing_group = await UserGroup.filter(name=update_data['name']).first()
                if existing_group and existing_group.user_group_id != user_group_id:
                    raise ConflictException(f"用户组名称 {update_data['name']} 已存在")
            
            # 更新字段
            for key, value in update_data.items():
                setattr(group, key, value)
            
            # 更新权限
            if data.permission is not None:
                group.permission = await self._serialize_permissions(data.permission)
            
            await group.save()
            logger.info(f"用户组更新完成: user_group_id={user_group_id}")
            
            group_dict = await self._build_user_group_response(group)
            return UserGroupResponse(**group_dict)
        except (NotFoundException, ConflictException, ValidationException):
            raise
        except DoesNotExist:
            raise NotFoundException("用户组", user_group_id)
        except Exception as e:
            logger.error(f"更新用户组失败: user_group_id={user_group_id}, error={str(e)}")
            raise
    
    async def delete_user_group(self, user_group_id: int) -> None:
        """
        删除用户组
        
        Args:
            user_group_id: 用户组ID
            
        Raises:
            NotFoundException: 用户组不存在
            ConflictException: 用户组被使用，无法删除
        """
        logger.info(f"开始删除用户组: user_group_id={user_group_id}")
        try:
            group = await UserGroup.get_or_none(user_group_id=user_group_id)
            if not group:
                raise NotFoundException("用户组", user_group_id)
            
            # 检查是否有用户使用此用户组
            if await self._check_user_group_usage(user_group_id):
                users_count = await User.filter(user_group_id=user_group_id).count()
                raise ConflictException(
                    f"用户组ID {user_group_id} 正在被 {users_count} 个用户使用，无法删除",
                    details={"user_group_id": user_group_id, "users_count": users_count}
                )
            
            await group.delete()
            logger.info(f"用户组删除完成: user_group_id={user_group_id}")
        except (NotFoundException, ConflictException):
            raise
        except DoesNotExist:
            raise NotFoundException("用户组", user_group_id)
        except Exception as e:
            logger.error(f"删除用户组失败: user_group_id={user_group_id}, error={str(e)}")
            raise
    
    # ==================== 权限管理 ====================
    
    async def get_user_group_permissions(
        self,
        user_group_id: int
    ) -> List[PermissionListResponse]:
        """
        获取用户组权限列表
        
        Args:
            user_group_id: 用户组ID
            
        Returns:
            List[PermissionListResponse]: 权限列表
            
        Raises:
            NotFoundException: 用户组不存在
        """
        logger.info(f"开始获取用户组权限: user_group_id={user_group_id}")
        try:
            group = await UserGroup.get_or_none(user_group_id=user_group_id)
            if not group:
                raise NotFoundException("用户组", user_group_id)
            
            permissions = await self._parse_permissions(group.permission)
            
            result = [
                PermissionListResponse(resource=resource, actions=actions)
                for resource, actions in permissions.items()
            ]
            logger.info(f"用户组权限获取完成: user_group_id={user_group_id}")
            return result
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取用户组权限失败: user_group_id={user_group_id}, error={str(e)}")
            raise
    
    async def update_user_group_permissions(
        self,
        user_group_id: int,
        permissions: List[PermissionUpdate]
    ) -> UserGroupResponse:
        """
        更新用户组权限
        
        Args:
            user_group_id: 用户组ID
            permissions: 权限列表
            
        Returns:
            UserGroupResponse: 更新后的用户组信息
            
        Raises:
            NotFoundException: 用户组不存在
        """
        logger.info(f"开始更新用户组权限: user_group_id={user_group_id}")
        try:
            group = await UserGroup.get_or_none(user_group_id=user_group_id)
            if not group:
                raise NotFoundException("用户组", user_group_id)
            
            # 构建权限字典
            permission_dict = {}
            for perm in permissions:
                permission_dict[perm.resource] = perm.actions
            
            # 更新权限
            group.permission = await self._serialize_permissions(permission_dict)
            await group.save()
            
            logger.info(f"用户组权限更新完成: user_group_id={user_group_id}")
            
            group_dict = await self._build_user_group_response(group)
            group_dict['permission'] = permission_dict
            return UserGroupResponse(**group_dict)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"更新用户组权限失败: user_group_id={user_group_id}, error={str(e)}")
            raise
    
    async def add_user_group_permission(
        self,
        user_group_id: int,
        permission: PermissionUpdate
    ) -> UserGroupResponse:
        """
        添加用户组权限（合并到现有权限）
        
        Args:
            user_group_id: 用户组ID
            permission: 要添加的权限
            
        Returns:
            UserGroupResponse: 更新后的用户组信息
            
        Raises:
            NotFoundException: 用户组不存在
        """
        logger.info(f"开始添加用户组权限: user_group_id={user_group_id}, resource={permission.resource}")
        try:
            group = await UserGroup.get_or_none(user_group_id=user_group_id)
            if not group:
                raise NotFoundException("用户组", user_group_id)
            
            # 获取现有权限
            permissions = await self._parse_permissions(group.permission)
            
            # 合并新权限（去重）
            if permission.resource in permissions:
                existing_actions = set(permissions[permission.resource])
                new_actions = set(permission.actions)
                permissions[permission.resource] = list(existing_actions | new_actions)
            else:
                permissions[permission.resource] = permission.actions
            
            # 更新权限
            group.permission = await self._serialize_permissions(permissions)
            await group.save()
            
            logger.info(f"用户组权限添加完成: user_group_id={user_group_id}")
            
            group_dict = await self._build_user_group_response(group)
            group_dict['permission'] = permissions
            return UserGroupResponse(**group_dict)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"添加用户组权限失败: user_group_id={user_group_id}, error={str(e)}")
            raise
    
    async def delete_user_group_permission(
        self,
        user_group_id: int,
        resource: str
    ) -> UserGroupResponse:
        """
        删除用户组权限（删除整个资源权限）
        
        Args:
            user_group_id: 用户组ID
            resource: 资源名称
            
        Returns:
            UserGroupResponse: 更新后的用户组信息
            
        Raises:
            NotFoundException: 用户组不存在
        """
        logger.info(f"开始删除用户组权限: user_group_id={user_group_id}, resource={resource}")
        try:
            group = await UserGroup.get_or_none(user_group_id=user_group_id)
            if not group:
                raise NotFoundException("用户组", user_group_id)
            
            # 获取现有权限
            permissions = await self._parse_permissions(group.permission)
            
            # 删除资源权限
            if resource in permissions:
                del permissions[resource]
            
            # 更新权限
            group.permission = await self._serialize_permissions(permissions) if permissions else None
            await group.save()
            
            logger.info(f"用户组权限删除完成: user_group_id={user_group_id}, resource={resource}")
            
            group_dict = await self._build_user_group_response(group)
            group_dict['permission'] = permissions
            return UserGroupResponse(**group_dict)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"删除用户组权限失败: user_group_id={user_group_id}, error={str(e)}")
            raise
    
    async def get_user_permissions(self, user_id: int) -> List[str]:
        """
        获取用户权限列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[str]: 权限列表（格式：resource:action）
            
        Raises:
            NotFoundException: 用户不存在
        """
        logger.info(f"开始获取用户权限: user_id={user_id}")
        try:
            user = await User.get_or_none(user_id=user_id)
            if not user:
                raise NotFoundException("用户", user_id)
            
            # 获取用户组权限
            user_group = await UserGroup.get_or_none(user_group_id=user.user_group_id)
            if not user_group:
                return []
            
            permissions = await self._parse_permissions(user_group.permission)
            
            # 转换为权限字符串列表
            result = []
            for resource, actions in permissions.items():
                for action in actions:
                    result.append(f"{resource}:{action}")
            
            logger.info(f"用户权限获取完成: user_id={user_id}, count={len(result)}")
            return result
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取用户权限失败: user_id={user_id}, error={str(e)}")
            raise
    
    # ==================== 用户活动日志 ====================
    
    async def get_user_activities(
        self,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserActivityResponse]:
        """
        获取用户活动日志
        
        Args:
            user_id: 用户ID（可选，如果提供则只返回该用户的活动）
            skip: 跳过的记录数
            limit: 返回的记录数
            
        Returns:
            List[UserActivityResponse]: 活动日志列表
        """
        logger.info(f"开始获取用户活动日志: user_id={user_id}, skip={skip}, limit={limit}")
        try:
            query = UserLogin.all()
            
            if user_id is not None:
                query = query.filter(user_id=user_id)
            
            # 按时间倒序排列
            activities = await query.order_by('-date_added').offset(skip).limit(limit)
            result = [UserActivityResponse.model_validate(activity) for activity in activities]
            
            logger.info(f"用户活动日志获取完成: count={len(result)}")
            return result
        except Exception as e:
            logger.error(f"获取用户活动日志失败: {str(e)}")
            raise
    
    # ==================== 私有方法 ====================
    
    async def _validate_username_uniqueness(
        self,
        username: str,
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        验证用户名唯一性
        
        Args:
            username: 用户名
            exclude_id: 排除的用户ID（用于更新时检查）
            
        Returns:
            bool: 如果用户名唯一返回True，否则返回False
        """
        try:
            query = User.filter(username=username)
            if exclude_id:
                query = query.filter(user_id__ne=exclude_id)
            
            existing = await query.first()
            return existing is None
        except Exception as e:
            logger.warning(f"验证用户名唯一性失败: username={username}, error={str(e)}")
            return False
    
    async def _validate_email(self, email: str) -> bool:
        """
        验证邮箱格式
        
        Args:
            email: 邮箱字符串
            
        Returns:
            bool: 如果邮箱格式正确返回True，否则返回False
        """
        if not email:
            return False
        
        # 使用正则表达式验证邮箱格式
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    async def _parse_permissions(self, permission_str: Optional[str]) -> Dict[str, List[str]]:
        """
        解析权限JSON字符串为字典
        
        Args:
            permission_str: 权限JSON字符串
            
        Returns:
            Dict[str, List[str]]: 权限字典
        """
        if not permission_str:
            return {}
        
        try:
            return json.loads(permission_str)
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"解析权限JSON失败: {permission_str}")
            return {}
    
    async def _serialize_permissions(self, permissions: Dict[str, List[str]]) -> Optional[str]:
        """
        序列化权限字典为JSON字符串
        
        Args:
            permissions: 权限字典
            
        Returns:
            Optional[str]: JSON字符串，如果为空字典则返回None
        """
        if not permissions:
            return None
        
        try:
            return json.dumps(permissions, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            logger.error(f"序列化权限失败: {str(e)}")
            raise ValidationException(f"权限格式无效: {str(e)}")
    
    async def _build_user_group_response(self, group: UserGroup) -> Dict[str, Any]:
        """
        构建用户组响应对象
        
        Args:
            group: UserGroup模型实例
            
        Returns:
            Dict[str, Any]: 用户组响应字典
        """
        group_dict = {
            "user_group_id": group.user_group_id,
            "name": group.name,
            "permission": await self._parse_permissions(group.permission)
        }
        return group_dict
    
    async def _check_user_usage(self, user_id: int) -> bool:
        """
        检查用户是否被使用
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 如果被使用返回True，否则返回False
        """
        try:
            # 检查订单表（如果存在）
            try:
                from app.models.order.order import Order
                count = await Order.filter(customer_id=user_id).count()
                if count > 0:
                    logger.info(f"用户被订单使用: user_id={user_id}, count={count}")
                    return True
            except (ImportError, AttributeError):
                logger.debug("订单表不存在，跳过订单检查")
            
            # 可以继续检查其他使用用户的表
            # 例如：评论、评价等
            
            return False
        except Exception as e:
            logger.warning(f"检查用户使用情况失败: user_id={user_id}, error={str(e)}")
            # 如果检查失败，为了安全起见，返回True（不允许删除）
            return True
    
    async def _check_user_group_usage(self, user_group_id: int) -> bool:
        """
        检查用户组是否被使用
        
        Args:
            user_group_id: 用户组ID
            
        Returns:
            bool: 如果被使用返回True，否则返回False
        """
        try:
            count = await User.filter(user_group_id=user_group_id).count()
            return count > 0
        except Exception as e:
            logger.warning(f"检查用户组使用情况失败: user_group_id={user_group_id}, error={str(e)}")
            # 如果检查失败，为了安全起见，返回True（不允许删除）
            return True

