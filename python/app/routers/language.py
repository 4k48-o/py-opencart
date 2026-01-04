"""
Language API router
"""
import logging
from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List, Optional

try:
    from app.models.system.user import User
except (ImportError, AttributeError):
    import importlib
    user_module = importlib.import_module('app.models.system.user')
    User = user_module.User

from app.schemas.language import LanguageCreate, LanguageUpdate, LanguageResponse
from app.services.language_service import LanguageService
from app.exceptions import NotFoundException, ConflictException, ValidationException
from app.api.deps import get_current_user, require_permission, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/languages", tags=["languages"])


@router.get("/", response_model=List[LanguageResponse], summary="获取语言列表")
async def list_languages(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    status: Optional[int] = Query(None, ge=0, le=1, description="状态筛选（0=禁用，1=启用）"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("language:read")),
    service: LanguageService = Depends(get_service(LanguageService)),
):
    """
    获取语言列表
    
    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的记录数（最大1000）
    - **status**: 状态筛选（可选，0=禁用，1=启用）
    """
    logger.info(f"开始获取语言列表: skip={skip}, limit={limit}, user_id={current_user.user_id}")
    try:
        return await service.list_languages(skip=skip, limit=limit, status=status)
    except Exception as e:
        logger.error(f"获取语言列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取语言列表失败: {str(e)}"
        )


@router.get("/{language_id}", response_model=LanguageResponse, summary="根据ID获取语言")
async def get_language(
    language_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("language:read")),
    service: LanguageService = Depends(get_service(LanguageService)),
):
    """
    根据ID获取语言信息
    
    - **language_id**: 语言ID
    """
    logger.info(f"开始获取语言信息: language_id={language_id}, user_id={current_user.user_id}")
    try:
        return await service.get_language(language_id=language_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"语言ID {language_id} 不存在"
        )
    except Exception as e:
        logger.error(f"获取语言信息失败: language_id={language_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取语言信息失败: {str(e)}"
        )


@router.get("/by-code/{code}", response_model=LanguageResponse, summary="根据代码获取语言")
async def get_language_by_code(
    code: str,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("language:read")),
    service: LanguageService = Depends(get_service(LanguageService)),
):
    """
    根据语言代码获取语言（便捷接口）
    
    - **code**: 语言代码（如 'en', 'zh-CN'）
    """
    logger.info(f"开始获取语言: code={code}, user_id={current_user.user_id}")
    try:
        return await service.get_language_by_code(code=code)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"语言代码 {code} 不存在"
        )
    except ValidationException as e:
        detail_msg = e.detail.get("message", "无效的语言代码格式") if isinstance(e.detail, dict) else str(e.detail)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail_msg
        )
    except Exception as e:
        logger.error(f"获取语言失败: code={code}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取语言失败: {str(e)}"
        )


@router.post("/", response_model=LanguageResponse, status_code=status.HTTP_201_CREATED, summary="创建新语言")
async def create_language(
    language_data: LanguageCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("language:create")),
    service: LanguageService = Depends(get_service(LanguageService)),
):
    """
    创建新语言
    
    - **name**: 语言名称（必填）
    - **code**: 语言代码（必填，2-5个字符）
    - **locale**: 区域设置（可选）
    - **extension**: 扩展名（可选）
    - **sort_order**: 排序（可选，默认0）
    - **status**: 状态（可选，默认0=禁用）
    """
    logger.info(f"开始创建语言: name={language_data.name}, code={language_data.code}, user_id={current_user.user_id}")
    try:
        return await service.create_language(language_data)
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "语言代码已存在"))
        )
    except Exception as e:
        logger.error(f"创建语言失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建语言失败: {str(e)}"
        )


@router.put("/{language_id}", response_model=LanguageResponse, summary="更新语言信息")
async def update_language(
    language_id: int,
    language_data: LanguageUpdate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("language:update")),
    service: LanguageService = Depends(get_service(LanguageService)),
):
    """
    更新语言信息
    
    - **language_id**: 语言ID
    - **name**: 语言名称（可选）
    - **code**: 语言代码（可选）
    - **locale**: 区域设置（可选）
    - **extension**: 扩展名（可选）
    - **sort_order**: 排序（可选）
    - **status**: 状态（可选）
    """
    logger.info(f"开始更新语言: language_id={language_id}, user_id={current_user.user_id}")
    try:
        return await service.update_language(language_id=language_id, data=language_data)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"语言ID {language_id} 不存在"
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "语言代码已存在"))
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "验证失败"))
        )
    except Exception as e:
        logger.error(f"更新语言失败: language_id={language_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新语言失败: {str(e)}"
        )


@router.delete("/{language_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除语言")
async def delete_language(
    language_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("language:delete")),
    service: LanguageService = Depends(get_service(LanguageService)),
):
    """
    删除语言
    
    - **language_id**: 语言ID
    
    注意：删除前会检查是否有其他数据引用该语言
    """
    logger.info(f"开始删除语言: language_id={language_id}, user_id={current_user.user_id}")
    try:
        await service.delete_language(language_id=language_id)
        return None
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"语言ID {language_id} 不存在"
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "语言正在被使用，无法删除"))
        )
    except Exception as e:
        logger.error(f"删除语言失败: language_id={language_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除语言失败: {str(e)}"
        )
