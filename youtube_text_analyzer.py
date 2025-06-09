#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube 文字分析器
專注於 YouTube 文字提取 + 分析 Prompt 生成 + 自動複製到剪貼板
無需檔案生成，直接記憶體處理
"""

import os
import sys
from typing import Dict, Optional, List
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import hashlib
import argparse

# 導入剪貼板功能
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False
    print("❌ 剪貼板功能不可用，請運行: pip install pyperclip")
    sys.exit(1)

try:
    from youtube_text_extractor import YouTubeTextExtractor
except ImportError:
    print("❌ 無法導入 YouTubeTextExtractor")
    print("📋 請確保 youtube_text_extractor.py 在同一目錄下")
    sys.exit(1)

# 添加專案根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class YouTubeTextAnalyzer:
    """YouTube 文字分析器 - 高速版本"""
    
    def __init__(self):
        """初始化分析器"""
        self.extractor = YouTubeTextExtractor()
        self._cache = {}  # 簡單的記憶體緩存
        self._cache_lock = threading.Lock()  # 確保線程安全
    
    def _get_cache_key(self, video_id: str, prompt_type: str) -> str:
        """生成緩存鍵值"""
        return f"{video_id}_{prompt_type}_{hashlib.md5((video_id + prompt_type).encode()).hexdigest()[:8]}"
    
    def _get_from_cache(self, video_id: str, prompt_type: str) -> Optional[str]:
        """從緩存獲取內容"""
        key = self._get_cache_key(video_id, prompt_type)
        with self._cache_lock:
            return self._cache.get(key)
    
    def _save_to_cache(self, video_id: str, prompt_type: str, content: str):
        """保存到緩存"""
        key = self._get_cache_key(video_id, prompt_type)
        with self._cache_lock:
            self._cache[key] = content
            # 簡單的緩存大小控制，避免記憶體過度使用
            if len(self._cache) > 50:  # 最多保留50個結果
                # 刪除最舊的一半
                keys_to_remove = list(self._cache.keys())[:25]
                for k in keys_to_remove:
                    del self._cache[k]
    
    def copy_to_clipboard(self, content: str) -> bool:
        """
        複製內容到剪貼板
        
        Args:
            content: 要複製的內容
            
        Returns:
            是否成功複製
        """
        try:
            pyperclip.copy(content)
            print("✅ 內容已自動複製到剪貼板！")
            print("📋 現在您可以直接 Ctrl+V 貼到任何 AI 網站使用")
            return True
            
        except Exception as e:
            print(f"❌ 複製到剪貼板失敗: {e}")
            return False
    
    def analyze_video(self, video_url: str, prompt_type: str = None) -> bool:
        """
        分析影片並自動複製到剪貼板（優化版本）
        
        Args:
            video_url: YouTube 影片 URL
            prompt_type: 分析類型
            
        Returns:
            是否成功處理
        """
        print("🚀 YouTube 高速文字分析器")
        print("="*50)
        
        # 如果沒有指定分析類型，顯示選單
        if not prompt_type:
            prompt_type = self._select_prompt_type()
            if not prompt_type:
                print("❌ 未選擇分析類型")
                return False
        
        # 提取影片資訊和文字
        print(f"\n🔍 開始處理影片: {video_url}")
        print(f"📊 分析類型: {prompt_type}")
        
        start_time = time.time()
        
        try:
            # 直接生成內容字串，不保存檔案
            content = self._create_ai_content(video_url, prompt_type)
            
            process_time = time.time() - start_time
            
            if content:
                print(f"\n✅ 分析完成！({process_time:.1f} 秒)")
                print(f"📄 內容長度: {len(content)} 字元")
                
                # 顯示內容預覽
                self._show_content_preview(content)
                
                # 自動複製到剪貼板
                self.copy_to_clipboard(content)
                
                return True
            else:
                print("❌ 內容生成失敗")
                return False
                
        except Exception as e:
            print(f"❌ 處理過程中發生錯誤: {e}")
            return False
    
    def _create_ai_content(self, video_url: str, prompt_type: str) -> Optional[str]:
        """
        創建AI分析內容（記憶體處理，不生成檔案）- 優化版本
        
        Args:
            video_url: YouTube 影片 URL
            prompt_type: 分析類型
            
        Returns:
            生成的內容字串或 None
        """
        try:
            # 提取影片ID
            video_id = self.extractor.extract_video_id(video_url)
            if not video_id:
                print("❌ 無法提取影片ID")
                return None
            
            # 檢查緩存
            cached_content = self._get_from_cache(video_id, prompt_type)
            if cached_content:
                print("⚡ 從緩存獲取內容")
                return cached_content
            
            # 快速檢查（簡化版本）
            print("🔍 檢查影片...")
            
            # 直接提取文字稿（使用增強版本）
            print("📥 提取影片文字稿...")
            transcript = self.extractor.extract_transcript(video_id)
            
            # 如果標準方法失敗，嘗試詳細調試方法
            if not transcript:
                print("⚠️ 標準方法失敗，嘗試詳細調試方法...")
                transcript = self.extractor.extract_transcript_with_detailed_debug(video_id)
            
            # 如果還是失敗，嘗試備用方法
            if not transcript:
                print("⚠️ 詳細調試方法失敗，嘗試備用方法...")
                transcript = self.extractor.extract_transcript_alternative(video_id)
            
            if not transcript:
                print("❌ 無法提取影片文字稿")
                # 提供診斷信息
                print("🔍 執行診斷以獲取更多信息...")
                diagnosis = self.extractor.diagnose_video_transcript_issues(video_id)
                if diagnosis['recommended_actions']:
                    print("💡 建議操作:")
                    for action in diagnosis['recommended_actions'][:3]:
                        print(f"  • {action}")
                return None
            
            # 清理文字
            cleaned_text = self.extractor.clean_text(transcript)
            
            # 獲取影片資訊（簡化版）
            video_info = {
                'id': video_id,
                'url': video_url,
                'title': f"YouTube Video {video_id}"  # 簡化標題以加速
            }
            
            # 獲取prompt模板
            prompt_templates = self.extractor._get_prompt_templates()
            if prompt_type not in prompt_templates:
                print(f"❌ 不支援的分析類型: {prompt_type}")
                return None
            
            prompt_content = prompt_templates[prompt_type]
            
            # 組合最終內容
            content = f"""影片標題：{video_info['title']}
