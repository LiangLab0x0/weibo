#!/bin/bash

# 微博AI内容管理器部署脚本
# 用于快速部署和启动整个应用

set -e

echo "🚀 开始部署微博AI内容管理器..."

# 检查Docker和Docker Compose是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "📝 创建环境变量文件..."
    cp env.example .env
    echo "⚠️  请编辑 .env 文件，设置必要的配置（特别是DEEPSEEK_API_KEY和SECRET_KEY）"
    echo "⚠️  设置完成后请重新运行此脚本"
    exit 1
fi

# 检查必要的环境变量
source .env
if [ -z "$DEEPSEEK_API_KEY" ] || [ "$DEEPSEEK_API_KEY" = "your_deepseek_api_key_here" ]; then
    echo "❌ 请在 .env 文件中设置有效的 DEEPSEEK_API_KEY"
    exit 1
fi

if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your_secret_key_here" ]; then
    echo "❌ 请在 .env 文件中设置有效的 SECRET_KEY"
    exit 1
fi

echo "✅ 环境变量检查通过"

# 停止现有容器
echo "🛑 停止现有容器..."
docker-compose down --remove-orphans

# 构建镜像
echo "🔨 构建Docker镜像..."
docker-compose build --no-cache

# 安装Playwright浏览器（在后端容器中）
echo "🌐 安装Playwright浏览器..."
docker-compose run --rm backend playwright install chromium --with-deps

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败"
    docker-compose logs backend
    exit 1
fi

if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端服务启动成功"
else
    echo "❌ 前端服务启动失败"
    docker-compose logs frontend
    exit 1
fi

echo ""
echo "🎉 部署完成！"
echo ""
echo "📱 访问地址："
echo "   前端界面: http://localhost:3000"
echo "   API文档:  http://localhost:8000/docs"
echo "   任务监控: http://localhost:5555"
echo ""
echo "📋 管理命令："
echo "   查看日志: docker-compose logs -f"
echo "   停止服务: docker-compose down"
echo "   重启服务: docker-compose restart"
echo ""
echo "⚠️  使用提示："
echo "   1. 首次使用请先在前端登录微博账号"
echo "   2. 建议使用小号进行测试"
echo "   3. 请遵守微博平台的使用规则"
echo "" 