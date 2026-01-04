"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from tortoise import Tortoise
from app.config import settings
from app.models.system.user import User
from app.models.system.user_group import UserGroup
from app.core.security import get_password_hash, create_access_token
from dotenv import load_dotenv

# 加载测试环境变量（如果存在 .env.test 文件）
test_env_path = Path(__file__).parent.parent / ".env.test"
if test_env_path.exists():
    load_dotenv(test_env_path)
else:
    # 尝试加载 .env 文件
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def get_test_db_config():
    """获取测试数据库配置"""
    # 优先使用测试环境变量，否则使用默认配置
    db_host = os.getenv("TEST_DB_HOST") or os.getenv("DB_HOST") or settings.db_host
    db_port = int(os.getenv("TEST_DB_PORT") or os.getenv("DB_PORT") or settings.db_port)
    db_user = os.getenv("TEST_DB_USER") or os.getenv("DB_USER") or settings.db_user
    db_password = os.getenv("TEST_DB_PASSWORD") or os.getenv("DB_PASSWORD") or settings.db_password
    
    # 数据库名称处理：如果设置了TEST_DB_NAME，直接使用；否则根据DB_NAME生成
    test_db_name = os.getenv("TEST_DB_NAME")
    if test_db_name:
        db_name = test_db_name
    else:
        base_db_name = os.getenv("DB_NAME") or settings.db_name
        # 如果数据库名已经以_test结尾，不再添加
        if base_db_name.endswith("_test"):
            db_name = base_db_name
        else:
            db_name = f"{base_db_name}_test"
    
    return {
        "host": db_host,
        "port": db_port,
        "user": db_user,
        "password": db_password,
        "name": db_name,
    }


def get_test_redis_config():
    """获取测试Redis配置"""
    # 优先使用测试环境变量，否则使用默认配置
    redis_host = os.getenv("TEST_REDIS_HOST") or os.getenv("REDIS_HOST") or settings.redis_host
    redis_port = int(os.getenv("TEST_REDIS_PORT") or os.getenv("REDIS_PORT") or settings.redis_port)
    redis_password = os.getenv("TEST_REDIS_PASSWORD") or os.getenv("REDIS_PASSWORD") or settings.redis_password
    redis_db = int(os.getenv("TEST_REDIS_DB") or os.getenv("REDIS_DB", "1"))  # 使用DB 1作为测试数据库
    
    return {
        "host": redis_host,
        "port": redis_port,
        "password": redis_password,
        "db": redis_db,
    }


@pytest.fixture(scope="function")
async def db_setup():
    """Setup database connection for tests"""
    db_config = get_test_db_config()
    
    # 构建数据库连接URL
    # 如果密码为空，则不包含密码部分
    if db_config["password"]:
        db_url = f"mysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['name']}"
    else:
        db_url = f"mysql://{db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['name']}"
    
    await Tortoise.init(
        db_url=db_url,
        modules={
            "models": [
                "app.models.system",
                "app.models.localisation",
                "app.models.customer",
                "app.models.catalog",
                "app.models.order",
                "app.models.marketing",
                "app.models.cms",
                "app.models.design",
                "app.models.report",
            ]
        },
    )
    yield
    await Tortoise.close_connections()