影片 ID：{video_info['id']}
影片 URL：{video_info['url']}
============================================================

AI 分析 Prompt ({prompt_type})：
----------------------------------------
{prompt_content}

============================================================

YouTube 影片完整文字稿：
----------------------------------------
{cleaned_text}"""
            
            # 保存到緩存
            self._save_to_cache(video_id, prompt_type, content)
            
            return content
            
        except Exception as e:
            print(f"❌ 創建內容時發生錯誤: {e}")
            return None
    
    def _select_prompt_type(self) -> Optional[str]:
        """顯示分析類型選單並讓用戶選擇"""
        print("\n📋 請選擇分析類型:")
        
        # 獲取可用的分析類型
        prompt_types = self.extractor.get_available_prompt_types()
        
        # 顯示選單
        for i, (key, info) in enumerate(prompt_types.items(), 1):
            icon = info.get('icon', '📝')
            name = info.get('name', key)
            description = info.get('description', '')
            print(f"{i:2d}. {icon} {name}")
            if description:
                print(f"     {description}")
        
        print(f"{len(prompt_types) + 1:2d}. ❌ 取消")
        
        # 用戶選擇
        try:
            choice = input(f"\n請選擇 (1-{len(prompt_types) + 1}): ").strip()
            choice_num = int(choice)
            
            if choice_num == len(prompt_types) + 1:
                return None
            
            if 1 <= choice_num <= len(prompt_types):
                selected_key = list(prompt_types.keys())[choice_num - 1]
                selected_info = prompt_types[selected_key]
                print(f"\n✅ 已選擇: {selected_info.get('icon', '📝')} {selected_info.get('name', selected_key)}")
                return selected_key
            else:
                print("❌ 無效選擇")
                return None
                
        except (ValueError, IndexError):
            print("❌ 無效輸入")
            return None
    
    def _show_content_preview(self, content: str):
        """顯示內容預覽"""
        try:
            lines = content.split('\n')
            preview_lines = lines[:10]  # 顯示前10行
            
            print(f"\n📖 內容預覽 (前10行):")
            print("-" * 50)
            for line in preview_lines:
                print(line)
            
            if len(lines) > 10:
                print(f"... (還有 {len(lines) - 10} 行)")
            print("-" * 50)
            
        except Exception as e:
            print(f"⚠️  無法預覽內容: {e}")
    
    def _process_single_video(self, video_url: str, prompt_type: str, video_index: int = None) -> tuple:
        """
        處理單個影片（用於並行處理）
        
        Returns:
            (video_url, success, content, error_message)
        """
        try:
            prefix = f"[{video_index}]" if video_index else ""
            print(f"{prefix} 🎥 處理: {video_url[:50]}...")
            
            start_time = time.time()
            content = self._create_ai_content(video_url, prompt_type)
            process_time = time.time() - start_time
            
            if content:
                print(f"{prefix} ✅ 完成 ({process_time:.1f}秒)")
                return (video_url, True, content, None)
            else:
                print(f"{prefix} ❌ 失敗")
                return (video_url, False, None, "內容生成失敗")
                
        except Exception as e:
            print(f"{prefix} ❌ 錯誤: {str(e)[:100]}")
            return (video_url, False, None, str(e))
    
    def batch_analyze(self, video_urls: list, prompt_type: str = None, max_workers: int = 4) -> Dict[str, bool]:
        """
        高速批次分析多個影片（並行處理）
        
        Args:
            video_urls: YouTube 影片 URL 列表
            prompt_type: 分析類型
            max_workers: 最大並行處理數（預設4）
            
        Returns:
            分析結果字典 {url: success}
        """
        print(f"🚀 高速批次分析 {len(video_urls)} 個影片（並行處理）")
        
        # 如果沒有指定分析類型，顯示選單
        if not prompt_type:
            prompt_type = self._select_prompt_type()
            if not prompt_type:
                print("❌ 未選擇分析類型")
                return {}
        
        results = {}
        successful_contents = []
        
        start_time = time.time()
        
        # 使用線程池並行處理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任務
            future_to_url = {
                executor.submit(self._process_single_video, url, prompt_type, i+1): url 
                for i, url in enumerate(video_urls)
            }
            
            # 收集結果
            for future in as_completed(future_to_url):
                url, success, content, error = future.result()
                results[url] = success
                
                if success and content:
                    successful_contents.append(f"=== 影片 {len(successful_contents)+1}: {url} ===\n{content}")
        
        total_time = time.time() - start_time
        successful_count = len(successful_contents)
        
        print(f"\n📊 批次分析完成！")
        print(f"⏱️  總時間: {total_time:.1f} 秒")
        print(f"✅ 成功: {successful_count}/{len(video_urls)}")
        print(f"⚡ 平均速度: {total_time/len(video_urls):.1f} 秒/影片")
        
        # 合併成功的內容並複製到剪貼板
        if successful_contents:
            self._copy_batch_content(successful_contents)
        else:
            print("❌ 沒有成功處理的影片")
        
        return results
    
    def _copy_batch_content(self, successful_contents: list):
        """
        複製批次內容到剪貼板
        
        Args:
            successful_contents: 成功處理的內容列表
        """
        try:
            # 計算統計資訊
            total_videos = len(successful_contents)
            total_length = sum(len(content) for content in successful_contents)
            
            # 創建批次標題
            batch_header = f"""
