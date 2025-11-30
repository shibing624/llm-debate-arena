#!/bin/bash

echo "🚀 Starting LLM Debate Arena..."

# 检查是否存在虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装后端依赖
if [ ! -f "backend/requirements.txt" ]; then
    echo "❌ backend/requirements.txt not found!"
    exit 1
fi

echo "📦 Installing backend dependencies..."
pip install -r backend/requirements.txt -q

# 检查环境变量
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found, copying from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and fill in your API keys!"
fi

# 启动后端
echo "🔧 Starting backend server..."
python -m uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# 启动前端
echo "🎨 Starting frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ LLM Debate Arena started successfully!"
echo ""
echo "📍 Backend:  http://localhost:8000"
echo "📍 Frontend: http://localhost:3000"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# 清理函数
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# 捕获 Ctrl+C
trap cleanup INT

# 等待
wait
