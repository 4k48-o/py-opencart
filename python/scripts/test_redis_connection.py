#!/usr/bin/env python3
"""
测试Redis连接脚本

用于验证测试环境的Redis配置是否正确
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.conftest import get_test_redis_config
from app.core.redis_client import get_redis_client, close_redis_client


async def test_connection():
    """测试Redis连接"""
    redis_config = get_test_redis_config()
    
    print("=" * 60)
    print("测试Redis连接")
    print("=" * 60)
    print(f"主机: {redis_config['host']}")
    print(f"端口: {redis_config['port']}")
    print(f"数据库: {redis_config['db']}")
    print(f"密码: {'已设置' if redis_config['password'] else '未设置'}")
    print("=" * 60)
    print()
    
    # 设置环境变量
    import os
    original_env = {}
    for key in ["REDIS_HOST", "REDIS_PORT", "REDIS_PASSWORD", "REDIS_DB"]:
        original_env[key] = os.getenv(key)
    
    os.environ["REDIS_HOST"] = redis_config["host"]
    os.environ["REDIS_PORT"] = str(redis_config["port"])
    if redis_config["password"]:
        os.environ["REDIS_PASSWORD"] = redis_config["password"]
    else:
        os.environ.pop("REDIS_PASSWORD", None)
    os.environ["REDIS_DB"] = str(redis_config["db"])
    
    # 重新加载配置
    from importlib import reload
    import app.config
    reload(app.config)
    
    try:
        print("正在连接Redis...")
        # 直接使用配置构建连接
        import redis.asyncio as aioredis
        if redis_config["password"]:
            redis_url = f"redis://:{redis_config['password']}@{redis_config['host']}:{redis_config['port']}/{redis_config['db']}"
        else:
            redis_url = f"redis://{redis_config['host']}:{redis_config['port']}/{redis_config['db']}"
        
        client = aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        
        # 测试基本操作
        await client.set("test_key", "test_value")
        value = await client.get("test_key")
        assert value == "test_value", f"期望 'test_value'，实际 '{value}'"
        
        # 清理测试数据
        await client.delete("test_key")
        
        print("✅ Redis连接成功！")
        print("   基本操作测试通过")
        
        await client.aclose()
        return True
        
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        print()
        print("请检查:")
        print("1. Redis 服务是否正在运行")
        print("2. Redis 连接信息是否正确")
        print("3. Redis 密码是否正确")
        print("4. 网络连接是否正常")
        return False


def main():
    """主函数"""
    try:
        result = asyncio.run(test_connection())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
