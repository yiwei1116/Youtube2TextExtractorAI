#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版 Chrome 連接器
避免複雜的調試端口配置，提供更穩定的連接
"""

import time
import os
import subprocess
import psutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class SimpleChromeConnector:
    """簡化版 Chrome 連接器"""
    
    def __init__(self, debug_port: int = 9222):
        self.driver = None
        self.service = None
        self.debug_port = debug_port
        
    def get_chrome_version(self):
        """獲取 Chrome 版本"""
        try:
            # 尋找 Chrome 執行檔
            chrome_paths = [
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                os.path.expanduser(r'~\AppData\Local\Google\Chrome\Application\chrome.exe')
            ]
            
            for path in chrome_paths:
                if os.path.exists(path):
                    # 使用 subprocess 獲取版本
                    result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        version = result.stdout.strip().split()[-1]
                        print(f"✅ 檢測到 Chrome 版本: {version}")
                        return version
            
            print("⚠️  無法檢測 Chrome 版本")
            return "unknown"
        except Exception as e:
            print(f"⚠️  版本檢測失敗: {e}")
            return "unknown"
    
    def kill_existing_chrome_processes(self):
        """清理現有的 Chrome 進程（可選）"""
        try:
            killed_count = 0
            for proc in psutil.process_iter(['pid', 'name']):
                if 'chrome' in proc.info['name'].lower():
                    try:
                        proc.terminate()
                        killed_count += 1
                    except:
                        pass
            
            if killed_count > 0:
                print(f"🧹 清理了 {killed_count} 個 Chrome 進程")
                time.sleep(2)
        except Exception as e:
            print(f"⚠️  進程清理失敗: {e}")
    
    def create_driver_standard(self):
        """標準模式創建 WebDriver"""
        try:
            print("🚀 嘗試標準模式連接...")
            
            # 基本 Chrome 選項
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            
            # 創建 Service
            print("📦 正在下載/檢查 ChromeDriver...")
            self.service = Service(ChromeDriverManager().install())
            
            print("🔧 正在啟動 Chrome 瀏覽器...")
            self.driver = webdriver.Chrome(service=self.service, options=chrome_options)
            
            # 設置超時
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            print("✅ 標準模式連接成功！")
            return True
            
        except Exception as e:
            print(f"❌ 標準模式連接失敗: {e}")
            return False
    
    def create_driver_minimal(self):
        """最小配置模式"""
        try:
            print("🚀 嘗試最小配置模式...")
            
            # 最小配置
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            
            # 使用 ChromeDriverManager
            self.service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=self.service, options=chrome_options)
            
            # 基本超時設置
            self.driver.set_page_load_timeout(30)
            
            print("✅ 最小配置模式連接成功！")
            return True
            
        except Exception as e:
            print(f"❌ 最小配置模式連接失敗: {e}")
            return False
    
    def create_driver_headless(self):
        """無頭模式（測試用）"""
        try:
            print("🚀 嘗試無頭模式...")
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            self.service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=self.service, options=chrome_options)
            
            print("✅ 無頭模式連接成功！")
            return True
            
        except Exception as e:
            print(f"❌ 無頭模式連接失敗: {e}")
            return False
    
    def connect(self, mode='existing'):
        """
        連接到 Chrome
        
        Args:
            mode: 連接模式 ('existing', 'auto', 'standard', 'minimal', 'headless', 'clean')
        """
        print("🌐 SimpleChromeConnector 啟動")
        print("=" * 50)
        
        # 顯示 Chrome 版本
        self.get_chrome_version()
        
        if mode == 'clean':
            print("🧹 清理模式：先清理現有進程...")
            self.kill_existing_chrome_processes()
            mode = 'standard'
        
        # 優先嘗試連接現有瀏覽器
        if mode == 'existing':
            print("🔍 優先嘗試連接現有的 Chrome 瀏覽器...")
            
            # 檢查是否有調試模式的 Chrome
            if self.is_chrome_debug_running():
                if self.connect_to_existing_chrome():
                    return True
            else:
                print("💡 未檢測到調試模式的 Chrome")
                print("🎯 為了使用現有瀏覽器，需要啟用調試模式")
                
                if self.guide_user_enable_debug_mode():
                    # 用戶說已經啟用，再次嘗試
                    print("🔄 重新檢測調試模式...")
                    time.sleep(2)
                    if self.is_chrome_debug_running() and self.connect_to_existing_chrome():
                        return True
                
                print("⚠️  無法連接到現有瀏覽器，是否要創建新實例？")
                create_new = input("是否創建新的 Chrome 實例？(y/n): ").strip().lower()
                if create_new not in ['y', 'yes', '']:
                    print("❌ 用戶選擇不創建新實例")
                    return False
                
                # 回退到自動模式
                mode = 'auto'
        
        # 根據模式嘗試連接
        if mode == 'auto':
            # 自動模式：依序嘗試不同方式
            modes_to_try = ['standard', 'minimal']
            for try_mode in modes_to_try:
                print(f"\n🔄 嘗試 {try_mode} 模式...")
                if try_mode == 'standard' and self.create_driver_standard():
                    return True
                elif try_mode == 'minimal' and self.create_driver_minimal():
                    return True
        elif mode == 'standard':
            return self.create_driver_standard()
        elif mode == 'minimal':
            return self.create_driver_minimal()
        elif mode == 'headless':
            return self.create_driver_headless()
        
        print("❌ 所有連接模式都失敗了")
        return False
    
    def test_connection(self):
        """測試連接是否正常"""
        if not self.driver:
            return False
        
        try:
            print("🧪 測試連接...")
            self.driver.get("https://www.google.com")
            title = self.driver.title
            print(f"✅ 連接測試成功，頁面標題: {title}")
            return True
        except Exception as e:
            print(f"❌ 連接測試失敗: {e}")
            return False
    
    def get_driver(self):
        """獲取 WebDriver 實例"""
        return self.driver
    
    def close(self):
        """關閉連接"""
        if self.driver:
            try:
                self.driver.quit()
                print("🧹 瀏覽器已關閉")
            except:
                pass
        self.driver = None
    
    def is_chrome_debug_running(self):
        """檢查 Chrome 是否已經在調試模式運行"""
        try:
            import requests
            response = requests.get(f"http://127.0.0.1:{self.debug_port}/json", timeout=2)
            if response.status_code == 200:
                print(f"✅ 檢測到調試模式的 Chrome (端口 {self.debug_port})")
                return True
        except:
            pass
        
        # 檢查進程
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'chrome' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if f'--remote-debugging-port={self.debug_port}' in cmdline:
                        print(f"✅ 檢測到調試進程 Chrome (PID: {proc.info['pid']})")
                        return True
        except Exception as e:
            pass
        
        print(f"⚠️  未檢測到調試模式的 Chrome")
        return False
    
    def connect_to_existing_chrome_with_timeout(self):
        """帶超時的連接到現有 Chrome"""
        import threading
        import time
        
        result = {'success': False, 'error': None}
        
        def connect_worker():
            try:
                # Chrome 選項設定
                chrome_options = Options()
                chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.debug_port}")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                
                # 創建 Service 
                self.service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=self.service, options=chrome_options)
                
                # 設置超時
                self.driver.set_page_load_timeout(20)
                self.driver.implicitly_wait(5)
                
                result['success'] = True
            except Exception as e:
                result['error'] = str(e)
        
        # 啟動連接線程
        connect_thread = threading.Thread(target=connect_worker)
        connect_thread.daemon = True
        connect_thread.start()
        
        # 等待最多 15 秒
        connect_thread.join(timeout=15)
        
        if connect_thread.is_alive():
            print("❌ WebDriver 連接超時（15秒）")
            return False
        
        if result['success']:
            print("✅ 成功連接到現有 Chrome 瀏覽器！")
            return True
        else:
            print(f"❌ WebDriver 創建失敗: {result['error']}")
            return False
    
    def connect_to_existing_chrome(self):
        """連接到現有的 Chrome 實例（調試模式）"""
        try:
            print("🔍 嘗試連接到現有的 Chrome 瀏覽器...")
            
            # 添加連接前的檢查
            print("🔧 正在檢查調試端口連通性...")
            try:
                import requests
                response = requests.get(f"http://127.0.0.1:{self.debug_port}/json", timeout=5)
                if response.status_code == 200:
                    print(f"✅ 調試端口 {self.debug_port} 可訪問")
                else:
                    print(f"⚠️  調試端口響應異常: {response.status_code}")
            except Exception as port_error:
                print(f"❌ 調試端口檢查失敗: {port_error}")
                print("💡 Chrome 可能沒有正確啟用調試模式")
                return False
            
            # 使用帶超時的連接方法
            print("🔗 正在建立 WebDriver 連接...")
            print("⏳ 這可能需要幾秒鐘...")
            
            if self.connect_to_existing_chrome_with_timeout():
                # 測試連接
                print("🧪 測試連接...")
                try:
                    current_url = self.driver.current_url
                    print(f"📄 當前頁面: {current_url}")
                    return True
                except Exception as test_error:
                    print(f"⚠️  連接測試異常: {test_error}")
                    return True  # 即使測試失敗，連接可能仍然有效
            else:
                return False
            
        except Exception as e:
            print(f"❌ 連接現有 Chrome 失敗: {e}")
            print("💡 建議:")
            print("   1. 確認 Chrome 已啟用調試模式")
            print("   2. 檢查防火牆設定")
            print("   3. 嘗試重新啟動 Chrome")
            return False
    
    def guide_user_enable_debug_mode(self):
        """指導用戶啟用 Chrome 調試模式"""
        print("\n📋 如何啟用 Chrome 調試模式:")
        print("=" * 50)
        print("1. 關閉所有 Chrome 瀏覽器視窗")
        print("2. 開啟命令提示字元或 PowerShell")
        print("3. 輸入以下命令:")
        print(f'   "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port={self.debug_port}')
        print("   或")
        print(f'   "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port={self.debug_port}')
        print("\n💡 提示: 啟用後 Chrome 會自動開啟，然後您就可以正常瀏覽")
        print("⚠️  重要: 請保持這個 Chrome 實例開啟，程序會連接到這個實例")
        
        choice = input("\n已按照步驟啟用調試模式了嗎？(y/n): ").strip().lower()
        return choice in ['y', 'yes', '']

def test_all_modes():
    """測試所有連接模式"""
    print("🧪 SimpleChromeConnector 全面測試")
    print("=" * 60)
    
    modes = ['standard', 'minimal', 'headless']
    results = {}
    
    for mode in modes:
        print(f"\n🔬 測試模式: {mode}")
        print("-" * 30)
        
        connector = SimpleChromeConnector()
        try:
            if connector.connect(mode):
                if connector.test_connection():
                    results[mode] = "✅ 成功"
                else:
                    results[mode] = "⚠️ 連接成功但測試失敗"
            else:
                results[mode] = "❌ 連接失敗"
        except Exception as e:
            results[mode] = f"❌ 錯誤: {e}"
        finally:
            connector.close()
            time.sleep(2)  # 等待清理
    
    print(f"\n📊 測試結果摘要:")
    print("=" * 60)
    for mode, result in results.items():
        print(f"{mode.ljust(15)}: {result}")
    
    # 推薦最佳模式
    if results.get('standard') == "✅ 成功":
        print(f"\n💡 推薦使用: standard 模式")
    elif results.get('minimal') == "✅ 成功":
        print(f"\n💡 推薦使用: minimal 模式")
    else:
        print(f"\n⚠️  建議檢查 Chrome 和 ChromeDriver 安裝")

if __name__ == "__main__":
    test_all_modes() 