"""
Tortoise ORM database configuration
"""
import json
import logging
import traceback
from tortoise import Tortoise
from app.config import settings

logger = logging.getLogger(__name__)

# #region agent log
def _log_debug(session_id, run_id, hypothesis_id, location, message, data=None):
    try:
        with open('/Users/laoyang/code/ai/opencart-4.1.0.3/.cursor/debug.log', 'a') as f:
            log_entry = {
                "sessionId": session_id,
                "runId": run_id,
                "hypothesisId": hypothesis_id,
                "location": location,
                "message": message,
                "data": data or {},
                "timestamp": __import__('time').time() * 1000
            }
            f.write(json.dumps(log_entry) + '\n')
    except:
        pass
# #endregion agent log


async def init_db():
    """Initialize database connection
    
    注意：在测试环境中，db_setup fixture可能已经初始化了Tortoise ORM。
    如果已经初始化，则跳过初始化，复用现有连接，避免创建多个数据库连接导致事务隔离问题。
    """
    # #region agent log
    _log_debug('debug-session', 'post-fix', 'A', 'database.py:init_db', 'init_db called', {'db_name': settings.db_name, 'db_host': settings.db_host})
    # #endregion agent log
    
    # 检查Tortoise是否已经初始化（测试环境可能已经通过db_setup初始化）
    # 如果已经初始化，跳过初始化，复用现有连接
    # 这是架构组推荐方案1的实现：统一数据库连接，避免双重连接导致的事务隔离问题
    try:
        # 方法1：尝试获取连接，如果能获取到说明已经初始化
        connection = Tortoise.get_connection("default")
        # 检查连接是否真的可用（检查连接对象和pool属性）
        if connection and hasattr(connection, 'pool'):
            # #region agent log
            _log_debug('debug-session', 'post-fix', 'SKIP', 'database.py:init_db', 'Tortoise already initialized, skipping init', {'db_name': settings.db_name})
            # #endregion agent log
            logger.info(f"数据库已初始化，跳过重复初始化（测试环境复用db_setup的连接）")
            return  # 已经初始化，跳过
    except KeyError:
        # KeyError: 连接不存在（未初始化）
        # 需要初始化
        logger.debug("数据库未初始化（KeyError），开始初始化")
        pass
    except (AttributeError, RuntimeError) as e:
        # AttributeError: Tortoise对象没有get_connection方法（未初始化）
        # RuntimeError: 其他运行时错误
        # 需要初始化
        logger.debug(f"数据库未初始化（{type(e).__name__}: {str(e)}），开始初始化")
        pass
    except Exception as e:
        # 捕获其他所有异常，确保即使检查失败也能继续初始化
        # 这是安全措施，避免因为检查逻辑的问题导致初始化失败
        logger.warning(f"检查数据库初始化状态时出现异常（{type(e).__name__}: {str(e)}），将继续初始化", exc_info=True)
        pass
    
    modules_list = [
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
    
    # #region agent log
    _log_debug('debug-session', 'post-fix', 'B', 'database.py:init_db', 'Before Tortoise.init', {'modules': modules_list})
    # #endregion agent log
    
    try:
        await Tortoise.init(
            db_url=f"mysql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}",
            modules={
                "models": modules_list
            },
        )
        # #region agent log
        _log_debug('debug-session', 'post-fix', 'C', 'database.py:init_db', 'Tortoise.init completed successfully')
        # #endregion agent log
    except Exception as e:
        # #region agent log
        _log_debug('debug-session', 'post-fix', 'D', 'database.py:init_db', 'Tortoise.init failed', {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'traceback': traceback.format_exc()
        })
        # #endregion agent log
        raise
    
    # Generate schemas after initialization
    # Note: generate_schemas is optional and may fail if tables already exist
    # It's safe to skip this if database connection fails
    try:
        await Tortoise.generate_schemas()
        # #region agent log
        _log_debug('debug-session', 'post-fix', 'E', 'database.py:init_db', 'generate_schemas completed')
        # #endregion agent log
    except Exception as e:
        # #region agent log
        _log_debug('debug-session', 'post-fix', 'F', 'database.py:init_db', 'generate_schemas failed (non-critical)', {
            'error_type': type(e).__name__,
            'error_message': str(e)
        })
        # #endregion agent log
        # Don't raise - schema generation is optional
        pass


async def close_db():
    """Close database connection"""
    # 检查连接是否存在，避免在测试环境中关闭已关闭的连接
    try:
        connection = Tortoise.get_connection("default")
        await Tortoise.close_connections()
    except (AttributeError, KeyError, RuntimeError):
        # 连接不存在或已关闭，忽略（测试环境可能已经关闭）
        pass

