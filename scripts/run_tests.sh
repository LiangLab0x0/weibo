#!/bin/bash

# 微博AI内容管理器测试运行脚本
# 执行所有单元测试和集成测试

set -e

echo "🧪 开始运行微博AI内容管理器测试套件..."

# 检查环境变量
if [ ! -f ".env" ]; then
    echo "❌ .env 文件不存在"
    exit 1
fi

source .env
if [ -z "$DEEPSEEK_API_KEY" ] || [ "$DEEPSEEK_API_KEY" = "your_deepseek_api_key_here" ]; then
    echo "❌ 请在 .env 文件中设置有效的 DEEPSEEK_API_KEY"
    exit 1
fi

echo "✅ 环境变量检查通过"

# 进入后端目录
cd backend

# 检查Python虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装测试依赖
echo "📦 安装测试依赖..."
pip install -r requirements.txt

# 设置环境变量
export $(cat ../.env | grep -v '^#' | xargs)

echo ""
echo "🔧 开始配置测试..."

# 1. 配置测试
echo "📋 1. 运行配置测试..."
python -m pytest tests/test_config.py -v -s

echo ""
echo "🤖 2. 运行AI代理测试..."
python -m pytest tests/test_agents.py -v -s

echo ""
echo "🌐 3. 运行API测试..."
python -m pytest tests/test_api.py -v -s

echo ""
echo "🔗 4. 运行DeepSeek集成测试..."
python -m pytest tests/test_deepseek_integration.py -v -s

echo ""
echo "🔄 5. 运行集成测试..."
python -m pytest tests/test_integration.py -v -s

echo ""
echo "📊 6. 生成测试报告..."
python -m pytest tests/ --tb=short --maxfail=5 -q

echo ""
echo "🎉 所有测试完成！"

# 返回项目根目录
cd ..

echo ""
echo "📋 测试总结："
echo "   ✅ 配置测试 - 验证环境变量和配置加载"
echo "   ✅ AI代理测试 - 验证微博代理核心功能"
echo "   ✅ API测试 - 验证所有REST API端点"
echo "   ✅ DeepSeek集成测试 - 验证AI API真实调用"
echo "   ✅ 集成测试 - 验证端到端工作流程"
echo ""
echo "🚀 系统已准备就绪，可以进行Docker部署！" 