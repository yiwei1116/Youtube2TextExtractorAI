#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube 影片文字提取器
根據步驟化流程從 YouTube 影片中提取和處理文字內容
"""

import re
import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import requests

# 需要安裝的套件：
# pip install youtube-transcript-api google-api-python-client

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter
    from googleapiclient.discovery import build
except ImportError as e:
    print(f"請安裝必要套件: pip install youtube-transcript-api google-api-python-client")
    print(f"錯誤詳情: {e}")
    exit(1)

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YouTubeTextExtractor:
    """YouTube 影片文字提取器主類別"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化提取器
        
        Args:
            api_key: YouTube Data API v3 金鑰（可選）
        """
        self.api_key = api_key
        self.youtube_service = None
        
        if api_key:
            try:
                self.youtube_service = build('youtube', 'v3', developerKey=api_key)
                logger.info("YouTube API 服務初始化成功")
            except Exception as e:
                logger.warning(f"YouTube API 初始化失敗: {e}")
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        步驟 1: 從 YouTube URL 提取影片 ID
        
        Args:
            url: YouTube 影片 URL
            
        Returns:
            影片 ID 或 None
        """
        logger.info(f"提取影片 ID: {url}")
        
        # 處理不同格式的 YouTube URL
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/v/([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                logger.info(f"成功提取影片 ID: {video_id}")
                return video_id
        
        # 直接檢查是否已經是 video_id
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
            logger.info(f"輸入已是影片 ID: {url}")
            return url
        
        logger.error(f"無法從 URL 提取影片 ID: {url}")
        return None
    
    def check_captions_available(self, video_id: str) -> Tuple[bool, List[Dict]]:
        """
        步驟 2: 檢查影片是否有字幕
        
        Args:
            video_id: YouTube 影片 ID
            
        Returns:
            (是否有字幕, 可用字幕列表)
        """
        logger.info(f"檢查影片字幕可用性: {video_id}")
        
        try:
            # 嘗試獲取字幕列表
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            available_transcripts = []
            
            for transcript in transcript_list:
                transcript_info = {
                    'language': transcript.language,
                    'language_code': transcript.language_code,
                    'is_generated': transcript.is_generated,
                    'is_translatable': transcript.is_translatable
                }
                available_transcripts.append(transcript_info)
                logger.info(f"發現字幕: {transcript_info}")
            
            if available_transcripts:
                logger.info(f"影片有 {len(available_transcripts)} 個可用字幕")
                return True, available_transcripts
            else:
                logger.warning("影片沒有可用字幕")
                return False, []
                
        except Exception as e:
            logger.error(f"檢查字幕時發生錯誤: {e}")
            return False, []
    
    def extract_transcript(self, video_id: str, language_codes: List[str] = None) -> Optional[List[Dict]]:
        """
        步驟 3 & 4: 提取轉錄文字
        
        Args:
            video_id: YouTube 影片 ID
            language_codes: 偏好的語言代碼列表，預設為 ['zh-TW', 'zh', 'en']
            
        Returns:
            轉錄內容列表或 None
        """
        if language_codes is None:
            language_codes = ['zh-TW', 'zh-CN', 'zh', 'en']
        
        logger.info(f"提取影片轉錄: {video_id}")
        
        try:
            # 嘗試獲取指定語言的字幕
            for lang_code in language_codes:
                try:
                    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang_code])
                    logger.info(f"成功獲取 {lang_code} 字幕，共 {len(transcript)} 個片段")
                    return transcript
                except Exception as e:
                    logger.debug(f"無法獲取 {lang_code} 字幕: {e}")
                    continue
            
            # 如果指定語言都失敗，嘗試獲取任何可用的字幕
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                logger.info(f"獲取預設字幕，共 {len(transcript)} 個片段")
                return transcript
            except Exception as e:
                logger.error(f"無法獲取任何字幕: {e}")
                return None
                
        except Exception as e:
            logger.error(f"提取轉錄時發生錯誤: {e}")
            return None
    
    def clean_text(self, transcript: List[Dict], remove_timestamps: bool = True) -> str:
        """
        步驟 5: 清理轉錄文字
        
        Args:
            transcript: 轉錄內容列表
            remove_timestamps: 是否移除時間戳
            
        Returns:
            清理後的文字
        """
        logger.info("開始清理轉錄文字")
        
        if not transcript:
            return ""
        
        # 提取純文字
        texts = []
        for item in transcript:
            text = item.get('text', '').strip()
            if text:
                # 移除常見的轉錄標記
                text = re.sub(r'\[.*?\]', '', text)  # 移除 [音樂]、[掌聲] 等
                text = re.sub(r'\(.*?\)', '', text)  # 移除括號內容
                text = re.sub(r'<.*?>', '', text)   # 移除 HTML 標籤
                text = re.sub(r'\s+', ' ', text)    # 標準化空白
                text = text.strip()
                
                if text:
                    texts.append(text)
        
        # 合併文字
        full_text = ' '.join(texts)
        
        # 進一步清理
        full_text = re.sub(r'\s+', ' ', full_text)  # 多餘空白
        full_text = re.sub(r'([.!?])\s*([A-Z])', r'\1\n\2', full_text)  # 句子換行
        
        logger.info(f"文字清理完成，共 {len(full_text)} 個字符")
        return full_text.strip()
    
    def identify_speakers(self, transcript: List[Dict]) -> Dict[str, List[str]]:
        """
        步驟 6: 處理多位講者（簡單實現）
        
        Args:
            transcript: 轉錄內容列表
            
        Returns:
            按講者分組的文字字典
        """
        logger.info("嘗試識別多位講者")
        
        speakers = {'未知講者': []}
        
        for item in transcript:
            text = item.get('text', '').strip()
            
            # 簡單的講者識別模式
            speaker_patterns = [
                r'^([A-Za-z\u4e00-\u9fff]+)\s*[:：]\s*(.+)',  # "講者名: 內容"
                r'^\[([^\]]+)\]\s*(.+)',  # "[講者名] 內容"
            ]
            
            speaker_found = False
            for pattern in speaker_patterns:
                match = re.match(pattern, text)
                if match:
                    speaker = match.group(1).strip()
                    content = match.group(2).strip()
                    
                    if speaker not in speakers:
                        speakers[speaker] = []
                    speakers[speaker].append(content)
                    speaker_found = True
                    break
            
            if not speaker_found and text:
                speakers['未知講者'].append(text)
        
        # 移除空的講者
        speakers = {k: v for k, v in speakers.items() if v}
        
        logger.info(f"識別到 {len(speakers)} 位講者")
        return speakers
    
    def correct_transcription_errors(self, text: str) -> str:
        """
        步驟 7: 修正常見的轉錄錯誤
        
        Args:
            text: 原始文字
            
        Returns:
            修正後的文字
        """
        logger.info("修正轉錄錯誤")
        
        # 常見錯誤修正規則
        corrections = {
            # 數字修正
            r'\b一個\b': '1個',
            r'\b兩個\b': '2個',
            r'\b三個\b': '3個',
            
            # 標點符號修正
            r'\s+([,，.。!！?？;；:：])': r'\1',
            r'([,，.。!！?？;；:：])\s*([,，.。!！?？;；:：])': r'\1\2',
            
            # 空白修正
            r'\s+': ' ',
        }
        
        corrected_text = text
        for pattern, replacement in corrections.items():
            corrected_text = re.sub(pattern, replacement, corrected_text)
        
        logger.info("轉錄錯誤修正完成")
        return corrected_text.strip()
    
    def save_text(self, text: str, filename: str, format_type: str = 'txt', 
                  video_info: Dict = None, prompt_type: str = None) -> bool:
        """
        步驟 9: 儲存文字
        
        Args:
            text: 要儲存的文字
            filename: 檔案名稱
            format_type: 儲存格式 ('txt', 'json')
            video_info: 影片資訊字典
            prompt_type: Prompt類型，如果提供則會在文件中包含相應的prompt
            
        Returns:
            是否成功儲存
        """
        logger.info(f"儲存文字到 {filename}.{format_type}")
        
        try:
            if format_type.lower() == 'txt':
                content = ""
                
                # 如果有影片資訊，添加標題
                if video_info:
                    content += f"影片標題：{video_info.get('title', '未知影片')}\n"
                    content += f"影片 ID：{video_info.get('video_id', '')}\n"
                    content += f"影片 URL：https://www.youtube.com/watch?v={video_info.get('video_id', '')}\n"
                    content += "=" * 60 + "\n\n"
                
                # 如果有prompt類型，添加相應的prompt
                if prompt_type:
                    prompt_templates = self._get_prompt_templates()
                    if prompt_type in prompt_templates:
                        content += f"AI 分析 Prompt ({prompt_type})：\n"
                        content += "-" * 40 + "\n"
                        content += prompt_templates[prompt_type] + "\n\n"
                        content += "=" * 60 + "\n\n"
                
                # 添加文字稿標題
                content += "YouTube 影片完整文字稿：\n"
                content += "-" * 40 + "\n"
                content += text
                
                with open(f"{filename}.txt", 'w', encoding='utf-8') as f:
                    f.write(content)
                    
            elif format_type.lower() == 'json':
                import datetime
                data = {
                    'text': text,
                    'length': len(text),
                    'timestamp': str(datetime.datetime.now()),
                    'video_info': video_info,
                    'prompt_type': prompt_type
                }
                with open(f"{filename}.json", 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                logger.error(f"不支援的格式: {format_type}")
                return False
            
            logger.info(f"文字成功儲存到 {filename}.{format_type}")
            return True
            
        except Exception as e:
            logger.error(f"儲存文字時發生錯誤: {e}")
            return False
    
    def _get_prompt_templates(self) -> Dict[str, str]:
        """獲取不同類型的優化 prompt 模板"""
        return {
            'summary': """🎯 YouTube 影片智能摘要分析

請基於以下影片內容進行專業摘要分析：

📋 **摘要要求：**
1. **核心內容摘要** (3-5個主要觀點)
   - 每個觀點用1-2句話精確概括
   - 標註重要性等級 (⭐⭐⭐ 高重要性，⭐⭐ 中等，⭐ 一般)

2. **關鍵洞察與論證**
   - 影片提出的獨特觀點或創新想法
   - 主要論證邏輯和支持證據

3. **實用價值評估**
   - 對觀眾的實際應用價值
   - 可行性和操作性分析

4. **目標受眾識別**
   - 最適合的觀眾群體
   - 建議的知識背景要求

5. **內容品質評級**
   - 資訊準確度 (A/B/C/D)
   - 內容深度 (深入/中等/基礎)
   - 實用性評分 (1-10分)

請用繁體中文回覆，並使用清晰的結構化格式。""",

            'analysis': """🔍 YouTube 影片深度專業分析

請對以下影片內容進行全面的專業分析：

📊 **分析架構：**

1. **內容結構解析**
   - 影片邏輯架構和組織方式
   - 資訊層次和重點分佈
   - 敘述手法和表達技巧

2. **論證體系評估**
   - 主要論點識別和分類
   - 論證強度和說服力分析
   - 證據類型 (數據/案例/專家意見/理論依據)

3. **邏輯脈絡檢視**
   - 推理過程的合理性
   - 因果關係的準確性
   - 邏輯漏洞或薄弱環節

4. **多角度觀點對比**
   - 可能的反駁觀點
   - 不同立場的考量
   - 爭議點和討論空間

5. **實用性與可行性**
   - 實際應用的可能性
   - 實施難度和資源需求
   - 預期效果和風險評估

6. **建議改進方向**
   - 內容可以加強的地方
   - 建議的後續深入研究
   - 實踐行動計劃

請用專業且客觀的角度進行分析，使用繁體中文回覆。""",

            'questions': """❓ YouTube 影片學習問題生成系統

基於以下影片內容，請生成多層次的學習問題：

📚 **問題設計架構：**

1. **基礎理解層 (5題)**
   - 事實性問題：測試基本資訊掌握
   - 概念性問題：檢驗重要概念理解
   - 標註答案可在影片中的大概時間位置

2. **分析思考層 (3題)**
   - 比較分析：不同觀點或方法的對比
   - 因果推理：原因結果關係的探討
   - 批判思考：優缺點和限制性分析

3. **應用實踐層 (2題)**
   - 情境應用：如何在實際情況中運用
   - 問題解決：面對相關挑戰時的策略

4. **創新延伸層 (2題)**
   - 假設推論：基於內容的進一步推測
   - 跨領域連結：與其他知識的關聯

5. **學習路徑建議**
   - 推薦的延伸閱讀或學習資源
   - 相關技能的發展建議
   - 實踐練習的具體方向

每個問題請標註：
- 🎯 難度等級 (初級/中級/高級)
- ⏰ 建議思考時間
- 💡 思考提示或關鍵字

請用繁體中文設計問題。""",

            'translation': """🌐 YouTube 影片多語言優化翻譯

請對以下影片文字稿進行專業的語言優化和翻譯：

📝 **翻譯優化流程：**

1. **原文語言識別與清理**
   - 識別主要語言和方言特色
   - 清理語音轉文字的常見錯誤
   - 標準化標點符號和格式

2. **繁體中文優化版本**
   - 提升語言流暢度和可讀性
   - 統一專業術語翻譯
   - 調整語句結構，符合繁體中文表達習慣
   - 添加適當的語氣詞和連接詞

3. **英文專業翻譯**
   - 準確傳達原意和語調
   - 使用恰當的英文表達方式
   - 保持專業術語的一致性
   - 考慮目標讀者的文化背景

4. **關鍵術語對照表**
   - 列出重要專業詞彙的中英對照
   - 提供術語的簡要解釋
   - 標註行業標準用法

5. **內容結構重組**
   - 按邏輯主題重新組織內容
   - 提取重點摘要
   - 製作簡潔的要點列表

6. **文化適應性調整**
   - 解釋文化特定的概念或例子
   - 提供在地化的類比或案例
   - 標註可能需要額外背景知識的部分

請確保翻譯的準確性、專業性和可讀性。""",

            'mindmap': """🧠 YouTube 影片心智圖結構設計

請為以下影片內容創建完整的心智圖結構：

🗺️ **心智圖設計原則：**

1. **中心主題確立**
   - 影片的核心概念 (放置於中心)
   - 主題的簡潔描述 (1-2個關鍵詞)

2. **主要分支架構 (3-7個主分支)**
   - 第一層：主要概念或章節
   - 使用不同顏色標記各分支
   - 每個分支用動詞或名詞短語表達

3. **次級節點展開 (每個主分支2-5個子節點)**
   - 第二層：具體要點或子概念
   - 包含重要的細節或例子
   - 使用關鍵詞而非完整句子

4. **關聯線條設計**
   - 標示分支間的相互關係
   - 用虛線表示間接關聯
   - 用箭頭表示因果關係或流程

5. **視覺元素建議**
   - 🎨 顏色編碼方案
   - 📊 圖示和符號建議
   - 📏 相對重要性的大小區分

6. **記憶輔助技巧**
   - 助記口訣或關鍵字聯想
   - 邏輯記憶順序建議
   - 複習要點提醒

7. **學習路徑指引**
   - 建議的學習順序 (1→2→3...)
   - 重點複習節點標記 ⭐
   - 延伸學習方向建議

請用層次分明的結構化格式呈現，便於製作實際的心智圖。""",

            'historical_verification': """📊 YouTube 影片歷史數據驗證分析

請基於影片內容進行歷史數據驗證和事實核查：

🔍 **驗證分析架構：**

1. **事實核查層面**
   - 識別影片中的具體數據、統計資料和事實聲明
   - 標註需要驗證的關鍵信息
   - 評估資訊的可信度等級 (高/中/低)

2. **歷史趨勢對比**
   - 將影片論點與歷史數據進行對比
   - 識別與過往趨勢的一致性或差異
   - 分析數據的時效性和相關性

3. **資料來源評估**
   - 評估影片引用的資料來源品質
   - 識別可能的偏見或局限性
   - 建議更權威或最新的資料來源

4. **數據可靠性分析**
   - 檢視統計方法的合理性
   - 識別可能的樣本偏差或錯誤
   - 評估數據解讀的準確性

5. **時間脈絡檢驗**
   - 分析論點在不同時期的適用性
   - 識別可能已過時的資訊
   - 評估持續有效性

6. **交叉驗證建議**
   - 建議查證的權威資料庫或機構
   - 提供相關的研究報告或學術文獻
   - 列出可以進一步核實的官方資源

7. **結論可信度評級**
   - 整體事實準確度評分 (A/B/C/D)
   - 標註高可信度的部分 ✅
   - 標註需要謹慎對待的部分 ⚠️
   - 標註可能有誤的部分 ❌

請以客觀、專業的態度進行驗證分析。""",

            'trend_analysis': """📈 YouTube 影片趨勢分析與預測

請對影片內容進行趨勢識別和發展方向分析：

🔮 **趨勢分析框架：**

1. **當前趨勢識別**
   - 影片反映的現有趨勢和模式
   - 趨勢的發展階段 (萌芽期/成長期/成熟期/衰退期)
   - 趨勢的影響範圍和深度

2. **歷史發展軌跡**
   - 追溯相關領域的歷史發展
   - 識別重要的轉折點和里程碑
   - 分析週期性模式或規律

3. **驅動因素分析**
   - 技術進步的推動作用
   - 社會需求的變化
   - 政策環境的影響
   - 經濟因素的作用

4. **未來發展預測**
   - 短期發展預測 (1-2年)
   - 中期趨勢展望 (3-5年)
   - 長期前景分析 (5-10年)

5. **機會與風險評估**
   - 潛在的發展機會
   - 可能面臨的挑戰和風險
   - 不確定性因素分析

6. **影響因子監測**
   - 需要持續關注的關鍵指標
   - 可能改變趨勢的重要因素
   - 預警信號和轉折點

7. **策略建議**
   - 個人或組織的應對策略
   - 投資或發展建議
   - 風險規避措施

請基於數據和邏輯進行分析，提供具體且可行的洞察。""",

            'future_prediction': """🚀 YouTube 影片未來預測分析

基於影片內容，請進行系統性的未來預測分析：

🔭 **預測分析體系：**

1. **基準現狀評估**
   - 當前狀況的全面描述
   - 關鍵指標的基準值
   - 影響因素的權重分析

2. **情境建模預測**
   - **樂觀情境** 🌟
     * 最理想發展條件下的可能結果
     * 實現機率評估 (%)
     * 關鍵成功因素

   - **基準情境** 📊
     * 基於現有趨勢的合理預期
     * 最可能的發展路徑
     * 預期時間框架

   - **悲觀情境** ⚠️
     * 面臨重大挑戰時的可能後果
     * 風險因素和阻礙
     * 應對和緩解策略

3. **時間線預測**
   - **近期 (6個月-1年)**
     * 確定性較高的變化
     * 可觀察的早期指標

   - **中期 (1-3年)**
     * 中等確定性的發展
     * 需要監測的關鍵節點

   - **遠期 (3-10年)**
     * 可能性範圍較廣的變化
     * 顛覆性因素的潛在影響

4. **影響評估矩陣**
   - 對不同利害關係人的影響程度
   - 社會、經濟、技術層面的衝擊
   - 正面和負面效應的平衡

5. **不確定性分析**
   - 預測的可信度區間
   - 主要的不確定性來源
   - 可能改變預測的關鍵因素

6. **監測指標設計**
   - 追蹤預測準確性的關鍵指標
   - 早期預警信號
   - 修正預測的觸發條件

7. **行動建議**
   - 基於預測的戰略規劃建議
   - 風險管理和機會把握策略
   - 適應性調整的準備方案

8. **預測更新機制**
   - 定期重新評估的時間點
   - 新資訊整合的方法
   - 預測模型的持續優化

⚠️ **重要聲明：**
此預測基於當前可得資訊，實際發展可能受到不可預見因素影響。
建議將此作為參考工具，並結合最新資訊持續更新判斷。

請提供邏輯清晰、證據充分的預測分析。""",

            'industry_insight': """🏢 YouTube 影片行業洞察分析

請從行業專業角度深度解析影片內容：

💼 **行業分析維度：**

1. **行業定位分析**
   - 影片涉及的主要行業領域
   - 在產業鏈中的位置和角色
   - 與其他行業的關聯性

2. **市場環境評估**
   - 目標市場的規模和特徵
   - 競爭格局和主要參與者
   - 市場成熟度和發展潛力

3. **商業模式解析**
   - 價值創造和傳遞機制
   - 收益模式和盈利點
   - 成本結構和效率分析

4. **技術創新影響**
   - 相關技術的發展水平
   - 技術創新對行業的改變
   - 未來技術趨勢的潛在衝擊

5. **政策法規環境**
   - 相關政策的支持或限制
   - 法規變化的影響評估
   - 合規要求和挑戰

6. **投資與財務分析**
   - 行業投資熱點和資金流向
   - 估值水平和投資回報
   - 財務風險和機會

7. **人才與資源需求**
   - 關鍵人才的需求和供給
   - 核心資源的稀缺性
   - 能力建設的重點方向

8. **策略建議**
   - 進入策略和時機選擇
   - 競爭優勢的建立方式
   - 風險管控和機會把握

請從專業投資者或行業專家的角度提供深度洞察。""",

            'fact_check': """✅ YouTube 影片事實核查報告

請對影片中的關鍵聲明進行系統性事實核查：

🔍 **事實核查流程：**

1. **聲明識別與分類**
   - 提取影片中的具體事實聲明
   - 分類：數據/統計/歷史事件/科學論述/引用
   - 標註聲明的重要性級別

2. **核查結果評級**
   - ✅ **完全正確**：經權威來源證實
   - ⚠️ **部分正確**：基本正確但有細節偏差
   - ❓ **需要查證**：無法確認或來源不明
   - ❌ **明確錯誤**：與權威資料不符
   - 🔄 **過時資訊**：曾經正確但已過期

3. **證據來源評估**
   - 一手資料：官方統計、研究報告、政府數據
   - 二手資料：新聞報導、專業媒體、學術文獻
   - 權威機構：WHO、聯合國、央行、知名研究機構
   - 來源可信度評分 (A+/A/B/C/D)

4. **數據準確性檢驗**
   - 數字的精確性和時效性
   - 統計方法的合理性
   - 樣本代表性和偏差分析
   - 資料解讀的客觀性

5. **脈絡完整性評估**
   - 是否存在斷章取義
   - 重要脈絡資訊的遺漏
   - 偏見或傾向性表達

6. **更正建議**
   - 錯誤資訊的正確版本
   - 補充缺失的重要資訊
   - 更權威的資料來源

7. **總體可信度評估**
   - 整體事實準確度 (1-10分)
   - 主要可信部分總結
   - 需要質疑的部分提醒

請保持客觀中立，基於事實進行核查。"""
        }
    
    def create_ai_ready_file(self, video_url: str, prompt_type: str = 'summary', 
                           output_dir: str = "ai_uploads") -> Optional[str]:
        """
        創建準備上傳到 AI 的文件
        
        Args:
            video_url: YouTube 影片 URL
            prompt_type: Prompt 類型
            output_dir: 輸出目錄
            
        Returns:
            生成的文件路徑或 None
        """
        logger.info(f"創建 AI 準備文件: {video_url}, prompt_type: {prompt_type}")
        
        # 確保輸出目錄存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 處理影片
        result = self.process_video(video_url)
        
        if not result['success']:
            logger.error(f"影片處理失敗: {result.get('error')}")
            return None
        
        # 準備影片資訊
        video_info = {
            'video_id': result['video_id'],
            'title': f"YouTube Video {result['video_id']}",
            'url': f"https://www.youtube.com/watch?v={result['video_id']}"
        }
        
        # 如果有 YouTube API，獲取更詳細的影片資訊
        if self.youtube_service:
            try:
                video_response = self.youtube_service.videos().list(
                    part='snippet,statistics',
                    id=result['video_id']
                ).execute()
                
                if video_response['items']:
                    snippet = video_response['items'][0]['snippet']
                    statistics = video_response['items'][0]['statistics']
                    
                    video_info.update({
                        'title': snippet.get('title', video_info['title']),
                        'description': snippet.get('description', ''),
                        'channel_title': snippet.get('channelTitle', ''),
                        'published_at': snippet.get('publishedAt', ''),
                        'view_count': statistics.get('viewCount', ''),
                        'like_count': statistics.get('likeCount', ''),
                        'comment_count': statistics.get('commentCount', '')
                    })
            except Exception as e:
                logger.warning(f"無法獲取影片詳細資訊: {e}")
        
        # 生成文件名
        safe_title = re.sub(r'[^\w\s-]', '', video_info['title'][:50])
        safe_title = re.sub(r'[-\s]+', '-', safe_title)
        filename = f"{output_dir}/{result['video_id']}_{prompt_type}_{safe_title}"
        
        # 儲存文件
        if self.save_text(result['text'], filename, 'txt', video_info, prompt_type):
            file_path = f"{filename}.txt"
            logger.info(f"AI 準備文件已創建: {file_path}")
            return file_path
        
        return None
    
    def get_available_prompt_types(self) -> Dict[str, Dict[str, str]]:
        """
        獲取所有可用的 Prompt 類型及其詳細說明
        
        Returns:
            包含 prompt 類型資訊的字典
        """
        return {
            'summary': {
                'name': '📝 智能摘要分析',
                'description': '專業摘要分析，包含核心觀點、實用價值評估和內容品質評級',
                'suitable_for': '快速了解影片重點、學習筆記整理、內容評估',
                'output_focus': '結構化摘要、重要性分級、實用建議'
            },
            'analysis': {
                'name': '🔍 深度專業分析', 
                'description': '全面的專業分析，包含論證體系、邏輯檢視和多角度對比',
                'suitable_for': '學術研究、批判性思考、專業評估',
                'output_focus': '邏輯架構、論證強度、改進建議'
            },
            'questions': {
                'name': '❓ 學習問題生成',
                'description': '多層次學習問題設計，從基礎理解到創新延伸',
                'suitable_for': '教學設計、自主學習、知識檢測',
                'output_focus': '分層問題、學習路徑、思考提示'
            },
            'translation': {
                'name': '🌐 多語言優化翻譯',
                'description': '專業語言優化和翻譯，包含術語對照和文化適應',
                'suitable_for': '跨語言學習、內容本地化、專業翻譯',
                'output_focus': '語言優化、術語對照、文化調整'
            },
            'mindmap': {
                'name': '🧠 心智圖結構設計',
                'description': '完整心智圖結構創建，包含視覺元素和記憶技巧',
                'suitable_for': '知識整理、記憶強化、概念關聯',
                'output_focus': '結構化布局、視覺設計、學習路徑'
            },
            'historical_verification': {
                'name': '📊 歷史數據驗證',
                'description': '基於歷史數據的事實核查和可信度評估',
                'suitable_for': '事實核查、資料驗證、可信度評估',
                'output_focus': '數據對比、來源評估、可信度分級'
            },
            'trend_analysis': {
                'name': '📈 趨勢分析預測',
                'description': '趨勢識別和發展方向分析，包含機會風險評估',
                'suitable_for': '市場分析、投資決策、策略規劃',
                'output_focus': '趨勢識別、發展預測、策略建議'
            },
            'future_prediction': {
                'name': '🚀 未來預測分析',
                'description': '系統性未來預測，包含多情境建模和時間線分析',
                'suitable_for': '戰略規劃、風險管理、決策支持',
                'output_focus': '情境建模、時間線預測、行動建議'
            },
            'industry_insight': {
                'name': '🏢 行業洞察分析',
                'description': '專業行業角度深度解析，包含市場環境和商業模式',
                'suitable_for': '投資分析、商業決策、行業研究',
                'output_focus': '行業定位、市場分析、投資建議'
            },
            'fact_check': {
                'name': '✅ 事實核查報告',
                'description': '系統性事實核查，包含聲明分類和證據評估',
                'suitable_for': '資訊驗證、新聞核查、學術研究',
                'output_focus': '事實驗證、來源評估、可信度評級'
            }
        }
    
    def display_prompt_types_menu(self) -> str:
        """
        顯示 Prompt 類型選擇菜單
        
        Returns:
            用戶選擇的 prompt 類型
        """
        prompt_types = self.get_available_prompt_types()
        
        print("\n🎯 請選擇 AI 分析類型:")
        print("=" * 80)
        
        type_mapping = {}
        counter = 1
        
        for key, info in prompt_types.items():
            type_mapping[str(counter)] = key
            print(f"{counter:2d}. {info['name']}")
            print(f"    📋 {info['description']}")
            print(f"    🎯 適用場景: {info['suitable_for']}")
            print(f"    📊 分析重點: {info['output_focus']}")
            print()
            counter += 1
        
        print("=" * 80)
        
        while True:
            choice = input(f"請選擇分析類型 (1-{len(prompt_types)}): ").strip()
            
            if choice in type_mapping:
                selected_type = type_mapping[choice]
                selected_info = prompt_types[selected_type]
                print(f"\n✅ 已選擇: {selected_info['name']}")
                print(f"📝 說明: {selected_info['description']}")
                return selected_type
            else:
                print("❌ 無效選擇，請重新輸入")
    
    def analyze_text(self, text: str) -> Dict:
        """
        步驟 10: 基本文字分析
        
        Args:
            text: 要分析的文字
            
        Returns:
            分析結果字典
        """
        logger.info("進行文字分析")
        
        # 基本統計
        word_count = len(text.split())
        char_count = len(text)
        char_count_no_spaces = len(text.replace(' ', ''))
        
        # 句子數量
        sentences = re.split(r'[.!?。！？]', text)
        sentence_count = len([s for s in sentences if s.strip()])
        
        # 段落數量
        paragraphs = text.split('\n')
        paragraph_count = len([p for p in paragraphs if p.strip()])
        
        # 常用詞分析（簡單實現）
        words = re.findall(r'\b\w+\b', text.lower())
        word_freq = {}
        for word in words:
            if len(word) > 1:  # 忽略單字符
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 取前10個最常用詞
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        analysis = {
            'word_count': word_count,
            'character_count': char_count,
            'character_count_no_spaces': char_count_no_spaces,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count,
            'top_words': top_words,
            'avg_words_per_sentence': round(word_count / sentence_count, 2) if sentence_count > 0 else 0
        }
        
        logger.info("文字分析完成")
        return analysis
    
    def process_video(self, video_url: str, output_filename: str = None, 
                     language_codes: List[str] = None) -> Dict:
        """
        完整處理流程：從 URL 到最終文字
        
        Args:
            video_url: YouTube 影片 URL 或 ID
            output_filename: 輸出檔名（可選）
            language_codes: 偏好語言代碼
            
        Returns:
            處理結果字典
        """
        result = {
            'success': False,
            'video_id': None,
            'captions_available': False,
            'text': '',
            'speakers': {},
            'analysis': {},
            'filename': None
        }
        
        try:
            # 步驟 1: 提取影片 ID
            video_id = self.extract_video_id(video_url)
            if not video_id:
                result['error'] = '無法提取影片 ID'
                return result
            
            result['video_id'] = video_id
            
            # 步驟 2: 檢查字幕
            has_captions, available_captions = self.check_captions_available(video_id)
            result['captions_available'] = has_captions
            result['available_captions'] = available_captions
            
            if not has_captions:
                result['error'] = '影片沒有可用字幕'
                return result
            
            # 步驟 3-4: 提取轉錄
            transcript = self.extract_transcript(video_id, language_codes)
            if not transcript:
                result['error'] = '無法提取轉錄內容'
                return result
            
            # 步驟 5: 清理文字
            clean_text = self.clean_text(transcript)
            
            # 步驟 6: 識別講者
            speakers = self.identify_speakers(transcript)
            result['speakers'] = speakers
            
            # 步驟 7: 修正錯誤
            corrected_text = self.correct_transcription_errors(clean_text)
            result['text'] = corrected_text
            
            # 步驟 9: 儲存文字
            if output_filename:
                if self.save_text(corrected_text, output_filename):
                    result['filename'] = f"{output_filename}.txt"
            
            # 步驟 10: 分析文字
            analysis = self.analyze_text(corrected_text)
            result['analysis'] = analysis
            
            result['success'] = True
            logger.info("影片處理完成")
            
        except Exception as e:
            logger.error(f"處理影片時發生錯誤: {e}")
            result['error'] = str(e)
        
        return result

def main():
    """主程序示例"""
    print("YouTube 影片文字提取器")
    print("=" * 50)
    
    # 初始化提取器
    # 如果有 YouTube API 金鑰，可以在此處設定
    extractor = YouTubeTextExtractor()
    
    # 輸入影片 URL 或 ID
    video_input = input("請輸入 YouTube 影片 URL 或 ID: ").strip()
    if not video_input:
        print("請提供有效的 YouTube 影片 URL 或 ID")
        return
    
    # 設定輸出檔名
    output_name = input("請輸入輸出檔名（不含副檔名，留空則不儲存）: ").strip()
    if not output_name:
        output_name = None
    
    # 處理影片
    print("\n開始處理影片...")
    result = extractor.process_video(video_input, output_name)
    
    # 顯示結果
    print("\n" + "=" * 50)
    if result['success']:
        print(f"✅ 處理成功！")
        print(f"影片 ID: {result['video_id']}")
        print(f"字幕可用: {'是' if result['captions_available'] else '否'}")
        
        if result['text']:
            print(f"\n📝 提取的文字長度: {len(result['text'])} 字符")
            print(f"前100字符預覽:")
            print(result['text'][:100] + "..." if len(result['text']) > 100 else result['text'])
        
        if result['speakers'] and len(result['speakers']) > 1:
            print(f"\n👥 識別到 {len(result['speakers'])} 位講者:")
            for speaker in result['speakers']:
                print(f"  - {speaker}")
        
        if result['analysis']:
            analysis = result['analysis']
            print(f"\n📊 文字分析:")
            print(f"  詞數: {analysis['word_count']}")
            print(f"  字符數: {analysis['character_count']}")
            print(f"  句數: {analysis['sentence_count']}")
            print(f"  段落數: {analysis['paragraph_count']}")
        
        if result.get('filename'):
            print(f"\n💾 文字已儲存至: {result['filename']}")
        
    else:
        print(f"❌ 處理失敗: {result.get('error', '未知錯誤')}")
    
    print("\n程序執行完成。")

if __name__ == "__main__":
    import datetime
    main()