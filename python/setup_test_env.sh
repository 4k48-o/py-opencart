#!/bin/bash
# 测试环境快速配置脚本

echo "=========================================="
echo "OpenCart FastAPI 测试环境配置"
echo "=========================================="
echo ""

# 检查是否已存在 .env.test
if [ -f ".env.test" ]; then
    echo "⚠️  .env.test 文件已存在"
    read -p "是否要覆盖? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消"
        exit 0
    fi
fi

# 创建 .env.test 文件
cat > .env.test << 'ENVEOF'
# 测试环境配置
# 请填写数据库组提供的实际配置信息

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=opencart
DB_PREFIX=oc_

# 应用配置
DEBUG=True
SECRET_KEY=test-secret-key-for-testing-only-minimum-32-characters
ENVEOF

echo "✅ 已创建 .env.test 文件"
echo ""
echo "📝 请编辑 .env.test 文件，填写数据库组提供的配置信息："
echo "   - DB_PASSWORD: 数据库密码（必须填写）"
echo "   - 其他配置项根据实际情况调整"
echo ""
echo "🔍 配置完成后，运行以下命令验证连接："
echo "   make test-db"
echo "   或"
echo "   python scripts/test_db_connection.py"
echo ""
