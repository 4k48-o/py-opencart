"""
临时调试脚本：检查数据库连接状态
"""
import pytest
import asyncio
from tortoise import Tortoise
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_connection_debug(db_setup, db_transaction):
    """调试：检查连接状态"""
    # 获取测试连接
    test_connection = Tortoise.get_connection("default")
    print(f"\n测试连接ID: {id(test_connection)}")
    print(f"测试连接类型: {type(test_connection)}")
    
    # 创建API客户端
    from app.main import app
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 触发startup事件（通过第一次请求）
        response = await ac.get("/api/v1/manufacturers/", headers={"Authorization": "Bearer test"})
        
        # 获取API使用的连接
        api_connection = Tortoise.get_connection("default")
        print(f"API连接ID: {id(api_connection)}")
        print(f"API连接类型: {type(api_connection)}")
        
        # 检查是否是同一个连接
        if id(test_connection) == id(api_connection):
            print("✅ 使用同一个连接")
        else:
            print("❌ 使用了不同的连接")
            
        # 检查环境变量
        import os
        print(f"\n环境变量:")
        print(f"  TESTING: {os.getenv('TESTING')}")
        print(f"  PYTEST: {os.getenv('PYTEST')}")
        print(f"  PYTEST_CURRENT_TEST: {os.getenv('PYTEST_CURRENT_TEST')}")

