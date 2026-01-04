"""
Setting API router
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

from app.schemas.setting import SettingCreate, SettingUpdate, SettingResponse
from app.services.setting_service import SettingService
from app.exceptions import NotFoundException, ConflictException, ValidationException
from app.api.deps import get_current_user, require_permission, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


# ==================== Timezone Settings ====================
# 注意：时区相关路由必须定义在 /{setting_id} 路由之前，避免路由冲突

@router.get("/timezone", response_model=SettingResponse, summary="获取时区设置")
async def get_timezone(
    store_id: int = Query(0, ge=0, description="店铺ID（默认0）"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("setting:read")),
    service: SettingService = Depends(get_service(SettingService)),
):
    """
    获取当前时区设置
    
    - **store_id**: 店铺ID（默认0，表示默认店铺）
    
    返回时区配置（code='config', key='config_timezone'）
    """
    logger.info(f"开始获取时区设置: store_id={store_id}, user_id={current_user.user_id}")
    try:
        return await service.get_timezone(store_id=store_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="时区设置不存在，默认时区为 UTC"
        )
    except Exception as e:
        logger.error(f"获取时区设置失败: store_id={store_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取时区设置失败: {str(e)}"
        )


@router.put("/timezone", response_model=SettingResponse, summary="更新时区设置")
async def update_timezone(
    timezone: str = Query(..., description="时区（如 'Asia/Shanghai', 'UTC', 'America/New_York'）"),
    store_id: int = Query(0, ge=0, description="店铺ID（默认0）"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("setting:update")),
    service: SettingService = Depends(get_service(SettingService)),
):
    """
    更新时区设置
    
    - **timezone**: 时区字符串（必填，如 'Asia/Shanghai', 'UTC', 'America/New_York'）
    - **store_id**: 店铺ID（默认0，表示默认店铺）
    
    支持的时区格式：IANA时区数据库格式（如 'Asia/Shanghai'）或 UTC
    """
    logger.info(f"开始更新时区设置: timezone={timezone}, store_id={store_id}, user_id={current_user.user_id}")
    try:
        return await service.update_timezone(timezone=timezone, store_id=store_id)
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "时区格式无效"))
        )
    except Exception as e:
        logger.error(f"更新时区设置失败: timezone={timezone}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新时区设置失败: {str(e)}"
        )


@router.get("/timezones", response_model=List[str], summary="获取常用时区列表")
async def list_timezones(
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("setting:read")),
    service: SettingService = Depends(get_service(SettingService)),
):
    """
    获取常用时区列表
    
    返回常用时区列表，供前端选择使用
    """
    logger.info(f"开始获取时区列表: user_id={current_user.user_id}")
    try:
        return await service.list_timezones()
    except Exception as e:
        logger.error(f"获取时区列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取时区列表失败: {str(e)}"
        )


# ==================== Setting CRUD ====================

@router.get("/", response_model=List[SettingResponse], summary="获取配置列表")
async def list_settings(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    store_id: Optional[int] = Query(None, ge=0, description="店铺ID筛选"),
    code: Optional[str] = Query(None, description="配置代码筛选"),
    key: Optional[str] = Query(None, description="配置键名筛选"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("setting:read")),
    service: SettingService = Depends(get_service(SettingService)),
):
    """
    获取配置列表
    
    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的记录数（最大1000）
    - **store_id**: 店铺ID筛选（可选）
    - **code**: 配置代码筛选（可选）
    - **key**: 配置键名筛选（可选）
    """
    logger.info(f"开始获取配置列表: skip={skip}, limit={limit}, user_id={current_user.user_id}")
    try:
        return await service.list_settings(
            skip=skip,
            limit=limit,
            store_id=store_id,
            code=code,
            key=key
        )
    except Exception as e:
        logger.error(f"获取配置列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置列表失败: {str(e)}"
        )


@router.get("/{setting_id}", response_model=SettingResponse, summary="根据ID获取配置")
async def get_setting(
    setting_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("setting:read")),
    service: SettingService = Depends(get_service(SettingService)),
):
    """
    根据ID获取配置信息
    
    - **setting_id**: 配置ID
    """
    logger.info(f"开始获取配置信息: setting_id={setting_id}, user_id={current_user.user_id}")
    try:
        return await service.get_setting(setting_id=setting_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置ID {setting_id} 不存在"
        )
    except Exception as e:
        logger.error(f"获取配置信息失败: setting_id={setting_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置信息失败: {str(e)}"
        )


@router.get("/by-key/{code}/{key}", response_model=SettingResponse, summary="根据code和key获取配置")
async def get_setting_by_key(
    code: str,
    key: str,
    store_id: int = Query(0, ge=0, description="店铺ID（默认0）"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("setting:read")),
    service: SettingService = Depends(get_service(SettingService)),
):
    """
    根据配置代码和键名获取配置（便捷接口）
    
    - **code**: 配置代码
    - **key**: 配置键名
    - **store_id**: 店铺ID（默认0）
    """
    logger.info(f"开始获取配置: code={code}, key={key}, store_id={store_id}, user_id={current_user.user_id}")
    try:
        return await service.get_setting_by_key(code=code, key=key, store_id=store_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置不存在: code={code}, key={key}, store_id={store_id}"
        )
    except Exception as e:
        logger.error(f"获取配置失败: code={code}, key={key}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置失败: {str(e)}"
        )


@router.post("/", response_model=SettingResponse, status_code=status.HTTP_201_CREATED, summary="创建新配置")
async def create_setting(
    setting_data: SettingCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("setting:create")),
    service: SettingService = Depends(get_service(SettingService)),
):
    """
    创建新配置
    
    - **code**: 配置代码（必填）
    - **key**: 配置键名（必填）
    - **value**: 配置值（必填）
    - **store_id**: 店铺ID（可选，默认0）
    - **serialized**: 是否序列化（可选，默认0）
    """
    logger.info(f"开始创建配置: code={setting_data.code}, key={setting_data.key}, user_id={current_user.user_id}")
    try:
        return await service.create_setting(setting_data)
    except ConflictException as e:
        detail_msg = e.detail.get("message", "配置已存在") if isinstance(e.detail, dict) else str(e.detail)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg
        )
    except ValidationException as e:
        detail_msg = e.detail.get("message", "验证失败") if isinstance(e.detail, dict) else str(e.detail)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg
        )
    except Exception as e:
        logger.error(f"创建配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建配置失败: {str(e)}"
        )


@router.put("/{setting_id}", response_model=SettingResponse, summary="更新配置信息")
async def update_setting(
    setting_id: int,
    setting_data: SettingUpdate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("setting:update")),
    service: SettingService = Depends(get_service(SettingService)),
):
    """
    更新配置信息
    
    - **setting_id**: 配置ID
    - **code**: 配置代码（可选）
    - **key**: 配置键名（可选）
    - **value**: 配置值（可选）
    - **store_id**: 店铺ID（可选）
    - **serialized**: 是否序列化（可选）
    """
    logger.info(f"开始更新配置: setting_id={setting_id}, user_id={current_user.user_id}")
    try:
        return await service.update_setting(setting_id=setting_id, data=setting_data)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置ID {setting_id} 不存在"
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "配置冲突"))
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "验证失败"))
        )
    except Exception as e:
        logger.error(f"更新配置失败: setting_id={setting_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新配置失败: {str(e)}"
        )


@router.put("/by-key/{code}/{key}", response_model=SettingResponse, summary="根据code和key更新配置")
async def update_setting_by_key(
    code: str,
    key: str,
    setting_data: SettingUpdate,
    store_id: int = Query(0, ge=0, description="店铺ID（默认0）"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("setting:update")),
    service: SettingService = Depends(get_service(SettingService)),
):
    """
    根据配置代码和键名更新配置（便捷接口）
    
    - **code**: 配置代码
    - **key**: 配置键名
    - **store_id**: 店铺ID（默认0）
    - **value**: 配置值（可选）
    - **serialized**: 是否序列化（可选）
    """
    logger.info(f"开始更新配置: code={code}, key={key}, store_id={store_id}, user_id={current_user.user_id}")
    try:
        return await service.update_setting_by_key(
            code=code,
            key=key,
            store_id=store_id,
            data=setting_data
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置不存在: code={code}, key={key}, store_id={store_id}"
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "验证失败"))
        )
    except Exception as e:
        logger.error(f"更新配置失败: code={code}, key={key}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新配置失败: {str(e)}"
        )


@router.delete("/{setting_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除配置")
async def delete_setting(
    setting_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("setting:delete")),
    service: SettingService = Depends(get_service(SettingService)),
):
    """
    删除配置
    
    - **setting_id**: 配置ID
    """
    logger.info(f"开始删除配置: setting_id={setting_id}, user_id={current_user.user_id}")
    try:
        await service.delete_setting(setting_id=setting_id)
        return None
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置ID {setting_id} 不存在"
        )
    except Exception as e:
        logger.error(f"删除配置失败: setting_id={setting_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除配置失败: {str(e)}"
        )
