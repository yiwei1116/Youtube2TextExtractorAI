@echo off
echo ======================================
echo Chrome 調試模式啟動器
echo ======================================
echo.
echo 正在關閉現有的 Chrome 進程...
taskkill /f /im chrome.exe >nul 2>&1
timeout /t 2 >nul

echo 正在啟動調試模式的 Chrome...
echo.

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo 使用 64 位 Chrome
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    echo 使用 32 位 Chrome
    start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
) else (
    echo 找不到 Chrome 安裝路徑！
    echo 請手動執行以下命令：
    echo "Chrome路徑\chrome.exe" --remote-debugging-port=9222
    pause
    exit /b 1
)

echo.
echo ✅ Chrome 調試模式已啟動！
echo 💡 現在可以運行 python youtube_text_2_AI.py
echo ⚠️  請保持這個 Chrome 視窗開啟
echo.
pause 