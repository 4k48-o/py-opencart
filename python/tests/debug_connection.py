"""
调试脚本：验证数据库连接和环境变量
"""
import asyncio
import os
from tortoise import Tortoise
from app.config import settings

async def test_connection():
    """测试连接状态"""
    print("=" * 60)
    print("数据库连接调试")
    print("=" * 60)
    
    # 检查环境变量
    print(f"\n环境变量检查:")
    print(f"  TESTING: {os.getenv('TESTING')}")
    print(f"  PYTEST_CURRENT_TEST: {os.getenv('PYTEST_CURRENT_TEST')}")
    print(f"  PYTEST: {os.getenv('PYTEST')}")
    
    # 检查Tortoise是否已初始化
    print(f"\nTortoise ORM状态:")
    try:
        connection = Tortoise.get_connection("default")
        print(f"  ✅ 连接已存在")
        print(f"  连接ID: {id(connection)}")
        print(f"  连接类型: {type(connection)}")
        if hasattr(connection, 'pool'):
            print(f"  连接池: {connection.pool}")
        if hasattr(connection, 'db_url'):
            print(f"  数据库URL: {connection.db_url}")
    except KeyError:
        print(f"  ❌ 连接不存在（未初始化）")
    except Exception as e:
        print(f"  ❌ 错误: {type(e).__name__}: {str(e)}")
    
    # 检查settings配置
    print(f"\nSettings配置:")
    print(f"  DB_NAME: {settings.db_name}")
    print(f"  DB_HOST: {settings.db_host}")
    print(f"  DB_PORT: {settings.db_port}")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_connection())

