"""
服务层基类
"""
import logging
from typing import Optional
from app.models.localisation.language import Language

logger = logging.getLogger(__name__)


class BaseService:
    """服务层基类
    
    提供所有服务类的通用功能，如：
    - 语言代码获取
    - 通用数据转换
    - 通用验证方法
    """
    
    async def get_language_code(self, language_id: int) -> Optional[str]:
        """
        获取语言代码
        
        Args:
            language_id: 语言ID
            
        Returns:
            Optional[str]: 语言代码，如果语言不存在则返回None
        """
        try:
            language = await Language.get_or_none(language_id=language_id)
            return language.code if language else None
        except Exception as e:
            logger.warning(f"获取语言代码失败: language_id={language_id}, error={str(e)}")
            return None
    
    async def validate_language_exists(self, language_id: int) -> bool:
        """
        验证语言是否存在
        
        Args:
            language_id: 语言ID
            
        Returns:
            bool: 如果语言存在返回True，否则返回False
        """
        try:
            language = await Language.get_or_none(language_id=language_id)
            return language is not None
        except Exception:
            return False
    
    async def get_language_codes(self, language_ids: list[int]) -> dict[int, Optional[str]]:
        """
        批量获取语言代码
        
        Args:
            language_ids: 语言ID列表
            
        Returns:
            dict[int, Optional[str]]: 语言ID到语言代码的映射
        """
        result = {}
        try:
            languages = await Language.filter(language_id__in=language_ids).all()
            language_map = {lang.language_id: lang.code for lang in languages}
            
            for lang_id in language_ids:
                result[lang_id] = language_map.get(lang_id)
        except Exception as e:
            logger.warning(f"批量获取语言代码失败: error={str(e)}")
            for lang_id in language_ids:
                result[lang_id] = None
        
        return result

