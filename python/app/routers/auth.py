"""
Authentication API router
"""
import logging
from fastapi import APIRouter, HTTPException, status, Depends, Request
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest, LogoutRequest
from app.services.auth_service import AuthService
from app.models.system.user_login import UserLogin
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(
    login_data: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends()
):
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    
    返回Access Token和Refresh Token
    """
    logger.info(f"开始用户登录: username={login_data.username}")
    try:
        user = await auth_service.authenticate_user(
            login_data.username,
            login_data.password
        )
        
        if not user:
            logger.warning(f"登录失败: username={login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 获取客户端IP和User-Agent
        client_ip = request.client.host if request.client else None
        # 如果使用了代理，尝试从X-Forwarded-For头获取真实IP
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        user_agent = request.headers.get("user-agent", "")
        
        # 创建Token（传递IP和User-Agent用于安全审计）
        tokens = await auth_service.create_tokens(user, ip_address=client_ip, user_agent=user_agent)
        
        # 记录登录日志
        try:
            await UserLogin.create(
                user_id=user.user_id,
                ip=client_ip or "",
                user_agent=user_agent,
                date_added=datetime.now()
            )
        except Exception as e:
            logger.warning(f"记录登录日志失败: {str(e)}")
        
        logger.info(f"用户登录成功: user_id={user.user_id}, username={login_data.username}")
        return tokens
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: username={login_data.username}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse, summary="刷新Access Token")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    auth_service: AuthService = Depends()
):
    """
    刷新Access Token
    
    - **refresh_token**: Refresh Token
    
    返回新的Access Token和Refresh Token
    """
    logger.info("开始刷新Access Token")
    try:
        # 获取客户端IP和User-Agent
        client_ip = request.client.host if request.client else None
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        user_agent = request.headers.get("user-agent", "")
        
        tokens = await auth_service.refresh_access_token(
            refresh_data.refresh_token,
            ip_address=client_ip,
            user_agent=user_agent
        )
        logger.info("Access Token刷新成功")
        return tokens
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新Token失败: error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout", summary="用户登出")
async def logout(
    logout_data: LogoutRequest,
    auth_service: AuthService = Depends()
):
    """
    用户登出
    
    - **refresh_token**: Refresh Token
    
    撤销Refresh Token
    """
    logger.info("开始用户登出")
    try:
        success = await auth_service.revoke_token(logout_data.refresh_token)
        if success:
            logger.info("用户登出成功")
            return {"message": "Logged out successfully"}
        else:
            logger.warning("撤销Token失败")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to revoke token"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登出失败: error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

