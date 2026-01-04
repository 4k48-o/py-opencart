"""
Language service - 语言服务层
"""
import logging
from typing import List, Optional
from tortoise.exceptions import DoesNotExist, IntegrityError

try:
    from app.models.localisation.language import Language
except (ImportError, AttributeError):
    import importlib
    language_module = importlib.import_module('app.models.localisation.language')
    Language = language_module.Language

from app.schemas.language import LanguageCreate, LanguageUpdate, LanguageResponse
from app.services.base_service import BaseService
from app.exceptions import NotFoundException, ConflictException, ValidationException

logger = logging.getLogger(__name__)


class LanguageService(BaseService):
    """语言服务"""
    
    async def list_languages(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[int] = None
    ) -> List[LanguageResponse]:
        """
        获取语言列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            status: 状态筛选（可选，0=禁用，1=启用）
            
        Returns:
            List[LanguageResponse]: 语言列表
        """
        logger.info(f"开始获取语言列表: skip={skip}, limit={limit}")
        try:
            query = Language.all()
            
            if status is not None:
                query = query.filter(status=status)
            
            # 按sort_order和name排序
            languages = await query.order_by('sort_order', 'name').offset(skip).limit(limit)
            result = [LanguageResponse.model_validate(lang) for lang in languages]
            
            logger.info(f"语言列表获取完成: count={len(result)}")
            return result
        except Exception as e:
            logger.error(f"获取语言列表失败: {str(e)}")
            raise
    
    async def get_language(self, language_id: int) -> LanguageResponse:
        """
        根据ID获取语言
        
        Args:
            language_id: 语言ID
            
        Returns:
            LanguageResponse: 语言信息
            
        Raises:
            NotFoundException: 语言不存在
        """
        logger.info(f"开始获取语言信息: language_id={language_id}")
        try:
            language = await Language.get_or_none(language_id=language_id)
            if not language:
                raise NotFoundException("语言", language_id)
            
            logger.info(f"语言信息获取完成: language_id={language_id}")
            return LanguageResponse.model_validate(language)
        except NotFoundException:
            raise
        except DoesNotExist:
            raise NotFoundException("语言", language_id)
        except Exception as e:
            logger.error(f"获取语言信息失败: language_id={language_id}, error={str(e)}")
            raise
    
    async def get_language_by_code(self, code: str) -> LanguageResponse:
        """
        根据代码获取语言
        
        Args:
            code: 语言代码（如 'en', 'zh-CN'）
            
        Returns:
            LanguageResponse: 语言信息
            
        Raises:
            NotFoundException: 语言不存在
            ValidationException: 代码格式无效
        """
        logger.info(f"开始获取语言: code={code}")
        try:
            # ✅ 添加参数验证：在查询数据库之前验证code格式
            if not code or len(code.strip()) < 2 or len(code.strip()) > 5:
                raise ValidationException(
                    "语言代码长度必须在2-5个字符之间",
                    details={"code": code, "length": len(code.strip()) if code else 0}
                )
            
            # 验证code格式：只能包含字母、数字、连字符和下划线
            import re
            code_trimmed = code.strip()
            if not re.match(r'^[a-zA-Z0-9_-]+$', code_trimmed):
                raise ValidationException(
                    "语言代码只能包含字母、数字、连字符和下划线",
                    details={"code": code}
                )
            
            # 使用 filter().first() 代替 get_or_none()，避免 Multiple objects returned 错误
            language = await Language.filter(code=code_trimmed).first()
            if not language:
                raise NotFoundException("语言", code_trimmed)
            
            logger.info(f"语言获取完成: language_id={language.language_id}")
            return LanguageResponse.model_validate(language)
        except NotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"获取语言失败: code={code}, error={str(e)}")
            raise
    
    async def create_language(self, data: LanguageCreate) -> LanguageResponse:
        """
        创建新语言
        
        Args:
            data: 语言创建数据
            
        Returns:
            LanguageResponse: 创建的语言信息
            
        Raises:
            ConflictException: 语言代码已存在
        """
        logger.info(f"开始创建语言: name={data.name}, code={data.code}")
        try:
            # 检查语言代码是否已存在
            if not await self._validate_code_uniqueness(data.code):
                raise ConflictException(f"语言代码 {data.code} 已存在")
            
            language = await Language.create(**data.model_dump())
            logger.info(f"语言创建完成: language_id={language.language_id}, code={data.code}")
            return LanguageResponse.model_validate(language)
        except ConflictException:
            raise
        except IntegrityError as e:
            logger.error(f"创建语言失败（完整性错误）: {str(e)}")
            raise ConflictException(f"创建语言失败: {str(e)}")
        except Exception as e:
            logger.error(f"创建语言失败: {str(e)}")
            raise
    
    async def update_language(
        self,
        language_id: int,
        data: LanguageUpdate
    ) -> LanguageResponse:
        """
        更新语言
        
        Args:
            language_id: 语言ID
            data: 语言更新数据
            
        Returns:
            LanguageResponse: 更新后的语言信息
            
        Raises:
            NotFoundException: 语言不存在
            ConflictException: 语言代码冲突
            ValidationException: 验证失败
        """
        logger.info(f"开始更新语言: language_id={language_id}")
        try:
            language = await Language.get_or_none(language_id=language_id)
            if not language:
                raise NotFoundException("语言", language_id)
            
            update_data = data.model_dump(exclude_unset=True)
            
            if not update_data:
                raise ValidationException("没有需要更新的字段")
            
            # 如果更新code，检查是否重复
            if 'code' in update_data and update_data['code'] != language.code:
                if not await self._validate_code_uniqueness(update_data['code'], exclude_id=language_id):
                    raise ConflictException(f"语言代码 {update_data['code']} 已存在")
            
            # 更新字段
            for key, value in update_data.items():
                setattr(language, key, value)
            
            await language.save()
            logger.info(f"语言更新完成: language_id={language_id}")
            return LanguageResponse.model_validate(language)
        except (NotFoundException, ConflictException, ValidationException):
            raise
        except DoesNotExist:
            raise NotFoundException("语言", language_id)
        except Exception as e:
            logger.error(f"更新语言失败: language_id={language_id}, error={str(e)}")
            raise
    
    async def delete_language(self, language_id: int) -> None:
        """
        删除语言
        
        Args:
            language_id: 语言ID
            
        Raises:
            NotFoundException: 语言不存在
            ConflictException: 语言被使用，无法删除
        """
        logger.info(f"开始删除语言: language_id={language_id}")
        try:
            language = await Language.get_or_none(language_id=language_id)
            if not language:
                raise NotFoundException("语言", language_id)
            
            # 检查是否被使用
            if await self._check_language_usage(language_id):
                raise ConflictException(
                    "语言正在被使用，无法删除",
                    details={"language_id": language_id}
                )
            
            await language.delete()
            logger.info(f"语言删除完成: language_id={language_id}")
        except (NotFoundException, ConflictException):
            raise
        except DoesNotExist:
            raise NotFoundException("语言", language_id)
        except Exception as e:
            logger.error(f"删除语言失败: language_id={language_id}, error={str(e)}")
            raise
    
    # ==================== 私有方法 ====================
    
    async def _validate_code_uniqueness(
        self,
        code: str,
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        验证语言代码唯一性
        
        Args:
            code: 语言代码
            exclude_id: 排除的语言ID（用于更新时检查）
            
        Returns:
            bool: 如果代码唯一返回True，否则返回False
        """
        try:
            query = Language.filter(code=code)
            if exclude_id:
                query = query.filter(language_id__ne=exclude_id)
            
            existing = await query.first()
            return existing is None
        except Exception as e:
            logger.warning(f"验证语言代码唯一性失败: code={code}, error={str(e)}")
            return False
    
    async def _check_language_usage(self, language_id: int) -> bool:
        """
        检查语言是否被使用
        
        Args:
            language_id: 语言ID
            
        Returns:
            bool: 如果被使用返回True，否则返回False
        """
        try:
            # 检查是否有描述表使用该语言
            # 这里检查几个主要的描述表
            
            # 检查分类描述
            from app.models.catalog.category_description import CategoryDescription
            count = await CategoryDescription.filter(language_id=language_id).count()
            if count > 0:
                logger.info(f"语言被分类描述使用: language_id={language_id}, count={count}")
                return True
            
            # 检查商品描述
            from app.models.catalog.product_description import ProductDescription
            count = await ProductDescription.filter(language_id=language_id).count()
            if count > 0:
                logger.info(f"语言被商品描述使用: language_id={language_id}, count={count}")
                return True
            
            # 检查属性描述
            from app.models.catalog.attribute_description import AttributeDescription
            count = await AttributeDescription.filter(language_id=language_id).count()
            if count > 0:
                logger.info(f"语言被属性描述使用: language_id={language_id}, count={count}")
                return True
            
            # 检查属性组描述
            from app.models.catalog.attribute_group_description import AttributeGroupDescription
            count = await AttributeGroupDescription.filter(language_id=language_id).count()
            if count > 0:
                logger.info(f"语言被属性组描述使用: language_id={language_id}, count={count}")
                return True
            
            # 检查选项描述
            from app.models.catalog.option_description import OptionDescription
            count = await OptionDescription.filter(language_id=language_id).count()
            if count > 0:
                logger.info(f"语言被选项描述使用: language_id={language_id}, count={count}")
                return True
            
            # 检查选项值描述
            from app.models.catalog.option_value_description import OptionValueDescription
            count = await OptionValueDescription.filter(language_id=language_id).count()
            if count > 0:
                logger.info(f"语言被选项值描述使用: language_id={language_id}, count={count}")
                return True
            
            # 可以继续检查其他使用语言的表
            # 例如：订单、翻译表等
            
            return False
        except Exception as e:
            logger.warning(f"检查语言使用情况失败: language_id={language_id}, error={str(e)}")
            # 如果检查失败，为了安全起见，返回True（不允许删除）
            return True

