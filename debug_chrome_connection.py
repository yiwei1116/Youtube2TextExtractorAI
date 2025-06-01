#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome 連接診斷工具
幫助診斷和解決 Chrome 調試模式連接問題
"""

import time
import requests
import psutil
import subprocess
import os
from simple_chrome_connector import SimpleChromeConnector

def check_chrome_processes():
    """檢查 Chrome 進程"""
    print("🔍 檢查 Chrome 進程...")
    chrome_processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if 'chrome' in proc.info['name'].lower():
                chrome_processes.append(proc.info)
        
        if chrome_processes:
            print(f"✅ 找到 {len(chrome_processes)} 個 Chrome 進程:")
            for proc in chrome_processes[:5]:  # 只顯示前5個
                cmdline = ' '.join(proc['cmdline']) if proc['cmdline'] else 'N/A'
                has_debug = '--remote-debugging-port=' in cmdline
                debug_indicator = "🔧 [調試模式]" if has_debug else ""
                print(f"   PID: {proc['pid']} {debug_indicator}")
                if has_debug:
                    print(f"      指令: {cmdline[:100]}...")
        else:
            print("❌ 未找到 Chrome 進程")
    except Exception as e:
        print(f"❌ 檢查進程時出錯: {e}")
    
    return chrome_processes

def check_debug_port(port=9222):
    """檢查調試端口"""
    print(f"\n🔧 檢查調試端口 {port}...")
    
    try:
        response = requests.get(f"http://127.0.0.1:{port}/json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 調試端口 {port} 可訪問")
            print(f"📊 發現 {len(data)} 個標籤頁")
            for i, tab in enumerate(data[:3]):  # 顯示前3個標籤頁
                title = tab.get('title', 'N/A')[:50]
                url = tab.get('url', 'N/A')[:50]
                print(f"   標籤 {i+1}: {title} - {url}")
            return True
        else:
            print(f"⚠️  調試端口響應異常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ 無法連接到調試端口 {port}")
        print("💡 Chrome 可能沒有啟用調試模式")
        return False
    except Exception as e:
        print(f"❌ 檢查調試端口時出錯: {e}")
        return False

def force_kill_chrome():
    """強制關閉所有 Chrome 進程"""
    print("\n🧹 強制關閉所有 Chrome 進程...")
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(['taskkill', '/f', '/im', 'chrome.exe'], 
                         capture_output=True, text=True)
        else:  # Unix-like
            subprocess.run(['pkill', '-f', 'chrome'], 
                         capture_output=True, text=True)
        
        time.sleep(2)
        print("✅ Chrome 進程已清理")
    except Exception as e:
        print(f"❌ 清理進程時出錯: {e}")

def start_debug_chrome():
    """啟動調試模式的 Chrome"""
    print("\n🚀 啟動調試模式的 Chrome...")
    
    chrome_paths = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        os.path.expanduser(r'~\AppData\Local\Google\Chrome\Application\chrome.exe')
    ]
    
    chrome_path = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_path = path
            break
    
    if not chrome_path:
        print("❌ 找不到 Chrome 安裝路徑")
        return False
    
    try:
        cmd = [chrome_path, '--remote-debugging-port=9222', '--user-data-dir=chrome_debug_profile']
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Chrome 調試模式已啟動")
        
        # 等待啟動
        print("⏳ 等待 Chrome 啟動...")
        time.sleep(5)
        
        return check_debug_port()
    except Exception as e:
        print(f"❌ 啟動 Chrome 失敗: {e}")
        return False

def test_webdriver_connection():
    """測試 WebDriver 連接"""
    print("\n🧪 測試 WebDriver 連接...")
    
    connector = SimpleChromeConnector()
    try:
        if connector.connect_to_existing_chrome():
            print("✅ WebDriver 連接成功")
            
            # 測試基本功能
            driver = connector.get_driver()
            try:
                current_url = driver.current_url
                print(f"📄 當前頁面: {current_url}")
                
                # 嘗試導航
                driver.get("https://www.google.com")
                title = driver.title
                print(f"📄 測試頁面標題: {title}")
                
                print("✅ WebDriver 功能正常")
                return True
            except Exception as nav_error:
                print(f"⚠️  導航測試失敗: {nav_error}")
                return False
        else:
            print("❌ WebDriver 連接失敗")
            return False
    except Exception as e:
        print(f"❌ WebDriver 測試出錯: {e}")
        return False
    finally:
        try:
            connector.close()
        except:
            pass

def main():
    """主診斷流程"""
    print("🔧 Chrome 連接診斷工具")
    print("=" * 50)
    
    # 步驟 1: 檢查現有進程
    chrome_procs = check_chrome_processes()
    
    # 步驟 2: 檢查調試端口
    debug_available = check_debug_port()
    
    # 步驟 3: 根據結果決定下一步
    if debug_available:
        print("\n🎯 調試端口可用，嘗試 WebDriver 連接...")
        if test_webdriver_connection():
            print("\n🎉 診斷完成 - 連接正常！")
            print("💡 您可以運行 python youtube_text_2_AI.py")
            return
        else:
            print("\n⚠️  調試端口可用但 WebDriver 連接失敗")
    
    # 步驟 4: 嘗試修復
    print("\n🔄 嘗試修復連接問題...")
    
    choice = input("是否要重新啟動 Chrome 調試模式？(y/n): ").strip().lower()
    if choice in ['y', 'yes', '']:
        force_kill_chrome()
        
        if start_debug_chrome():
            print("\n🧪 重新測試 WebDriver 連接...")
            if test_webdriver_connection():
                print("\n🎉 修復成功！")
                print("💡 您可以運行 python youtube_text_2_AI.py")
            else:
                print("\n❌ 修復失敗")
                print("💡 建議檢查防火牆設定或嘗試重新安裝 Chrome")
        else:
            print("\n❌ 無法啟動調試模式的 Chrome")
    else:
        print("\n💡 診斷完成，請手動檢查 Chrome 設定")

if __name__ == "__main__":
    main() 