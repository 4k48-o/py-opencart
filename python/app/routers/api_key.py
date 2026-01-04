"""
API Key management router
"""
import logging
import secrets
import base64
from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List, Optional
from tortoise.exceptions import DoesNotExist, IntegrityError
from datetime import datetime

from app.models.system.api import Api
from app.schemas.api import (
    ApiKeyCreate,
    ApiKeyUpdate,
    ApiKeyResponse,
    ApiKeyCreateResponse,
)
from app.core.security import get_password_hash
from app.api.deps import get_current_user, require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/api-keys", tags=["api-keys"])


def generate_api_key() -> str:
    """
    生成API密钥（64字符，Base64编码）
    
    Returns:
        str: API密钥
    """
    random_bytes = secrets.token_bytes(48)  # 48字节 = 384位
    api_key = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
    # 确保长度为64字符
    api_key = api_key[:64].ljust(64, '0')
    return api_key


@router.get("/", response_model=List[ApiKeyResponse], summary="获取API密钥列表")
async def list_api_keys(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    status: Optional[int] = Query(None, ge=0, le=1, description="状态筛选 (0=禁用, 1=启用)"),
    current_user = Depends(get_current_user),
    _: bool = Depends(require_permission("api:read")),
):
    """
    获取API密钥列表
    
    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的记录数（最大1000）
    - **status**: 状态筛选（可选）
    """
    logger.info("开始获取API密钥列表")
    try:
        query = Api.all()
        
        if status is not None:
            query = query.filter(status=status)
        
        api_keys = await query.offset(skip).limit(limit)
        # 不返回密钥内容（安全考虑）
        result = []
        for api_key in api_keys:
            api_dict = ApiKeyResponse.model_validate(api_key).model_dump()
            api_dict['key'] = None  # 不返回密钥
            result.append(ApiKeyResponse(**api_dict))
        
        logger.info("API密钥列表获取完成")
        return result
    except Exception as e:
        logger.error(f"获取API密钥列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取API密钥列表失败: {str(e)}"
        )


@router.get("/{api_id}", response_model=ApiKeyResponse, summary="根据ID获取API密钥")
async def get_api_key(
    api_id: int,
    current_user = Depends(get_current_user),
    _: bool = Depends(require_permission("api:read")),
):
    """
    根据ID获取API密钥信息（不返回密钥内容）
    
    - **api_id**: API密钥ID
    """
    logger.info(f"开始获取API密钥信息: api_id={api_id}")
    try:
        api_key = await Api.get(api_id=api_id)
        api_dict = ApiKeyResponse.model_validate(api_key).model_dump()
        api_dict['key'] = None  # 不返回密钥
        logger.info(f"API密钥信息获取完成: api_id={api_id}")
        return ApiKeyResponse(**api_dict)
    except DoesNotExist:
        logger.warning(f"API密钥不存在: api_id={api_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API密钥ID {api_id} 不存在"
        )
    except Exception as e:
        logger.error(f"获取API密钥信息失败: api_id={api_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取API密钥信息失败: {str(e)}"
        )


@router.post("/", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED, summary="创建新API密钥")
async def create_api_key(
    api_data: ApiKeyCreate,
    current_user = Depends(get_current_user),
    _: bool = Depends(require_permission("api:create")),
):
    """
    创建新API密钥
    
    - **username**: API用户名（必填）
    - **status**: 状态（可选，默认1=启用）
    
    注意：API密钥仅在创建时返回一次，请妥善保管
    """
    logger.info(f"开始创建API密钥: username={api_data.username}")
    try:
        # 检查用户名是否已存在
        existing_api = await Api.filter(username=api_data.username).first()
        if existing_api:
            logger.warning(f"API用户名已存在: username={api_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"API用户名 {api_data.username} 已存在"
            )
        
        # 生成API密钥
        api_key_value = generate_api_key()
        
        # 加密存储密钥（使用密码哈希函数）
        hashed_key = get_password_hash(api_key_value)
        
        # 创建API密钥记录
        api_key = await Api.create(
            username=api_data.username,
            key=hashed_key,
            status=api_data.status,
            date_added=datetime.now(),
            date_modified=datetime.now()
        )
        
        logger.info(f"API密钥创建完成: api_id={api_key.api_id}, username={api_data.username}")
        
        # 返回响应（包含原始密钥，仅此一次）
        return ApiKeyCreateResponse(
            api_id=api_key.api_id,
            username=api_key.username or "",
            key=api_key_value,  # 返回原始密钥
            status=api_key.status or 0,
            message="请妥善保管API密钥，系统不会再次显示"
        )
    except HTTPException:
        raise
    except IntegrityError as e:
        logger.error(f"创建API密钥失败（完整性错误）: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建API密钥失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"创建API密钥失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建API密钥失败: {str(e)}"
        )


@router.put("/{api_id}", response_model=ApiKeyResponse, summary="更新API密钥信息")
async def update_api_key(
    api_id: int,
    api_data: ApiKeyUpdate,
    current_user = Depends(get_current_user),
    _: bool = Depends(require_permission("api:update")),
):
    """
    更新API密钥信息（不能更新密钥本身）
    
    - **api_id**: API密钥ID
    - **username**: API用户名（可选）
    - **status**: 状态（可选）
    """
    logger.info(f"开始更新API密钥: api_id={api_id}")
    try:
        api_key = await Api.get(api_id=api_id)
        update_data = api_data.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有需要更新的字段"
            )
        
        # 如果更新用户名，检查是否重复
        if 'username' in update_data and update_data['username'] != api_key.username:
            existing_api = await Api.filter(username=update_data['username']).first()
            if existing_api and existing_api.api_id != api_id:
                logger.warning(f"API用户名已存在: username={update_data['username']}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"API用户名 {update_data['username']} 已存在"
                )
        
        # 更新字段
        for key, value in update_data.items():
            setattr(api_key, key, value)
        
        api_key.date_modified = datetime.now()
        await api_key.save()
        
        logger.info(f"API密钥更新完成: api_id={api_id}")
        
        api_dict = ApiKeyResponse.model_validate(api_key).model_dump()
        api_dict['key'] = None  # 不返回密钥
        return ApiKeyResponse(**api_dict)
    except HTTPException:
        raise
    except DoesNotExist:
        logger.warning(f"API密钥不存在: api_id={api_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API密钥ID {api_id} 不存在"
        )
    except Exception as e:
        logger.error(f"更新API密钥失败: api_id={api_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新API密钥失败: {str(e)}"
        )


@router.delete("/{api_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除API密钥")
async def delete_api_key(
    api_id: int,
    current_user = Depends(get_current_user),
    _: bool = Depends(require_permission("api:delete")),
):
    """
    删除API密钥
    
    - **api_id**: API密钥ID
    """
    logger.info(f"开始删除API密钥: api_id={api_id}")
    try:
        api_key = await Api.get(api_id=api_id)
        await api_key.delete()
        logger.info(f"API密钥删除完成: api_id={api_id}")
        return None
    except DoesNotExist:
        logger.warning(f"API密钥不存在: api_id={api_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API密钥ID {api_id} 不存在"
        )
    except Exception as e:
        logger.error(f"删除API密钥失败: api_id={api_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除API密钥失败: {str(e)}"
        )

