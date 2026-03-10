@echo off

rem 安装依赖
echo Installing dependencies...
cd backend && pip install -r requirements.txt && cd ..

rem 启动后端服务
echo Starting backend service...
start "Backend Service" cmd /k "cd /d %~dp0\backend && python -m uvicorn app:app --reload"

rem 等待2秒，确保后端服务有足够时间启动
echo Waiting for backend service to start...
ping 127.0.0.1 -n 3 > nul

rem 启动前端服务
echo Starting frontend service...
start "Frontend Service" cmd /k "cd /d %~dp0\frontend && python -m http.server 3000"

echo Service startup completed!
echo Backend API: http://localhost:8000
echo Frontend: http://localhost:3000
echo Press any key to close this window...
pause