#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強版自動發送 Transcript 到 AI 網站
優先使用文件上傳功能，提高效率和穩定性
"""

import time
import os
import json
from typing import Dict, List, Optional
from pathlib import Path
import platform
import subprocess
import psutil

# 需要安裝的套件：
# pip install selenium webdriver-manager psutil

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    import psutil
    from simple_chrome_connector import SimpleChromeConnector
except ImportError as e:
    print(f"請安裝必要套件: pip install selenium webdriver-manager psutil")
    print(f"錯誤詳情: {e}")
    exit(1)

class EnhancedAIWebSender:
    """增強版自動發送內容到 AI 網站的類別 - 支持文件上傳"""
    
    def __init__(self, wait_time: int = 5):
        """
        初始化
        
        Args:
            wait_time: 等待時間（秒）
        """
        self.wait_time = wait_time
        self.auto_delete_files = True  # 強制啟用自動刪除
        self.chrome_connector = SimpleChromeConnector()
        self.driver = None
        self.ai_configs = self._load_ai_configs()
        
        # 用於追蹤處理狀態的變數
        self.processed_files = set()
        self.current_file_path = None
        
    def _load_ai_configs(self) -> Dict:
        """載入 AI 網站設定 - 支持文件上傳"""
        return {
            'chatgpt': {
                'name': 'ChatGPT',
                'url': 'https://chat.openai.com/',
                'supports_file_upload': True,
                'file_upload_selectors': [
                    'input[type="file"]',
                    'button[aria-label*="Attach"]',
                    '[data-testid="attachment-button"]'
                ],
                'input_selectors': [
                    'textarea[data-testid="prompt-textarea"]',
                    'textarea[placeholder*="Message ChatGPT"]',
                    '#prompt-textarea',
                    '.text-base textarea'
                ],
                'send_button_selectors': [
                    'button[data-testid="send-button"]',
                    'button[aria-label*="Send"]',
                    '.send-button'
                ]
            },
            'claude': {
                'name': 'Claude (Anthropic)',
                'url': 'https://claude.ai/',
                'supports_file_upload': True,
                'file_upload_selectors': [
                    'input[type="file"]',
                    'button[aria-label*="Attach"]',
                    '[data-testid="file-upload"]',
                    '.attachment-button'
                ],
                'input_selectors': [
                    'div[contenteditable="true"]',
                    '[data-testid="chat-input"]',
                    '.ProseMirror'
                ],
                'send_button_selectors': [
                    'button[aria-label="Send Message"]',
                    'button[aria-label*="Send"]',
                    '.send-button'
                ]
            },
            'gemini': {
                'name': 'Google Gemini',
                'url': 'https://gemini.google.com/',
                'supports_file_upload': True,
                'file_upload_selectors': [
                    'input[type="file"]',
                    'button[aria-label*="upload"]',
                    '.upload-button'
                ],
                'input_selectors': [
                    'div[contenteditable="true"]',
                    '.ql-editor',
                    '[data-testid="input-area"]'
                ],
                'send_button_selectors': [
                    'button[aria-label="Send message"]',
                    'button[aria-label*="Send"]',
                    '.send-button'
                ]
            },
            'grok': {
                'name': 'Grok (X.AI)',
                'url': 'https://grok.x.ai/',
                'supports_file_upload': False,  # Grok 可能不支持文件上傳
                'input_selectors': [
                    'textarea[placeholder*="Ask Grok"]',
                    'textarea[data-testid="message-input"]',
                    'textarea[placeholder*="Message"]',
                    '.message-input textarea',
                    '[contenteditable="true"]'
                ],
                'send_button_selectors': [
                    'button[type="submit"]',
                    'button[data-testid="send-button"]',
                    'button[aria-label*="Send"]',
                    '.send-button'
                ]
            },
            'perplexity': {
                'name': 'Perplexity AI',
                'url': 'https://www.perplexity.ai/',
                'supports_file_upload': False,  # Perplexity 可能不支持文件上傳
                'input_selectors': [
                    'textarea[placeholder*="Ask anything"]',
                    'textarea[data-testid="search-input"]',
                    '.search-input textarea'
                ],
                'send_button_selectors': [
                    'button[aria-label*="Submit"]',
                    'button[type="submit"]',
                    '.submit-button'
                ]
            }
        }
    
    def setup_connection(self) -> bool:
        """建立與 Chrome 的連接"""
        print("🔧 正在建立瀏覽器連接...")
        print("🎯 優先嘗試連接現有的 Chrome 瀏覽器...")
        
        # 嘗試連接（默認使用現有瀏覽器模式）
        try:
            if self.chrome_connector.connect(mode='existing'):
                self.driver = self.chrome_connector.get_driver()
                print("✅ 瀏覽器連接成功 (現有瀏覽器)")
                return True
        except Exception as e:
            print(f"⚠️  現有瀏覽器連接失敗: {e}")
        
        # 回退到新瀏覽器模式
        print("🔄 回退到新瀏覽器模式...")
        try:
            if self.chrome_connector.connect(mode='auto'):
                self.driver = self.chrome_connector.get_driver()
                print("✅ 瀏覽器連接成功 (新瀏覽器)")
                return True
        except Exception as e:
            print(f"❌ 新瀏覽器連接也失敗: {e}")
        
        print("❌ 所有瀏覽器連接方式都失敗")
        print("💡 建議: 請檢查 Chrome 安裝或嘗試重新啟動系統")
        return False
    
    def find_file_upload_button(self, ai_name: str):
        """尋找文件上傳按鈕"""
        config = self.ai_configs.get(ai_name)
        if not config or not config.get('supports_file_upload'):
            return None
        
        print(f"🔍 正在尋找 {config['name']} 的文件上傳按鈕...")
        
        # 為 Claude 添加特殊處理
        if ai_name == 'claude':
            # Claude 可能需要更長時間載入
            time.sleep(3)
            
            # 嘗試多次尋找，因為 Claude 的界面可能需要時間載入
            for attempt in range(3):
                print(f"🔄 第 {attempt + 1} 次嘗試尋找 Claude 上傳按鈕...")
                
                # Claude 特有的選擇器
                claude_selectors = [
                    'input[type="file"]',
                    'button[aria-label*="attach"]',
                    'button[aria-label*="upload"]',
                    'button[title*="attach"]',
                    'button[title*="upload"]',
                    '[data-testid*="file"]',
                    '[data-testid*="upload"]',
                    '[data-testid*="attach"]',
                    '.attachment-button',
                    '.file-upload',
                    '.upload-button'
                ]
                
                for selector in claude_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_enabled() and element.is_displayed():
                                print(f"✅ 找到 Claude 文件上傳按鈕: {selector}")
                                return element
                    except Exception as e:
                        continue
                
                time.sleep(2)  # 等待後重試
            
            print("⚠️  Claude 文件上傳按鈕搜尋超時，可能需要手動操作")
            return None
        
        # 其他 AI 的標準處理
        time.sleep(2)
        
        # 嘗試所有可能的文件上傳選擇器
        for selector in config.get('file_upload_selectors', []):
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_enabled():
                        print(f"✅ 找到文件上傳按鈕: {selector}")
                        return element
            except Exception as e:
                continue
        
        # 嘗試尋找隱藏的 file input
        try:
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
            for file_input in file_inputs:
                print(f"✅ 找到文件輸入框")
                return file_input
        except Exception as e:
            pass
        
        print(f"❌ 未找到 {config['name']} 的文件上傳按鈕")
        return None
    
    def upload_file(self, ai_name: str, file_path: str) -> bool:
        """
        上傳文件到 AI 網站
        
        Args:
            ai_name: AI 名稱
            file_path: 文件路徑
            
        Returns:
            是否成功上傳
        """
        config = self.ai_configs.get(ai_name)
        if not config:
            print(f"❌ 不支援的 AI: {ai_name}")
            return False
        
        if not config.get('supports_file_upload'):
            print(f"⚠️  {config['name']} 不支援文件上傳，將使用文字輸入方式")
            return False
        
        try:
            print(f"📁 正在上傳文件到 {config['name']}: {file_path}")
            
            # 檢查文件是否存在
            if not os.path.exists(file_path):
                print(f"❌ 文件不存在: {file_path}")
                return False
            
            # 尋找文件上傳元素
            upload_element = self.find_file_upload_button(ai_name)
            if not upload_element:
                print(f"❌ 找不到 {config['name']} 的文件上傳按鈕")
                return False
            
            # 上傳文件
            absolute_path = os.path.abspath(file_path)
            upload_element.send_keys(absolute_path)
            
            print(f"✅ 文件已上傳到 {config['name']}")
            time.sleep(3)  # 等待文件處理
            
            return True
            
        except Exception as e:
            print(f"❌ 文件上傳到 {config['name']} 失敗: {e}")
            return False
    
    def find_input_element(self, ai_name: str):
        """尋找輸入框元素"""
        config = self.ai_configs.get(ai_name)
        if not config:
            return None
        
        # 等待頁面載入
        time.sleep(2)
        
        # 嘗試所有可能的選擇器
        for selector in config['input_selectors']:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        print(f"✅ 找到輸入框: {selector}")
                        return element
            except Exception as e:
                continue
        
        return None
    
    def find_send_button(self, ai_name: str):
        """尋找發送按鈕"""
        config = self.ai_configs.get(ai_name)
        if not config:
            return None
        
        # 嘗試所有可能的發送按鈕選擇器
        for selector in config['send_button_selectors']:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        print(f"✅ 找到發送按鈕: {selector}")
                        return element
            except Exception as e:
                continue
        
        return None
    
    def send_to_ai_with_file(self, ai_name: str, file_path: str, additional_prompt: str = None) -> bool:
        """
        使用文件上傳的方式發送到 AI
        
        Args:
            ai_name: AI 名稱
            file_path: 文件路徑
            additional_prompt: 額外的提示詞
            
        Returns:
            是否成功發送
        """
        config = self.ai_configs.get(ai_name)
        if not config:
            print(f"❌ 不支援的 AI: {ai_name}")
            return False
        
        try:
            print(f"🌐 正在處理 {config['name']}...")
            
            # 檢查當前頁面，如果不是目標網站則導航
            current_url = self.driver.current_url
            if config['url'] not in current_url:
                print(f"🔄 導航到 {config['name']}")
                self.driver.get(config['url'])
                
                # 為 Claude 添加額外等待時間
                if ai_name == 'claude':
                    print("⏳ Claude 載入中，請稍等...")
                    time.sleep(8)  # Claude 需要更長的載入時間
                    
                    # 檢查是否需要登入
                    try:
                        login_elements = self.driver.find_elements(By.CSS_SELECTOR, '[href*="login"], [href*="sign"], .login, .signin')
                        if login_elements:
                            print("⚠️  Claude 需要登入，請在瀏覽器中手動登入後按 Enter 繼續...")
                            input("按 Enter 繼續...")
                    except:
                        pass
                else:
                    time.sleep(5)  # 其他網站的標準等待時間
            
            # 嘗試上傳文件
            if config.get('supports_file_upload'):
                if self.upload_file(ai_name, file_path):
                    # 如果有額外的提示詞，添加到輸入框
                    if additional_prompt:
                        input_element = self.find_input_element(ai_name)
                        if input_element:
                            input_element.click()
                            time.sleep(0.5)
                            input_element.send_keys(additional_prompt)
                            time.sleep(1)
                    
                    # 發送
                    send_button = self.find_send_button(ai_name)
                    if send_button:
                        print(f"🚀 正在發送到 {config['name']}...")
                        send_button.click()
                        print(f"✅ 文件和提示已發送到 {config['name']}")
                        time.sleep(3)
                        return True
                    else:
                        # 嘗試用 Enter 鍵發送
                        input_element = self.find_input_element(ai_name)
                        if input_element:
                            input_element.send_keys(Keys.RETURN)
                            print(f"✅ 已使用 Enter 鍵發送到 {config['name']}")
                            time.sleep(3)
                            return True
                else:
                    print(f"⚠️  文件上傳失敗，嘗試文字輸入方式")
                    return self.send_to_ai_with_text(ai_name, file_path)
            else:
                print(f"⚠️  {config['name']} 不支援文件上傳，使用文字輸入方式")
                return self.send_to_ai_with_text(ai_name, file_path)
                
        except Exception as e:
            print(f"❌ 發送到 {config['name']} 失敗: {e}")
            if ai_name == 'claude':
                print("💡 Claude 建議: 請確保已登入 Claude，並關閉任何廣告攔截器")
            return False
    
    def send_to_ai_with_text(self, ai_name: str, file_path: str) -> bool:
        """
        備用方案：讀取文件內容並以文字方式發送
        
        Args:
            ai_name: AI 名稱
            file_path: 文件路徑
            
        Returns:
            是否成功發送
        """
        try:
            # 讀取文件內容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 尋找輸入框
            input_element = self.find_input_element(ai_name)
            if not input_element:
                print(f"❌ 找不到 {self.ai_configs[ai_name]['name']} 的輸入框")
                return False
            
            print(f"📝 正在以文字方式輸入內容到 {self.ai_configs[ai_name]['name']}...")
            
            # 分段輸入以避免超長文字
            input_element.click()
            time.sleep(0.5)
            
            # 清空現有內容
            input_element.send_keys(Keys.CONTROL + "a")
            time.sleep(0.1)
            input_element.send_keys(Keys.DELETE)
            time.sleep(0.5)
            
            # 分段輸入，每次1000字符
            chunk_size = 1000
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i+chunk_size]
                input_element.send_keys(chunk)
                time.sleep(0.1)  # 短暫停頓
            
            print(f"✅ 內容輸入完成")
            time.sleep(1)
            
            # 發送
            send_button = self.find_send_button(ai_name)
            if send_button:
                print(f"🚀 正在發送...")
                send_button.click()
                print(f"✅ 內容已發送到 {self.ai_configs[ai_name]['name']}")
                time.sleep(3)
                return True
            else:
                # 嘗試用 Enter 鍵發送
                input_element.send_keys(Keys.RETURN)
                print(f"✅ 已使用 Enter 鍵發送到 {self.ai_configs[ai_name]['name']}")
                time.sleep(3)
                return True
                
        except Exception as e:
            print(f"❌ 文字發送失敗: {e}")
            return False
    
    def batch_send_file(self, file_path: str, ai_list: List[str] = None, 
                       additional_prompt: str = None) -> Dict[str, bool]:
        """批量發送文件到多個 AI"""
        if ai_list is None:
            ai_list = ['chatgpt', 'claude', 'gemini']
        
        if not self.setup_connection():
            print("❌ 無法連接到 Chrome 瀏覽器")
            return {}
        
        # 設定當前處理的文件
        self.current_file_path = file_path
        results = {}
        
        try:
            for ai_name in ai_list:
                if ai_name not in self.ai_configs:
                    print(f"⚠️  跳過不支援的 AI: {ai_name}")
                    continue
                
                print(f"\n{'='*50}")
                print(f"🤖 正在處理 {self.ai_configs[ai_name]['name']}")
                print(f"{'='*50}")
                
                try:
                    results[ai_name] = self.send_to_ai_with_file(ai_name, file_path, additional_prompt)
                except Exception as e:
                    print(f"❌ {self.ai_configs[ai_name]['name']} 處理失敗: {e}")
                    results[ai_name] = False
                    
                    # 詢問是否跳過或重試
                    if ai_name != ai_list[-1]:  # 不是最後一個
                        choice = input(f"\n⚠️  {self.ai_configs[ai_name]['name']} 出現問題，要 (s)跳過 還是 (r)重試？(s/r): ").strip().lower()
                        if choice == 'r':
                            print(f"🔄 重試 {self.ai_configs[ai_name]['name']}...")
                            try:
                                results[ai_name] = self.send_to_ai_with_file(ai_name, file_path, additional_prompt)
                            except Exception as retry_e:
                                print(f"❌ 重試失敗: {retry_e}")
                                results[ai_name] = False
                
                # 如果不是最後一個，等待用戶確認
                if ai_name != ai_list[-1]:
                    input(f"\n✅ {self.ai_configs[ai_name]['name']} 處理完成，按 Enter 繼續下一個...")
            
            # 處理完成後，根據成功率決定是否刪除文件
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            if self.should_delete_file(file_path, success_count, total_count):
                self.safe_delete_file(file_path)
            else:
                print(f"📁 文件已保留: {file_path}")
        
        finally:
            self.cleanup()
        
        return results
    
    def interactive_send_file(self, file_path: str):
        """互動式文件發送模式"""
        print("🎯 文件上傳模式")
        print("="*50)
        
        # 檢查文件是否存在
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return
        
        print(f"📁 準備發送文件: {file_path}")
        print(f"🗑️  文件將在成功上傳後自動清理")
        
        # 選擇 AI
        print("\n請選擇要發送的 AI：")
        print("1. ChatGPT")
        print("2. Claude") 
        print("3. Gemini")
        print("4. Grok")
        print("5. Perplexity")
        print("6. 多選（輸入數字，用逗號分隔，如：1,2,3）")
        
        ai_choice = input("請輸入選項: ").strip()
        
        ai_mapping = {
            '1': ['chatgpt'],
            '2': ['claude'], 
            '3': ['gemini'],
            '4': ['grok'],
            '5': ['perplexity']
        }
        
        if ',' in ai_choice:
            # 多選模式
            selected_numbers = ai_choice.split(',')
            ai_list = []
            for num in selected_numbers:
                num = num.strip()
                if num in ai_mapping:
                    ai_list.extend(ai_mapping[num])
        else:
            ai_list = ai_mapping.get(ai_choice, ['chatgpt'])
        
        # 詢問是否需要額外的提示詞
        additional_prompt = input("\n是否需要額外的提示詞？(直接按 Enter 跳過): ").strip()
        if not additional_prompt:
            additional_prompt = None
        
        # 執行發送
        results = self.batch_send_file(file_path, ai_list, additional_prompt)
        
        # 顯示結果
        print("\n📊 發送結果摘要：")
        for ai_name, success in results.items():
            status = "✅ 成功" if success else "❌ 失敗"
            ai_display_name = self.ai_configs.get(ai_name, {}).get('name', ai_name)
            print(f"  {ai_display_name}: {status}")
        
        # 顯示文件清理狀態
        success_count = sum(1 for success in results.values() if success)
        if success_count > 0 and not os.path.exists(file_path):
            print(f"🗑️  文件已自動清理")
        elif success_count > 0:
            print(f"📁 文件保留: {file_path}")
        else:
            print(f"⚠️  所有平台處理失敗，文件已保留: {file_path}")
    
    def cleanup(self):
        """清理資源"""
        if self.chrome_connector:
            self.chrome_connector.close()
            print("🧹 連接已關閉")

    def safe_delete_file(self, file_path: str) -> bool:
        """
        安全地刪除文件
        
        Args:
            file_path: 要刪除的文件路徑
            
        Returns:
            是否成功刪除
        """
        try:
            # 安全檢查：只刪除 ai_uploads 目錄下的 .txt 文件
            if not file_path:
                return False
            
            # 獲取絕對路徑
            abs_path = os.path.abspath(file_path)
            
            # 檢查文件是否存在
            if not os.path.exists(abs_path):
                print(f"⚠️  文件不存在，無需刪除: {file_path}")
                return True
            
            # 安全檢查：確保文件在 ai_uploads 目錄下且是 .txt 文件
            if 'ai_uploads' not in abs_path or not abs_path.endswith('.txt'):
                print(f"⚠️  為了安全，跳過刪除非 AI 上傳文件: {file_path}")
                return False
            
            # 刪除文件
            os.remove(abs_path)
            print(f"🗑️  文件已自動刪除: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ 刪除文件時發生錯誤: {e}")
            return False
    
    def should_delete_file(self, file_path: str, success_count: int, total_count: int) -> bool:
        """
        判斷是否應該刪除文件
        
        Args:
            file_path: 文件路徑
            success_count: 成功上傳的 AI 數量
            total_count: 總 AI 數量
            
        Returns:
            是否應該刪除
        """
        if not self.auto_delete_files:
            return False
        
        # 只有在至少有一個 AI 成功處理時才刪除
        if success_count > 0:
            print(f"📊 上傳結果: {success_count}/{total_count} 個 AI 平台成功處理")
            return True
        
        print(f"⚠️  所有 AI 平台都處理失敗，保留文件: {file_path}")
        return False

def main():
    """主程序"""
    print("🤖 增強版 YouTube to AI 自動發送工具 (現有瀏覽器版)")
    print("📌 優先使用現有的 Chrome 瀏覽器，避免重複開啟")
    print("🗑️  自動清理: 文件成功上傳後將自動刪除")
    print("🌐 瀏覽器: 連接到您現有的 Chrome 瀏覽器")
    print("="*60)
    
    try:
        # 直接進入完整流程
        video_url = input("請輸入 YouTube 影片 URL: ").strip()
        if not video_url:
            print("❌ 請提供有效的 YouTube 影片 URL")
            return
        
        try:
            # 導入 YouTube 提取器
            from youtube_text_extractor import YouTubeTextExtractor
            
            print("🎬 開始處理 YouTube 影片...")
            extractor = YouTubeTextExtractor()
            
            # 使用新的顯示菜單選擇 Prompt 類型
            prompt_type = extractor.display_prompt_types_menu()
            
            # 創建 AI 準備文件
            file_path = extractor.create_ai_ready_file(video_url, prompt_type)
            
            if not file_path:
                print("❌ 無法創建 AI 文件")
                return
            
            print(f"✅ AI 文件已創建: {file_path}")
            
            # 發送到 AI
            sender = EnhancedAIWebSender()
            sender.interactive_send_file(file_path)
            
        except ImportError:
            print("❌ 請確保 youtube_text_extractor.py 在同一目錄下")
    
    except KeyboardInterrupt:
        print("\n👋 程序已中斷")
    except Exception as e:
        print(f"❌ 程序執行錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()