"""
Setting service - 系统设置服务层
"""
import json
import logging
from typing import List, Optional
from tortoise.exceptions import DoesNotExist, IntegrityError

try:
    from app.models.system.setting import Setting
except (ImportError, AttributeError):
    import importlib
    setting_module = importlib.import_module('app.models.system.setting')
    Setting = setting_module.Setting

from app.schemas.setting import SettingCreate, SettingUpdate, SettingResponse
from app.services.base_service import BaseService
from app.exceptions import NotFoundException, ConflictException, ValidationException

logger = logging.getLogger(__name__)


class SettingService(BaseService):
    """系统设置服务"""
    
    async def list_settings(
        self,
        skip: int = 0,
        limit: int = 100,
        store_id: Optional[int] = None,
        code: Optional[str] = None,
        key: Optional[str] = None
    ) -> List[SettingResponse]:
        """
        获取配置列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            store_id: 店铺ID筛选（可选）
            code: 配置代码筛选（可选）
            key: 配置键名筛选（可选）
            
        Returns:
            List[SettingResponse]: 配置列表
        """
        logger.info(f"开始获取配置列表: skip={skip}, limit={limit}")
        try:
            query = Setting.all()
            
            if store_id is not None:
                query = query.filter(store_id=store_id)
            if code:
                query = query.filter(code=code)
            if key:
                query = query.filter(key=key)
            
            settings = await query.offset(skip).limit(limit)
            result = []
            for setting in settings:
                response = await self._build_setting_response(setting)
                result.append(response)
            
            logger.info(f"配置列表获取完成: count={len(result)}")
            return result
        except Exception as e:
            logger.error(f"获取配置列表失败: {str(e)}")
            raise
    
    async def get_setting(self, setting_id: int) -> SettingResponse:
        """
        根据ID获取配置
        
        Args:
            setting_id: 配置ID
            
        Returns:
            SettingResponse: 配置信息
            
        Raises:
            NotFoundException: 配置不存在
        """
        logger.info(f"开始获取配置信息: setting_id={setting_id}")
        try:
            setting = await Setting.get_or_none(setting_id=setting_id)
            if not setting:
                raise NotFoundException("配置", setting_id)
            
            response = await self._build_setting_response(setting)
            logger.info(f"配置信息获取完成: setting_id={setting_id}")
            return response
        except NotFoundException:
            raise
        except DoesNotExist:
            raise NotFoundException("配置", setting_id)
        except Exception as e:
            logger.error(f"获取配置信息失败: setting_id={setting_id}, error={str(e)}")
            raise
    
    async def get_setting_by_key(
        self,
        code: str,
        key: str,
        store_id: int = 0
    ) -> SettingResponse:
        """
        根据code和key获取配置
        
        Args:
            code: 配置代码
            key: 配置键名
            store_id: 店铺ID（默认0）
            
        Returns:
            SettingResponse: 配置信息
            
        Raises:
            NotFoundException: 配置不存在
        """
        logger.info(f"开始获取配置: code={code}, key={key}, store_id={store_id}")
        try:
            setting = await Setting.filter(
                code=code,
                key=key,
                store_id=store_id
            ).first()
            
            if not setting:
                raise NotFoundException("配置", 0)
            
            response = await self._build_setting_response(setting)
            logger.info(f"配置获取完成: code={code}, key={key}")
            return response
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取配置失败: code={code}, key={key}, error={str(e)}")
            raise
    
    async def create_setting(self, data: SettingCreate) -> SettingResponse:
        """
        创建新配置
        
        Args:
            data: 配置创建数据
            
        Returns:
            SettingResponse: 创建的配置信息
            
        Raises:
            ConflictException: 配置已存在
            ValidationException: 验证失败
        """
        logger.info(f"开始创建配置: code={data.code}, key={data.key}")
        try:
            # 检查配置是否已存在
            existing_setting = await Setting.filter(
                code=data.code,
                key=data.key,
                store_id=data.store_id
            ).first()
            
            if existing_setting:
                raise ConflictException(
                    f"配置已存在: code={data.code}, key={data.key}, store_id={data.store_id}"
                )
            
            # 如果serialized=1，验证value是否为有效JSON
            if data.serialized == 1:
                if not await self._validate_json_value(data.value):
                    raise ValidationException(
                        "当serialized=1时，value必须是有效的JSON格式"
                    )
            
            setting = await Setting.create(**data.model_dump())
            logger.info(f"配置创建完成: setting_id={setting.setting_id}")
            
            response = await self._build_setting_response(setting)
            return response
        except (ConflictException, ValidationException):
            raise
        except IntegrityError as e:
            logger.error(f"创建配置失败（完整性错误）: {str(e)}")
            raise ConflictException(f"创建配置失败: {str(e)}")
        except Exception as e:
            logger.error(f"创建配置失败: {str(e)}")
            raise
    
    async def update_setting(
        self,
        setting_id: int,
        data: SettingUpdate
    ) -> SettingResponse:
        """
        更新配置
        
        Args:
            setting_id: 配置ID
            data: 配置更新数据
            
        Returns:
            SettingResponse: 更新后的配置信息
            
        Raises:
            NotFoundException: 配置不存在
            ConflictException: 配置冲突
            ValidationException: 验证失败
        """
        logger.info(f"开始更新配置: setting_id={setting_id}")
        try:
            setting = await Setting.get_or_none(setting_id=setting_id)
            if not setting:
                raise NotFoundException("配置", setting_id)
            
            update_data = data.model_dump(exclude_unset=True)
            
            if not update_data:
                raise ValidationException("没有需要更新的字段")
            
            # 如果更新code/key/store_id，检查是否与其他配置冲突
            new_code = update_data.get('code', setting.code)
            new_key = update_data.get('key', setting.key)
            new_store_id = update_data.get('store_id', setting.store_id)
            
            if new_code != setting.code or new_key != setting.key or new_store_id != setting.store_id:
                existing_setting = await Setting.filter(
                    code=new_code,
                    key=new_key,
                    store_id=new_store_id
                ).first()
                
                if existing_setting and existing_setting.setting_id != setting_id:
                    raise ConflictException(
                        f"配置已存在: code={new_code}, key={new_key}, store_id={new_store_id}"
                    )
            
            # 如果更新value且serialized=1，验证JSON格式
            if 'value' in update_data:
                serialized = update_data.get('serialized', setting.serialized)
                if serialized == 1:
                    if not await self._validate_json_value(update_data['value']):
                        raise ValidationException(
                            "当serialized=1时，value必须是有效的JSON格式"
                        )
            
            # 更新字段
            for key, value in update_data.items():
                setattr(setting, key, value)
            
            await setting.save()
            logger.info(f"配置更新完成: setting_id={setting_id}")
            
            response = await self._build_setting_response(setting)
            return response
        except (NotFoundException, ConflictException, ValidationException):
            raise
        except DoesNotExist:
            raise NotFoundException("配置", setting_id)
        except Exception as e:
            logger.error(f"更新配置失败: setting_id={setting_id}, error={str(e)}")
            raise
    
    async def update_setting_by_key(
        self,
        code: str,
        key: str,
        store_id: int,
        data: SettingUpdate
    ) -> SettingResponse:
        """
        根据code和key更新配置
        
        Args:
            code: 配置代码
            key: 配置键名
            store_id: 店铺ID
            data: 配置更新数据
            
        Returns:
            SettingResponse: 更新后的配置信息
            
        Raises:
            NotFoundException: 配置不存在
            ValidationException: 验证失败
        """
        logger.info(f"开始更新配置: code={code}, key={key}, store_id={store_id}")
        try:
            setting = await Setting.filter(
                code=code,
                key=key,
                store_id=store_id
            ).first()
            
            if not setting:
                raise NotFoundException("配置", 0)
            
            update_data = data.model_dump(exclude_unset=True)
            
            if not update_data:
                raise ValidationException("没有需要更新的字段")
            
            # 如果更新value且serialized=1，验证JSON格式
            if 'value' in update_data:
                serialized = update_data.get('serialized', setting.serialized)
                if serialized == 1:
                    if not await self._validate_json_value(update_data['value']):
                        raise ValidationException(
                            "当serialized=1时，value必须是有效的JSON格式"
                        )
            
            # 更新字段
            for key, value in update_data.items():
                setattr(setting, key, value)
            
            await setting.save()
            logger.info(f"配置更新完成: code={code}, key={key}")
            
            response = await self._build_setting_response(setting)
            return response
        except (NotFoundException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"更新配置失败: code={code}, key={key}, error={str(e)}")
            raise
    
    async def delete_setting(self, setting_id: int) -> None:
        """
        删除配置
        
        Args:
            setting_id: 配置ID
            
        Raises:
            NotFoundException: 配置不存在
        """
        logger.info(f"开始删除配置: setting_id={setting_id}")
        try:
            setting = await Setting.get_or_none(setting_id=setting_id)
            if not setting:
                raise NotFoundException("配置", setting_id)
            
            await setting.delete()
            logger.info(f"配置删除完成: setting_id={setting_id}")
        except NotFoundException:
            raise
        except DoesNotExist:
            raise NotFoundException("配置", setting_id)
        except Exception as e:
            logger.error(f"删除配置失败: setting_id={setting_id}, error={str(e)}")
            raise
    
    async def get_timezone(self, store_id: int = 0) -> SettingResponse:
        """
        获取时区设置
        
        Args:
            store_id: 店铺ID（默认0）
            
        Returns:
            SettingResponse: 时区配置信息
            
        Raises:
            NotFoundException: 时区设置不存在
        """
        logger.info(f"开始获取时区设置: store_id={store_id}")
        try:
            # 使用 filter().first() 避免多条记录时抛出异常
            setting = await Setting.filter(
                code='config',
                key='config_timezone',
                store_id=store_id
            ).first()
            
            if not setting:
                # 使用自定义消息，因为时区设置可能不存在（使用默认值）
                raise NotFoundException("时区设置", 0)
            
            response = await self._build_setting_response(setting)
            logger.info(f"时区设置获取完成: timezone={setting.value}")
            return response
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取时区设置失败: store_id={store_id}, error={str(e)}")
            raise
    
    async def update_timezone(
        self,
        timezone: str,
        store_id: int = 0
    ) -> SettingResponse:
        """
        更新时区设置
        
        Args:
            timezone: 时区字符串（如 'Asia/Shanghai', 'UTC'）
            store_id: 店铺ID（默认0）
            
        Returns:
            SettingResponse: 更新后的时区配置信息
            
        Raises:
            ValidationException: 时区格式无效
        """
        logger.info(f"开始更新时区设置: timezone={timezone}, store_id={store_id}")
        try:
            # 验证时区格式
            if not await self._validate_timezone(timezone):
                raise ValidationException(f"无效的时区格式: {timezone}")
            
            # 查找或创建时区配置
            # 使用 filter().all() 处理可能的多条记录
            settings = await Setting.filter(
                code='config',
                key='config_timezone',
                store_id=store_id
            ).all()
            
            if settings:
                # 如果有多条记录，更新所有记录（虽然理论上应该只有一条）
                for s in settings:
                    s.value = timezone
                    await s.save()
                logger.info(f"时区设置更新完成: timezone={timezone}, 更新了 {len(settings)} 条记录")
                # 重新查询数据库获取最新值
                setting = await Setting.filter(
                    code='config',
                    key='config_timezone',
                    store_id=store_id
                ).first()
            else:
                # 创建新配置
                setting = await Setting.create(
                    code='config',
                    key='config_timezone',
                    value=timezone,
                    store_id=store_id,
                    serialized=0
                )
                logger.info(f"时区设置创建完成: timezone={timezone}")
            
            if not setting:
                raise ValidationException("时区设置操作失败")
            
            response = await self._build_setting_response(setting)
            return response
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"更新时区设置失败: timezone={timezone}, error={str(e)}")
            raise
    
    async def list_timezones(self) -> List[str]:
        """
        获取常用时区列表
        
        Returns:
            List[str]: 常用时区列表
        """
        logger.info("开始获取时区列表")
        try:
            # 常用时区列表
            common_timezones = [
                "UTC",
                "Asia/Shanghai",
                "Asia/Tokyo",
                "Asia/Hong_Kong",
                "Asia/Singapore",
                "Asia/Dubai",
                "Europe/London",
                "Europe/Paris",
                "Europe/Berlin",
                "Europe/Moscow",
                "America/New_York",
                "America/Chicago",
                "America/Denver",
                "America/Los_Angeles",
                "America/Toronto",
                "America/Mexico_City",
                "America/Sao_Paulo",
                "Australia/Sydney",
                "Australia/Melbourne",
            ]
            
            logger.info(f"时区列表获取完成: count={len(common_timezones)}")
            return common_timezones
        except Exception as e:
            logger.error(f"获取时区列表失败: {str(e)}")
            raise
    
    # ==================== 私有方法 ====================
    
    async def _build_setting_response(self, setting: Setting) -> SettingResponse:
        """
        构建配置响应对象
        
        Args:
            setting: Setting模型实例
            
        Returns:
            SettingResponse: 配置响应对象
        """
        setting_dict = SettingResponse.model_validate(setting).model_dump()
        
        # 处理序列化的值
        if setting.serialized == 1 and setting.value:
            try:
                setting_dict['parsed_value'] = json.loads(setting.value)
            except json.JSONDecodeError:
                setting_dict['parsed_value'] = None
        
        return SettingResponse(**setting_dict)
    
    async def _validate_json_value(self, value: str) -> bool:
        """
        验证JSON值
        
        Args:
            value: 要验证的值
            
        Returns:
            bool: 如果是有效的JSON返回True，否则返回False
        """
        if not value:
            return False
        
        try:
            json.loads(value)
            return True
        except json.JSONDecodeError:
            return False
    
    async def _validate_timezone(self, timezone: str) -> bool:
        """
        验证时区格式
        
        Args:
            timezone: 时区字符串
            
        Returns:
            bool: 如果是有效的时区返回True，否则返回False
        """
        if not timezone:
            return False
        
        try:
            # 尝试使用 zoneinfo (Python 3.9+)
            try:
                from zoneinfo import ZoneInfo
                ZoneInfo(timezone)
                return True
            except ImportError:
                # Python < 3.9 使用 pytz
                try:
                    import pytz
                    pytz.timezone(timezone)
                    return True
                except ImportError:
                    logger.warning("未安装 zoneinfo 或 pytz，跳过时区格式验证")
                    # 如果没有安装时区库，只验证基本格式
                    return bool(timezone.strip())
                except Exception:
                    return False
        except Exception:
            return False

