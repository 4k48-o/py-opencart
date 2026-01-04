#!/usr/bin/env python3
"""
测试数据库连接脚本

用于验证测试数据库配置是否正确
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.conftest import get_test_db_config
from tortoise import Tortoise


async def test_connection():
    """测试数据库连接"""
    db_config = get_test_db_config()
    
    print("=" * 60)
    print("测试数据库连接")
    print("=" * 60)
    print(f"主机: {db_config['host']}")
    print(f"端口: {db_config['port']}")
    print(f"用户: {db_config['user']}")
    print(f"密码: {'已设置' if db_config['password'] else '未设置'}")
    print(f"数据库: {db_config['name']}")
    print("=" * 60)
    print()
    
    if not db_config['password']:
        print("⚠️  警告: 数据库密码未设置")
        print("请创建 .env.test 文件并设置 DB_PASSWORD")
        print("或设置环境变量: export DB_PASSWORD=your_password")
        print()
        return False
    
    # 构建连接URL
    if db_config['password']:
        db_url = f"mysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['name']}"
    else:
        db_url = f"mysql://{db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['name']}"
    
    try:
        print("正在连接数据库...")
        await Tortoise.init(
            db_url=db_url,
            modules={"models": ["app.models.system"]},
        )
        
        # 尝试执行一个简单查询
        connection = Tortoise.get_connection("default")
        result = await connection.execute_query("SELECT 1 as test")
        
        print("✅ 数据库连接成功！")
        print(f"   查询结果: {result}")
        
        await Tortoise.close_connections()
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print()
        print("请检查:")
        print("1. MySQL 服务是否正在运行")
        print("2. 数据库连接信息是否正确")
        print("3. 测试数据库是否存在: CREATE DATABASE IF NOT EXISTS opencart_test;")
        print("4. 数据库用户是否有足够的权限")
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

