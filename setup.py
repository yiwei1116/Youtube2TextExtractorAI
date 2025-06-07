#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube 文字分析器 - 安裝設置
簡化版本，專注於文字提取功能
"""

import subprocess
import sys
import os

def install_requirements():
    """安裝必要套件"""
    print("🔧 YouTube 文字分析器 - 安裝設置")
    print("="*50)
    
    requirements_file = "requirements.txt"
    
    if not os.path.exists(requirements_file):
        print(f"❌ 找不到 {requirements_file} 檔案")
        return False
    
    try:
        print(f"📦 正在安裝套件...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", requirements_file
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 套件安裝成功！")
            return True
        else:
            print(f"❌ 套件安裝失敗:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 安裝過程中發生錯誤: {e}")
        return False

def check_python_version():
    """檢查 Python 版本"""
    print("🐍 檢查 Python 版本...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 7:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} (支援)")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (需要 Python 3.7+)")
        return False

def test_imports():
    """測試套件導入"""
    print("🧪 測試套件導入...")
    
    test_packages = [
        ('youtube_transcript_api', 'YouTubeTranscriptApi'),
        ('googleapiclient.discovery', 'build'),
        ('requests', 'requests'),
        ('pyperclip', 'pyperclip')
    ]
    
    success = True
    for package, module in test_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - 導入失敗")
            success = False
    
    return success

def create_output_directory():
    """創建輸出目錄"""
    print("📁 創建輸出目錄...")
    
    directories = ['ai_ready_files']
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ {directory}")
        except Exception as e:
            print(f"❌ 創建目錄 {directory} 失敗: {e}")
            return False
    
    return True

def main():
    """主安裝程序"""
    print("🎥 YouTube 文字分析器 - 安裝程序")
    print("🎯 專注於 YouTube 文字提取 + 分析 Prompt 生成")
    print("="*60)
    
    # 檢查 Python 版本
    if not check_python_version():
        print("\n❌ Python 版本不符合要求")
        input("按 Enter 鍵退出...")
        return
    
    # 安裝套件
    if not install_requirements():
        print("\n❌ 套件安裝失敗")
        input("按 Enter 鍵退出...")
        return
    
    # 測試導入
    if not test_imports():
        print("\n❌ 套件測試失敗")
        input("按 Enter 鍵退出...")
        return
    
    # 創建目錄
    if not create_output_directory():
        print("\n❌ 目錄創建失敗")
        input("按 Enter 鍵退出...")
        return
    
    # 完成
    print("\n🎉 安裝完成！")
    print("="*40)
    print("📋 下一步:")
    print("1. 運行: python youtube_text_analyzer.py")
    print("2. 輸入 YouTube 影片 URL")
    print("3. 選擇分析類型")
    print("4. 獲得 AI 分析檔案")
    print()
    print("💡 檔案會保存在 ai_ready_files 資料夾中")
    print("   您可以直接複製內容到 AI 網站使用")
    
    input("\n按 Enter 鍵退出...")

if __name__ == "__main__":
    main() 