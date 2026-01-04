"""
Tortoise ORM database configuration
"""
import json
import traceback
from tortoise import Tortoise
from app.config import settings

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
    """Initialize database connection"""
    # #region agent log
    _log_debug('debug-session', 'post-fix', 'A', 'database.py:init_db', 'init_db called', {'db_name': settings.db_name, 'db_host': settings.db_host})
    # #endregion agent log
    
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
    await Tortoise.close_connections()

