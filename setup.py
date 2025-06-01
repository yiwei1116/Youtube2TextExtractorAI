#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube to AI 系統安裝腳本
"""

import os
import sys
import subprocess

def install_requirements():
    """安裝必要套件"""
    print("🔧 正在安裝必要套件...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ 套件安裝完成！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 套件安裝失敗: {e}")
        return False

def create_directories():
    """創建必要目錄"""
    print("📁 正在創建目錄...")
    
    directories = ["ai_uploads", "logs"]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ 創建目錄: {directory}")
        else:
            print(f"📁 目錄已存在: {directory}")

def check_chrome():
    """檢查 Chrome 瀏覽器"""
    print("🌐 正在檢查 Chrome 瀏覽器...")
    
    import platform
    system = platform.system()
    
    chrome_paths = {
        'Windows': [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
        ],
        'Darwin': [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        ],
        'Linux': [
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable'
        ]
    }
    
    found_chrome = False
    for path in chrome_paths.get(system, []):
        if os.path.exists(path):
            print(f"✅ 找到 Chrome: {path}")
            found_chrome = True
            break
    
    if not found_chrome:
        print("⚠️  未找到 Chrome 瀏覽器，請先安裝 Google Chrome")
        return False
    
    return True

def run_test():
    """運行快速測試"""
    print("🧪 是否要運行快速測試？")
    choice = input("輸入 'y' 運行測試，或按 Enter 跳過: ").strip().lower()
    
    if choice in ['y', 'yes']:
        try:
            subprocess.run([sys.executable, "quick_test.py"])
        except Exception as e:
            print(f"❌ 測試運行失敗: {e}")

def main():
    """主安裝程序"""
    print("🚀 YouTube to AI 系統安裝程序")
    print("=" * 50)
    
    steps = [
        ("安裝 Python 套件", install_requirements),
        ("創建必要目錄", create_directories),
        ("檢查 Chrome 瀏覽器", check_chrome)
    ]
    
    all_success = True
    
    for step_name, step_func in steps:
        print(f"\n📋 步驟: {step_name}")
        if not step_func():
            all_success = False
            print(f"❌ {step_name} 失敗")
        else:
            print(f"✅ {step_name} 完成")
    
    print("\n" + "=" * 50)
    
    if all_success:
        print("🎉 安裝完成！")
        print("\n📚 使用說明:")
        print("1. 運行主程序: python youtube_text_2_AI.py")
        print("2. 快速測試: python quick_test.py")
        print("3. 查看說明: 參考 README.md")
        
        run_test()
    else:
        print("⚠️  安裝過程中發生問題，請檢查錯誤信息")
        print("💡 可以嘗試手動安裝: pip install -r requirements.txt")

if __name__ == "__main__":
    main() 