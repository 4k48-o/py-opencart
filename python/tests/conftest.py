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

# 在模块级别设置测试环境变量（在任何导入之前）
# 确保FastAPI应用导入时就能检测到测试环境
# 这是架构组推荐方案2的实现：确保TESTING环境变量在所有代码执行前就设置好
os.environ["TESTING"] = "1"

# 使用pytest_configure hook确保环境变量在pytest加载任何测试文件之前就设置好
# 这比模块级别的设置更早，可以确保即使测试文件在导入时就创建FastAPI应用，也能检测到测试环境
def pytest_configure(config):
    """pytest配置hook，在pytest加载任何测试文件之前执行"""
    os.environ["TESTING"] = "1"
    os.environ["PYTEST"] = "1"

# 在pytest会话开始时也设置一次（双重保险）
@pytest.fixture(scope="session", autouse=True)
def set_testing_env():
    """在pytest会话开始时设置测试环境变量（双重保险）
    
    注意：TESTING环境变量已在模块级别设置，此fixture作为双重保险。
    确保在所有fixture和测试执行前就设置好，让FastAPI的startup_event能检测到测试环境。
    """
    os.environ["TESTING"] = "1"
    yield
    # 测试结束后清理（可选）
    # os.environ.pop("TESTING", None)


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
    """Setup database connection for tests
    
    注意：TESTING环境变量已在session级别的fixture中设置（set_testing_env），
    确保FastAPI的startup_event跳过init_db()，使用db_setup创建的连接，
    避免双重连接导致的事务隔离问题。这是架构组推荐方案2的实现。
    """
    db_config = get_test_db_config()
    
    # 构建数据库连接URL
    # 如果密码为空，则不包含密码部分
    # 注意：不需要在URL中添加max_connections参数，Tortoise ORM会自动管理连接池
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
    
    # 清理测试环境变量（可选，不影响其他测试）
    # os.environ.pop("TESTING", None)


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
    """Create a database transaction for each test
    
    注意：根据架构组分析（19-制造商API测试失败架构层面根本原因分析.md），
    我们已经实现了方案1（统一数据库连接），让FastAPI应用复用测试环境的连接。
    因此不需要修改事务隔离级别，保持MySQL默认的REPEATABLE READ隔离级别即可。
    """
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
        "manufacturer": ["read", "create", "update", "delete"],
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
async def async_client(db_setup, db_transaction):
    """Create an async HTTP client for testing
    
    注意：
    1. db_setup已经初始化了Tortoise ORM，创建了连接A
    2. db_transaction在连接A上启动了事务
    3. TESTING环境变量已在模块级别和pytest_configure中设置
    4. FastAPI的startup_event应该能检测到测试环境并跳过init_db()，使用db_setup创建的连接A
    5. async_client现在也依赖db_transaction，确保API请求在同一个事务中执行
    
    关键：ASGITransport在第一次请求时会自动触发startup事件，此时startup_event会检测到
    TESTING=1并跳过init_db()，确保API使用db_setup创建的连接A，从而能看到db_transaction中的未提交数据。
    """
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    
    # 确保环境变量已设置（双重保险）
    import os
    if os.getenv("TESTING") != "1":
        os.environ["TESTING"] = "1"
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("async_client: TESTING环境变量未设置，已重新设置")
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