🚀 YouTube 高速批次分析結果
===============================================
📊 處理影片數量: {total_videos}
📄 總內容長度: {total_length:,} 字元
⏰ 處理時間: {time.strftime('%Y-%m-%d %H:%M:%S')}
===============================================

"""
            
            # 合併所有內容
            combined_content = batch_header + "\n\n".join(successful_contents)
            
            # 複製到剪貼板
            print(f"\n📋 合併複製 {total_videos} 個分析結果...")
            if self.copy_to_clipboard(combined_content):
                print(f"✅ 已複製完整批次分析結果到剪貼板！")
                print(f"📊 總長度: {len(combined_content):,} 字元")
            else:
                print("❌ 複製到剪貼板失敗")
                
        except Exception as e:
            print(f"❌ 複製批次內容時發生錯誤: {e}")
    
    def clear_cache(self):
        """清除緩存"""
        with self._cache_lock:
            self._cache.clear()
        print("🗑️  緩存已清除")
    
    def get_cache_stats(self):
        """獲取緩存統計資訊"""
        with self._cache_lock:
            return {
                'cached_items': len(self._cache),
                'cache_keys': list(self._cache.keys())
            }
    
    def show_usage(self):
        """顯示使用說明"""
        print("""
🚀 YouTube 高速文字分析器 v2.0
===============================================

