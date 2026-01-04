"""
Currency API router
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

from app.schemas.currency import CurrencyCreate, CurrencyUpdate, CurrencyResponse
from app.services.currency_service import CurrencyService
from app.exceptions import NotFoundException, ConflictException, ValidationException
from app.api.deps import get_current_user, require_permission, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/currencies", tags=["currencies"])


@router.get("/", response_model=List[CurrencyResponse], summary="获取货币列表")
async def list_currencies(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    status: Optional[int] = Query(None, ge=0, le=1, description="状态筛选（0=禁用，1=启用）"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("currency:read")),
    service: CurrencyService = Depends(get_service(CurrencyService)),
):
    """
    获取货币列表
    
    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的记录数（最大1000）
    - **status**: 状态筛选（可选，0=禁用，1=启用）
    """
    logger.info(f"开始获取货币列表: skip={skip}, limit={limit}, user_id={current_user.user_id}")
    try:
        return await service.list_currencies(skip=skip, limit=limit, status=status)
    except Exception as e:
        logger.error(f"获取货币列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取货币列表失败: {str(e)}"
        )


@router.get("/{currency_id}", response_model=CurrencyResponse, summary="根据ID获取货币")
async def get_currency(
    currency_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("currency:read")),
    service: CurrencyService = Depends(get_service(CurrencyService)),
):
    """
    根据ID获取货币信息
    
    - **currency_id**: 货币ID
    """
    logger.info(f"开始获取货币信息: currency_id={currency_id}, user_id={current_user.user_id}")
    try:
        return await service.get_currency(currency_id=currency_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"货币ID {currency_id} 不存在"
        )
    except Exception as e:
        logger.error(f"获取货币信息失败: currency_id={currency_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取货币信息失败: {str(e)}"
        )


@router.get("/by-code/{code}", response_model=CurrencyResponse, summary="根据代码获取货币")
async def get_currency_by_code(
    code: str,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("currency:read")),
    service: CurrencyService = Depends(get_service(CurrencyService)),
):
    """
    根据货币代码获取货币（便捷接口）
    
    - **code**: 货币代码（如 'USD', 'CNY'）
    """
    logger.info(f"开始获取货币: code={code}, user_id={current_user.user_id}")
    try:
        return await service.get_currency_by_code(code=code)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"货币代码 {code} 不存在"
        )
    except ValidationException as e:
        detail_msg = e.detail.get("message", "无效的货币代码格式") if isinstance(e.detail, dict) else str(e.detail)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg
        )
    except Exception as e:
        logger.error(f"获取货币失败: code={code}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取货币失败: {str(e)}"
        )


@router.post("/", response_model=CurrencyResponse, status_code=status.HTTP_201_CREATED, summary="创建新货币")
async def create_currency(
    currency_data: CurrencyCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("currency:create")),
    service: CurrencyService = Depends(get_service(CurrencyService)),
):
    """
    创建新货币
    
    - **title**: 货币名称（必填）
    - **code**: 货币代码（必填，ISO 4217格式，3个大写字母）
    - **symbol_left**: 左侧符号（可选）
    - **symbol_right**: 右侧符号（可选）
    - **decimal_place**: 小数位数（可选，默认2）
    - **value**: 汇率（必填，正数）
    - **status**: 状态（可选，默认0=禁用）
    """
    logger.info(f"开始创建货币: title={currency_data.title}, code={currency_data.code}, user_id={current_user.user_id}")
    try:
        return await service.create_currency(currency_data)
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "货币代码已存在"))
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "验证失败"))
        )
    except Exception as e:
        logger.error(f"创建货币失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建货币失败: {str(e)}"
        )


@router.put("/{currency_id}", response_model=CurrencyResponse, summary="更新货币信息")
async def update_currency(
    currency_id: int,
    currency_data: CurrencyUpdate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("currency:update")),
    service: CurrencyService = Depends(get_service(CurrencyService)),
):
    """
    更新货币信息
    
    - **currency_id**: 货币ID
    - **title**: 货币名称（可选）
    - **code**: 货币代码（可选）
    - **symbol_left**: 左侧符号（可选）
    - **symbol_right**: 右侧符号（可选）
    - **decimal_place**: 小数位数（可选）
    - **value**: 汇率（可选）
    - **status**: 状态（可选）
    
    注意：更新时会自动更新 date_modified 字段
    """
    logger.info(f"开始更新货币: currency_id={currency_id}, user_id={current_user.user_id}")
    try:
        return await service.update_currency(currency_id=currency_id, data=currency_data)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"货币ID {currency_id} 不存在"
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "货币代码已存在"))
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "验证失败"))
        )
    except Exception as e:
        logger.error(f"更新货币失败: currency_id={currency_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新货币失败: {str(e)}"
        )


@router.put("/{currency_id}/rate", response_model=CurrencyResponse, summary="更新汇率")
async def update_currency_rate(
    currency_id: int,
    value: float = Query(..., ge=0, description="新汇率（正数）"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("currency:update")),
    service: CurrencyService = Depends(get_service(CurrencyService)),
):
    """
    更新货币汇率（便捷接口）
    
    - **currency_id**: 货币ID
    - **value**: 新汇率（必填，正数）
    
    注意：更新时会自动更新 date_modified 字段
    """
    logger.info(f"开始更新汇率: currency_id={currency_id}, value={value}, user_id={current_user.user_id}")
    try:
        return await service.update_currency_rate(currency_id=currency_id, rate=value)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"货币ID {currency_id} 不存在"
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "汇率必须是正数"))
        )
    except Exception as e:
        logger.error(f"更新汇率失败: currency_id={currency_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新汇率失败: {str(e)}"
        )


@router.delete("/{currency_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除货币")
async def delete_currency(
    currency_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("currency:delete")),
    service: CurrencyService = Depends(get_service(CurrencyService)),
):
    """
    删除货币
    
    - **currency_id**: 货币ID
    
    注意：删除前会检查是否有其他数据引用该货币
    """
    logger.info(f"开始删除货币: currency_id={currency_id}, user_id={current_user.user_id}")
    try:
        await service.delete_currency(currency_id=currency_id)
        return None
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"货币ID {currency_id} 不存在"
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "货币正在被使用，无法删除"))
        )
    except Exception as e:
        logger.error(f"删除货币失败: currency_id={currency_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除货币失败: {str(e)}"
        )