@pytest.fixture(scope="function")
async def redis_setup():
    """Setup Redis connection for tests"""
    from app.core.redis_client import get_redis_client, close_redis_client
    
    redis_config = get_test_redis_config()
    
    # 临时设置Redis配置到环境变量（用于get_redis_client读取）
    original_host = os.getenv("REDIS_HOST")
    original_port = os.getenv("REDIS_PORT")
    original_password = os.getenv("REDIS_PASSWORD")
    original_db = os.getenv("REDIS_DB")
    
    try:
        # 设置测试Redis配置
        os.environ["REDIS_HOST"] = redis_config["host"]
        os.environ["REDIS_PORT"] = str(redis_config["port"])
        if redis_config["password"]:
            os.environ["REDIS_PASSWORD"] = redis_config["password"]
        os.environ["REDIS_DB"] = str(redis_config["db"])
        
        # 重新加载settings以获取新的Redis配置
        from importlib import reload
        import app.config
        reload(app.config)
        
        # 初始化Redis连接
        try:
            redis_client = await get_redis_client()
            await redis_client.ping()
            # 清理测试数据库
            await redis_client.flushdb()
        except Exception as e:
            # Redis不可用时，记录警告但不阻止测试
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Redis连接失败，测试将在无Redis模式下运行: {str(e)}")
        
        yield redis_client if 'redis_client' in locals() else None
        
    finally:
        # 恢复原始配置
        if original_host:
            os.environ["REDIS_HOST"] = original_host
        elif "REDIS_HOST" in os.environ:
            del os.environ["REDIS_HOST"]
            
        if original_port:
            os.environ["REDIS_PORT"] = original_port
        elif "REDIS_PORT" in os.environ:
            del os.environ["REDIS_PORT"]
            
        if original_password:
            os.environ["REDIS_PASSWORD"] = original_password
        elif "REDIS_PASSWORD" in os.environ:
            del os.environ["REDIS_PASSWORD"]
            
        if original_db:
            os.environ["REDIS_DB"] = original_db
        elif "REDIS_DB" in os.environ:
            del os.environ["REDIS_DB"]
        
        # 关闭Redis连接
        try:
            await close_redis_client()
        except:
            pass


@pytest.fixture
async def db_transaction(db_setup):
    """Create a database transaction for each test"""
    # Start transaction
    connection = Tortoise.get_connection("default")
    await connection.execute_query("START TRANSACTION")
    
    yield
    
    # Rollback transaction
    await connection.execute_query("ROLLBACK")


@pytest.fixture
async def test_user_group(db_transaction):
    """Create a test user group with all permissions"""
    permissions = {
        "store": ["read", "create", "update", "delete"],
        "setting": ["read", "create", "update", "delete"],
        "language": ["read", "create", "update", "delete"],
        "currency": ["read", "create", "update", "delete"],
        "user": ["read", "create", "update", "delete"],
        "attribute_group": ["read", "create", "update", "delete"],
        "category": ["read", "create", "update", "delete"],
        "product": ["read", "create", "update", "delete"],
    }
    
    user_group = UserGroup(
        name="Test Admin Group",
        permission=json.dumps(permissions)
    )
    await user_group.save()
    return user_group


@pytest.fixture
async def test_user(db_transaction, test_user_group):
    """Create a test user with admin permissions"""
    user = User(
        username="testadmin",
        password=get_password_hash("testpass123"),
        user_group_id=test_user_group.user_group_id,
        email="testadmin@example.com",
        firstname="Test",
        lastname="Admin",
        status=1,
        date_added=datetime.now()
    )
    await user.save()
    return user


@pytest.fixture
async def auth_token(db_transaction, test_user):
    """Create an authentication token for test user"""
    from app.core.permissions import get_user_permissions
    
    permissions = await get_user_permissions(test_user)
    token_data = {
        "sub": str(test_user.user_id),
        "username": test_user.username or "",
        "email": test_user.email or "",
        "user_group_id": test_user.user_group_id or 0,
        "permissions": permissions
    }
    token = create_access_token(token_data)
    return token


@pytest.fixture
def auth_headers_sync(test_user):
    """Get authentication headers for API requests (synchronous version)"""
    import asyncio
    from app.core.permissions import get_user_permissions
    
    # Run async function in sync context
    loop = asyncio.get_event_loop()
    permissions = loop.run_until_complete(get_user_permissions(test_user))
    
    token_data = {
        "sub": str(test_user.user_id),
        "username": test_user.username or "",
        "email": test_user.email or "",
        "user_group_id": test_user.user_group_id or 0,
        "permissions": permissions
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def auth_headers(db_transaction, test_user):
    """Get authentication headers for API requests (async version)"""
    from app.core.permissions import get_user_permissions
    
    permissions = await get_user_permissions(test_user)
    token_data = {
        "sub": str(test_user.user_id),
        "username": test_user.username or "",
        "email": test_user.email or "",
        "user_group_id": test_user.user_group_id or 0,
        "permissions": permissions
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def async_client(db_setup):
    """Create an async HTTP client for testing"""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

