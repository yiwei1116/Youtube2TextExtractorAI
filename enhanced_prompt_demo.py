#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強版 Prompt 功能演示腳本
展示歷史驗證、趨勢分析、未來預測等新功能
"""

import os
from youtube_text_extractor import YouTubeTextExtractor

def demo_all_prompt_types():
    """演示所有 Prompt 類型"""
    print("🚀 增強版 YouTube Prompt 分析系統")
    print("✨ 支援歷史驗證、趨勢分析、未來預測等高階功能")
    print("=" * 80)
    
    # 初始化提取器
    extractor = YouTubeTextExtractor()
    
    # 顯示所有可用的 prompt 類型
    prompt_types = extractor.get_available_prompt_types()
    
    print("\n📋 系統支援的 AI 分析類型概覽:")
    print("=" * 80)
    
    for key, info in prompt_types.items():
        print(f"\n🎯 {info['name']}")
        print(f"   📝 描述: {info['description']}")
        print(f"   🎲 適用場景: {info['suitable_for']}")
        print(f"   📊 分析重點: {info['output_focus']}")
        print("-" * 70)
    
    print("\n🌟 新增的高階分析功能:")
    print("• 📊 歷史數據驗證 - 與過往數據對比，驗證內容真實性")
    print("• 📈 趨勢分析預測 - 識別發展趨勢，評估機會風險")
    print("• 🚀 未來預測分析 - 多情境建模，制定策略建議")
    print("• 🏢 行業洞察分析 - 專業投資角度，市場環境評估")
    print("• ✅ 事實核查報告 - 系統性核查，可信度評估")
    
    print("\n🗑️  文件管理功能:")
    print("• 自動清理 - 所有分析文件在上傳到 AI 後將自動刪除")
    print("• 智能保留 - 處理失敗時文件會保留以便重試")
    print("• 安全刪除 - 只刪除 ai_uploads 目錄下的 .txt 文件")
    print("• 磁盤優化 - 自動維持乾淨的工作環境")
    
    return extractor

def demo_create_sample_files():
    """創建示例文件展示不同 prompt 類型"""
    print("\n📁 創建示例文件展示")
    print("=" * 50)
    
    # 示例影片 URL（可替換為實際影片）
    demo_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # 經典測試影片
        "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # 另一個測試影片
    ]
    
    extractor = YouTubeTextExtractor()
    prompt_types = extractor.get_available_prompt_types()
    
    video_url = input("請輸入 YouTube 影片 URL (按 Enter 使用示例): ").strip()
    if not video_url:
        video_url = demo_urls[0]
        print(f"使用示例 URL: {video_url}")
    
    print("\n📝 選擇要創建的分析類型:")
    print("1. 創建單一類型分析文件")
    print("2. 創建所有類型的分析文件 (批量)")
    print("3. 創建自定義組合")
    
    choice = input("請選擇 (1-3): ").strip()
    
    if choice == '1':
        # 單一類型
        prompt_type = extractor.display_prompt_types_menu()
        create_single_analysis_file(extractor, video_url, prompt_type)
        
    elif choice == '2':
        # 批量創建所有類型
        create_all_analysis_files(extractor, video_url)
        
    elif choice == '3':
        # 自定義組合
        create_custom_combination(extractor, video_url)
    
    else:
        print("無效選擇")

def create_single_analysis_file(extractor, video_url, prompt_type):
    """創建單一分析文件"""
    print(f"\n🔄 正在創建 {prompt_type} 分析文件...")
    
    try:
        file_path = extractor.create_ai_ready_file(video_url, prompt_type)
        
        if file_path:
            print(f"✅ 文件創建成功: {file_path}")
            
            # 顯示文件內容預覽
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"\n📄 文件內容預覽:")
                print("-" * 60)
                print(content[:500] + "..." if len(content) > 500 else content)
                print("-" * 60)
        else:
            print("❌ 文件創建失敗")
            
    except Exception as e:
        print(f"❌ 創建過程中發生錯誤: {e}")

def create_all_analysis_files(extractor, video_url):
    """批量創建所有類型的分析文件"""
    print(f"\n🔄 正在批量創建所有分析類型...")
    
    prompt_types = extractor.get_available_prompt_types()
    created_files = []
    
    for prompt_type, info in prompt_types.items():
        print(f"\n📝 正在創建: {info['name']}")
        
        try:
            file_path = extractor.create_ai_ready_file(video_url, prompt_type)
            
            if file_path:
                created_files.append((prompt_type, file_path, info['name']))
                print(f"✅ 成功: {file_path}")
            else:
                print(f"❌ 失敗: {prompt_type}")
                
        except Exception as e:
            print(f"❌ 錯誤: {e}")
    
    # 顯示摘要
    print(f"\n📊 批量創建完成!")
    print(f"總共創建了 {len(created_files)} 個分析文件:")
    print("-" * 60)
    
    for prompt_type, file_path, name in created_files:
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        print(f"• {name}")
        print(f"  檔案: {file_path} ({file_size:,} bytes)")
    
    print(f"\n🎯 建議使用方式:")
    print("1. 基礎分析: summary → analysis")
    print("2. 深入研究: historical_verification → trend_analysis → future_prediction")
    print("3. 專業評估: industry_insight → fact_check")
    print("4. 學習應用: questions → mindmap → translation")

def create_custom_combination(extractor, video_url):
    """創建自定義組合"""
    print(f"\n🎨 自定義分析組合")
    print("=" * 50)
    
    prompt_types = extractor.get_available_prompt_types()
    
    print("請選擇要包含的分析類型 (輸入數字，用逗號分隔):")
    counter = 1
    type_mapping = {}
    
    for key, info in prompt_types.items():
        type_mapping[str(counter)] = key
        print(f"{counter:2d}. {info['name']}")
        counter += 1
    
    selection = input("\n請輸入選擇 (例如: 1,6,7,8): ").strip()
    
    if not selection:
        print("❌ 未選擇任何類型")
        return
    
    # 解析選擇
    selected_types = []
    for num in selection.split(','):
        num = num.strip()
        if num in type_mapping:
            selected_types.append(type_mapping[num])
    
    if not selected_types:
        print("❌ 無效選擇")
        return
    
    print(f"\n✅ 已選擇 {len(selected_types)} 個分析類型:")
    for prompt_type in selected_types:
        print(f"• {prompt_types[prompt_type]['name']}")
    
    # 創建文件
    created_files = []
    for prompt_type in selected_types:
        print(f"\n📝 正在創建: {prompt_types[prompt_type]['name']}")
        
        try:
            file_path = extractor.create_ai_ready_file(video_url, prompt_type)
            
            if file_path:
                created_files.append((prompt_type, file_path))
                print(f"✅ 成功: {file_path}")
            else:
                print(f"❌ 失敗: {prompt_type}")
                
        except Exception as e:
            print(f"❌ 錯誤: {e}")
    
    print(f"\n🎉 自定義組合創建完成!")
    print(f"成功創建 {len(created_files)} 個文件")

def demo_prompt_templates():
    """展示 Prompt 模板內容"""
    print("\n📋 Prompt 模板內容展示")
    print("=" * 50)
    
    extractor = YouTubeTextExtractor()
    templates = extractor._get_prompt_templates()
    
    print("選擇要查看的 Prompt 模板:")
    counter = 1
    type_mapping = {}
    
    for key in templates.keys():
        type_mapping[str(counter)] = key
        type_names = {
            'summary': '📝 智能摘要分析',
            'analysis': '🔍 深度專業分析',
            'questions': '❓ 學習問題生成',
            'translation': '🌐 多語言優化翻譯',
            'mindmap': '🧠 心智圖結構設計',
            'historical_verification': '📊 歷史數據驗證',
            'trend_analysis': '📈 趨勢分析預測',
            'future_prediction': '🚀 未來預測分析',
            'industry_insight': '🏢 行業洞察分析',
            'fact_check': '✅ 事實核查報告'
        }
        print(f"{counter:2d}. {type_names.get(key, key)}")
        counter += 1
    
    choice = input(f"\n請選擇 (1-{len(templates)}): ").strip()
    
    if choice in type_mapping:
        selected_type = type_mapping[choice]
        template = templates[selected_type]
        
        print(f"\n📄 {selected_type} Prompt 模板:")
        print("=" * 70)
        print(template)
        print("=" * 70)
        
        # 詢問是否要保存模板
        save_choice = input("\n💾 是否要將此 Prompt 模板保存為文件？(y/n): ").strip().lower()
        if save_choice in ['y', 'yes']:
            filename = f"prompt_template_{selected_type}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Prompt 類型: {selected_type}\n")
                f.write("=" * 50 + "\n\n")
                f.write(template)
            
            print(f"✅ Prompt 模板已保存至: {filename}")
    else:
        print("❌ 無效選擇")

def main():
    """主程序"""
    print("🎯 增強版 YouTube Prompt 系統演示")
    print("🚀 歷史驗證 • 趨勢分析 • 未來預測")
    print("=" * 60)
    
    try:
        while True:
            print("\n🎛️  請選擇功能:")
            print("1. 查看所有 Prompt 類型概覽")
            print("2. 創建 AI 分析文件")
            print("3. 查看 Prompt 模板內容")
            print("4. 演示歷史驗證功能")
            print("5. 演示趨勢分析功能")
            print("6. 演示未來預測功能")
            print("0. 退出")
            
            choice = input("\n請選擇 (0-6): ").strip()
            
            if choice == '0':
                print("👋 感謝使用，再見!")
                break
            elif choice == '1':
                demo_all_prompt_types()
            elif choice == '2':
                demo_create_sample_files()
            elif choice == '3':
                demo_prompt_templates()
            elif choice == '4':
                print("\n📊 歷史驗證功能演示")
                print("此功能可以:")
                print("• 對比影片內容與歷史數據")
                print("• 評估資訊的可信度")
                print("• 識別可能的偏見或錯誤")
                print("• 提供權威資料來源建議")
                input("\n按 Enter 繼續...")
            elif choice == '5':
                print("\n📈 趨勢分析功能演示")
                print("此功能可以:")
                print("• 識別當前和歷史趨勢")
                print("• 分析驅動因素")
                print("• 預測短中長期發展")
                print("• 評估機會與風險")
                input("\n按 Enter 繼續...")
            elif choice == '6':
                print("\n🚀 未來預測功能演示")
                print("此功能可以:")
                print("• 多情境建模預測")
                print("• 時間線分析")
                print("• 不確定性評估")
                print("• 策略建議制定")
                input("\n按 Enter 繼續...")
            else:
                print("❌ 無效選擇，請重新輸入")
    
    except KeyboardInterrupt:
        print("\n👋 程序已中斷")
    except Exception as e:
        print(f"❌ 程序執行錯誤: {e}")

if __name__ == "__main__":
    main() 