✨ 新功能特色:
• ⚡ 並行處理 - 批次分析時同時處理多個影片
• 🧠 智能緩存 - 自動緩存結果，重複分析瞬間完成
• 🎯 快速提取 - 優化的文字稿提取算法
• 📊 性能監控 - 顯示處理時間和速度統計

💡 使用方式:

1️⃣  單個影片分析（高速模式）:
   python youtube_text_analyzer.py

2️⃣  批次影片分析（並行處理）:
   python youtube_text_analyzer.py --batch

3️⃣  指定分析類型:
   python youtube_text_analyzer.py --type summary

4️⃣  清除緩存:
   python youtube_text_analyzer.py --clear-cache

📋 支援的分析類型:
   summary, deep_analysis, questions, translation, mind_map,
   historical_verification, trend_analysis, future_prediction,
   industry_insights, fact_check

🔧 批次處理說明:
• 在批次模式下，一次輸入多個 YouTube URL（每行一個）
• 系統會並行處理，大大提升速度
• 支援最多同時處理 4 個影片（可調整）
• 自動合併所有成功分析的結果到剪貼板

⚡ 性能優化:
• 智能緩存: 相同影片+分析類型的結果會被緩存
• 並行處理: 批次分析使用多線程同時處理
• 快速模式: 移除不必要的檢查步驟
• 內存處理: 完全不產生檔案，直接操作內存

💾 緩存說明:
• 自動緩存最近 50 個分析結果
• 重複分析相同影片會瞬間完成
• 可使用 --clear-cache 清除緩存

⚠️  注意事項:
• 需要安裝 pyperclip: pip install pyperclip
• 並行處理會增加 CPU 和網路使用量
• 過多並行請求可能被 YouTube 限制

===============================================
        """.strip())

def main():
    """主程序入口 - 高速版本"""
    # 創建命令行參數解析器
    parser = argparse.ArgumentParser(description='YouTube 高速文字分析器 v2.0')
    parser.add_argument('--batch', action='store_true', help='批次分析模式（並行處理）')
    parser.add_argument('--type', type=str, help='指定分析類型')
    parser.add_argument('--workers', type=int, default=4, help='並行處理數量（預設4）')
    parser.add_argument('--clear-cache', action='store_true', help='清除緩存')
    parser.add_argument('--cache-stats', action='store_true', help='顯示緩存統計')
    parser.add_argument('--help-usage', action='store_true', help='顯示詳細使用說明')
    
    args = parser.parse_args()
    
    # 創建分析器實例
    analyzer = YouTubeTextAnalyzer()
    
    # 處理特殊命令
    if args.clear_cache:
        analyzer.clear_cache()
        return
    
    if args.cache_stats:
        stats = analyzer.get_cache_stats()
        print(f"📊 緩存統計: {stats['cached_items']} 個項目")
        return
        
    if args.help_usage:
        analyzer.show_usage()
        return
    
    try:
        if args.batch:
            # 批次分析模式
            print("🚀 YouTube 高速批次分析器")
            print("="*50)
            print("📝 請輸入多個 YouTube 影片 URL（每行一個），完成後輸入空行:")
            
            urls = []
            while True:
                url = input("URL: ").strip()
                if not url:
                    break
                if url:
                    urls.append(url)
            
            if not urls:
                print("❌ 未輸入任何 URL")
                return
            
            print(f"\n📊 將並行處理 {len(urls)} 個影片")
            if args.workers != 4:
                print(f"⚙️  並行數量: {args.workers}")
            
            # 執行批次分析
            results = analyzer.batch_analyze(urls, args.type, args.workers)
            
            # 顯示最終統計
            success_count = sum(1 for success in results.values() if success)
            print(f"\n🏁 最終結果: {success_count}/{len(urls)} 成功")
            
        else:
            # 單個影片分析模式
            url = input("🎬 請輸入 YouTube 影片 URL: ").strip()
            if not url:
                print("❌ 未輸入 URL")
                return
            
            # 執行單個分析
            success = analyzer.analyze_video(url, args.type)
            
            if success:
                print("\n🎉 分析完成！內容已複製到剪貼板")
                print("💡 現在可以直接 Ctrl+V 貼到 ChatGPT、Claude 等 AI 網站")
            else:
                print("\n❌ 分析失敗")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  用戶中斷操作")
    except Exception as e:
        print(f"\n❌ 程序發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 