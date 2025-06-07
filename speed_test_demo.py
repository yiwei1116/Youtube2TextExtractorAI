#!/usr/bin/env python3
"""
YouTube 高速文字分析器 - 速度測試演示

展示新版本的性能提升：
1. 並行處理
2. 智能緩存
3. 優化提取
"""

import time
import sys
import os

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from youtube_text_analyzer import YouTubeTextAnalyzer

def speed_demo():
    """展示速度優化效果"""
    print("🚀 YouTube 高速文字分析器 - 性能演示")
    print("="*60)
    
    analyzer = YouTubeTextAnalyzer()
    
    # 示例影片 URL (請替換為真實的 YouTube URL)
    demo_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # 請替換為真實 URL
        "https://www.youtube.com/watch?v=9bZkp7q19f0",  # 請替換為真實 URL
        "https://www.youtube.com/watch?v=ScMzIvxBSi4"   # 請替換為真實 URL
    ]
    
    print("📝 請輸入 2-3 個 YouTube 影片 URL 來測試高速批次處理:")
    print("(或直接按 Enter 使用示例 URL)")
    
    # 收集用戶輸入的 URL
    user_urls = []
    for i in range(3):
        url = input(f"URL {i+1} (可選): ").strip()
        if url:
            user_urls.append(url)
    
    # 使用用戶輸入的 URL 或示例 URL
    test_urls = user_urls if user_urls else demo_urls
    
    if not test_urls:
        print("❌ 沒有可測試的 URL")
        return
    
    print(f"\n🎯 準備測試 {len(test_urls)} 個影片")
    print("📊 將測試: 單個處理 vs 並行處理")
    
    # 測試 1: 傳統逐個處理 (模擬)
    print(f"\n⏱️  測試 1: 傳統逐個處理模式")
    start_time = time.time()
    sequential_results = {}
    
    for i, url in enumerate(test_urls, 1):
        print(f"處理第 {i} 個影片...")
        try:
            content = analyzer._create_ai_content(url, 'summary')
            sequential_results[url] = content is not None
        except Exception:
            sequential_results[url] = False
    
    sequential_time = time.time() - start_time
    sequential_success = sum(1 for success in sequential_results.values() if success)
    
    print(f"✅ 逐個處理完成: {sequential_time:.1f} 秒")
    print(f"📊 成功處理: {sequential_success}/{len(test_urls)}")
    
    # 清除緩存以確保公平測試
    analyzer.clear_cache()
    
    # 測試 2: 高速並行處理
    print(f"\n⚡ 測試 2: 高速並行處理模式")
    start_time = time.time()
    
    parallel_results = analyzer.batch_analyze(test_urls, 'summary', max_workers=4)
    
    parallel_time = time.time() - start_time
    parallel_success = sum(1 for success in parallel_results.values() if success)
    
    print(f"✅ 並行處理完成: {parallel_time:.1f} 秒")
    print(f"📊 成功處理: {parallel_success}/{len(test_urls)}")
    
    # 性能對比
    print(f"\n🏆 性能對比結果:")
    print(f"⏱️  逐個處理: {sequential_time:.1f} 秒")
    print(f"⚡ 並行處理: {parallel_time:.1f} 秒")
    
    if parallel_time < sequential_time:
        speedup = sequential_time / parallel_time
        print(f"🚀 速度提升: {speedup:.1f}x 倍！")
        time_saved = sequential_time - parallel_time
        print(f"💾 節省時間: {time_saved:.1f} 秒")
    
    # 測試 3: 緩存效果
    print(f"\n🧠 測試 3: 智能緩存效果")
    if test_urls:
        test_url = test_urls[0]
        print(f"重複分析第一個影片...")
        
        start_time = time.time()
        cached_content = analyzer._create_ai_content(test_url, 'summary')
        cache_time = time.time() - start_time
        
        print(f"⚡ 緩存提取時間: {cache_time:.3f} 秒")
        print(f"🎯 緩存效果: {'成功' if cache_time < 1.0 else '需要優化'}")
    
    # 緩存統計
    cache_stats = analyzer.get_cache_stats()
    print(f"\n📈 緩存統計: {cache_stats['cached_items']} 個項目已緩存")
    
    print(f"\n🎉 性能測試完成！")
    print(f"💡 新版本的主要優勢:")
    print(f"   • 並行處理大幅提升批次分析速度")
    print(f"   • 智能緩存讓重複分析瞬間完成") 
    print(f"   • 優化算法減少不必要的等待時間")

def main():
    """主程序"""
    try:
        speed_demo()
    except KeyboardInterrupt:
        print("\n\n⚠️  測試中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    main() 