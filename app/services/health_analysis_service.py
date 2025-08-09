"""
健康分析服務 - 使用 Gemini AI 進行健康數據分析
"""

import os
import json
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from flask import current_app


class HealthAnalysisService:
    """健康分析服務類"""
    
    def __init__(self):
        """初始化服務"""
        self.api_key = os.environ.get('GEMINI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.model = None
            current_app.logger.warning("未設定 GEMINI_API_KEY，AI 分析功能將無法使用")
    
    def analyze_health_data(self, user_id: str, target_person: str, health_data: List[Dict]) -> Dict[str, Any]:
        """
        分析健康數據並生成洞察、評分和建議
        
        Args:
            user_id: 用戶ID
            target_person: 目標人員
            health_data: 健康數據列表
            
        Returns:
            包含洞察、評分和建議的字典
        """
        try:
            if not self.model:
                return self._generate_fallback_analysis(health_data)
            
            # 預處理健康數據
            processed_data = self._preprocess_health_data(health_data)
            
            # 嘗試 AI 分析，如果失敗則使用增強基本分析
            try:
                insights = self._generate_health_insights(processed_data, target_person)
                recommendations = self._generate_recommendations(processed_data, target_person)
                current_app.logger.info("AI 分析成功完成")
            except Exception as ai_error:
                current_app.logger.warning(f"AI 分析失敗，使用增強基本分析: {ai_error}")
                insights = self._generate_enhanced_basic_insights(processed_data, target_person)
                recommendations = self._generate_enhanced_basic_recommendations(processed_data, target_person)
            
            scores = self._calculate_health_scores(processed_data)
            
            return {
                'insights': insights,
                'scores': scores,
                'recommendations': recommendations,
                'analysis_time': datetime.now().isoformat(),
                'data_points': len(health_data)
            }
            
        except Exception as e:
            current_app.logger.error(f"健康分析失敗: {e}")
            return self._generate_error_response(str(e))
    
    def _preprocess_health_data(self, health_data: List[Dict]) -> Dict[str, Any]:
        """預處理健康數據"""
        processed = {
            'weight': [],
            'blood_pressure': [],
            'blood_sugar': [],
            'temperature': [],
            'blood_oxygen': [],
            'recent_data': [],
            'trends': {}
        }
        
        # 按時間排序
        sorted_data = sorted(health_data, key=lambda x: x.get('record_time', ''))
        
        # 分類數據
        for record in sorted_data:
            record_time = record.get('record_time')
            
            if record.get('weight'):
                processed['weight'].append({
                    'value': float(record['weight']),
                    'time': record_time
                })
            
            if record.get('systolic_pressure') and record.get('diastolic_pressure'):
                processed['blood_pressure'].append({
                    'systolic': int(record['systolic_pressure']),
                    'diastolic': int(record['diastolic_pressure']),
                    'time': record_time
                })
            
            if record.get('blood_sugar'):
                processed['blood_sugar'].append({
                    'value': float(record['blood_sugar']),
                    'time': record_time
                })
            
            if record.get('temperature'):
                processed['temperature'].append({
                    'value': float(record['temperature']),
                    'time': record_time
                })
            
            if record.get('blood_oxygen'):
                processed['blood_oxygen'].append({
                    'value': float(record['blood_oxygen']),
                    'time': record_time
                })
        
        # 計算趨勢
        processed['trends'] = self._calculate_trends(processed)
        
        # 獲取最近7天的數據
        cutoff_date = datetime.now() - timedelta(days=7)
        processed['recent_data'] = [
            record for record in sorted_data 
            if datetime.fromisoformat(record.get('record_time', '').replace('Z', '+00:00')) > cutoff_date
        ]
        
        return processed
    
    def _calculate_trends(self, processed_data: Dict) -> Dict[str, str]:
        """計算各項指標的趨勢"""
        trends = {}
        
        for metric in ['weight', 'blood_sugar', 'temperature', 'blood_oxygen']:
            data = processed_data.get(metric, [])
            if len(data) >= 2:
                recent_values = [item['value'] for item in data[-3:]]  # 最近3次
                older_values = [item['value'] for item in data[-6:-3]] if len(data) >= 6 else [item['value'] for item in data[:-3]]
                
                if older_values:
                    recent_avg = statistics.mean(recent_values)
                    older_avg = statistics.mean(older_values)
                    
                    if recent_avg > older_avg * 1.05:
                        trends[metric] = 'up'
                    elif recent_avg < older_avg * 0.95:
                        trends[metric] = 'down'
                    else:
                        trends[metric] = 'stable'
                else:
                    trends[metric] = 'stable'
            else:
                trends[metric] = 'stable'
        
        # 血壓趨勢
        bp_data = processed_data.get('blood_pressure', [])
        if len(bp_data) >= 2:
            recent_systolic = [item['systolic'] for item in bp_data[-3:]]
            older_systolic = [item['systolic'] for item in bp_data[-6:-3]] if len(bp_data) >= 6 else [item['systolic'] for item in bp_data[:-3]]
            
            if older_systolic:
                recent_avg = statistics.mean(recent_systolic)
                older_avg = statistics.mean(older_systolic)
                
                if recent_avg > older_avg * 1.05:
                    trends['blood_pressure'] = 'up'
                elif recent_avg < older_avg * 0.95:
                    trends['blood_pressure'] = 'down'
                else:
                    trends['blood_pressure'] = 'stable'
            else:
                trends['blood_pressure'] = 'stable'
        else:
            trends['blood_pressure'] = 'stable'
        
        return trends
    
    def _generate_health_insights(self, processed_data: Dict, target_person: str) -> List[Dict]:
        """使用 AI 生成健康洞察"""
        try:
            # 準備數據摘要
            data_summary = self._create_data_summary(processed_data)
            
            # 準備完整的健康數據統計
            data_summary = self._create_data_summary(processed_data)
            total_points = data_summary.get('data_points', 0)
            statistics = data_summary.get('statistics', {})
            abnormal_counts = data_summary.get('abnormal_counts', {})
            
            # 構建詳細的健康數據分析
            analysis_details = []
            
            # 血壓分析
            if 'blood_pressure' in statistics:
                bp_stats = statistics['blood_pressure']
                bp_abnormal = abnormal_counts.get('blood_pressure', 0)
                analysis_details.append(f"血壓{bp_stats['count']}筆，平均{bp_stats['avg_systolic']:.0f}/{bp_stats['avg_diastolic']:.0f}，{bp_abnormal}次異常")
            
            # 其他指標分析
            for metric in ['weight', 'blood_sugar', 'temperature', 'blood_oxygen']:
                if metric in statistics:
                    stats = statistics[metric]
                    abnormal = abnormal_counts.get(metric, 0)
                    metric_name = {'weight': '體重', 'blood_sugar': '血糖', 'temperature': '體溫', 'blood_oxygen': '血氧'}[metric]
                    analysis_details.append(f"{metric_name}{stats['count']}筆，平均{stats['avg']:.1f}，{abnormal}次異常")
            
            health_analysis = f"總計{total_points}筆記錄。" + "；".join(analysis_details[:2])
            
            prompt = f"""健康數據完整分析：{health_analysis}

提供2個基於完整數據的觀察，JSON格式：
[
  {{"type": "trend", "message": "基於所有記錄的趨勢分析"}},
  {{"type": "normal", "message": "整體健康狀況綜合評估"}}
]

要求：每個觀察不超過30字，基於完整統計數據。"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    top_p=1.0,
                    top_k=1,
                    max_output_tokens=200,
                ),
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE"
                    }
                ]
            )
            
            # 嘗試多種方式獲取回應內容
            text_content = None
            
            # 方法1: 直接獲取 text 屬性
            try:
                if hasattr(response, 'text') and response.text:
                    text_content = response.text
                    current_app.logger.info("成功通過 response.text 獲取內容")
            except Exception as e:
                current_app.logger.debug(f"無法通過 response.text 獲取內容: {e}")
            
            # 方法2: 通過 candidates 獲取
            if not text_content and hasattr(response, 'candidates') and response.candidates:
                try:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    text_content = part.text
                                    current_app.logger.info("成功通過 candidates 獲取內容")
                                    break
                except Exception as e:
                    current_app.logger.debug(f"無法通過 candidates 獲取內容: {e}")
            
            # 處理獲取到的內容
            if text_content:
                try:
                    clean_text = text_content.strip()
                    if clean_text.startswith('```json'):
                        clean_text = clean_text[7:]
                    if clean_text.endswith('```'):
                        clean_text = clean_text[:-3]
                    
                    insights = json.loads(clean_text.strip())
                    if isinstance(insights, list) and len(insights) > 0:
                        current_app.logger.info(f"成功解析 AI 洞察: {len(insights)} 個")
                        return insights
                except Exception as parse_error:
                    current_app.logger.error(f"解析 AI 回應失敗: {parse_error}, 原始內容: {text_content[:200]}")
            
            # 檢查是否被安全過濾器阻擋
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'safety_ratings'):
                    for rating in candidate.safety_ratings:
                        if hasattr(rating, 'probability') and rating.probability.name in ['HIGH', 'MEDIUM']:
                            current_app.logger.warning(f"AI 回應被安全過濾器阻擋: {rating.category.name}")
                            break
            
            current_app.logger.warning("無法獲取有效的 AI 洞察回應，使用基本分析")
            
        except Exception as e:
            current_app.logger.error(f"生成健康洞察失敗: {e}")
        
        # 回退到基本分析
        return self._generate_basic_insights(processed_data)
    
    def _calculate_health_scores(self, processed_data: Dict) -> Dict[str, float]:
        """計算健康評分"""
        scores = {
            'overall': 0,
            'weight': 0,
            'bloodPressure': 0,
            'bloodSugar': 0,
            'temperature': 0,
            'bloodOxygen': 0
        }
        
        valid_scores = []
        
        # 體重評分
        weight_data = processed_data.get('weight', [])
        if weight_data:
            latest_weight = weight_data[-1]['value']
            # 簡化評分：假設正常範圍
            if 45 <= latest_weight <= 80:
                scores['weight'] = 85
            elif 40 <= latest_weight <= 90:
                scores['weight'] = 70
            else:
                scores['weight'] = 50
            valid_scores.append(scores['weight'])
        
        # 血壓評分
        bp_data = processed_data.get('blood_pressure', [])
        if bp_data:
            latest_bp = bp_data[-1]
            systolic = latest_bp['systolic']
            diastolic = latest_bp['diastolic']
            
            if systolic <= 120 and diastolic <= 80:
                scores['bloodPressure'] = 90
            elif systolic <= 130 and diastolic <= 85:
                scores['bloodPressure'] = 75
            elif systolic <= 140 and diastolic <= 90:
                scores['bloodPressure'] = 60
            else:
                scores['bloodPressure'] = 40
            valid_scores.append(scores['bloodPressure'])
        
        # 血糖評分
        sugar_data = processed_data.get('blood_sugar', [])
        if sugar_data:
            latest_sugar = sugar_data[-1]['value']
            if 70 <= latest_sugar <= 100:
                scores['bloodSugar'] = 90
            elif 100 <= latest_sugar <= 126:
                scores['bloodSugar'] = 70
            else:
                scores['bloodSugar'] = 50
            valid_scores.append(scores['bloodSugar'])
        
        # 體溫評分
        temp_data = processed_data.get('temperature', [])
        if temp_data:
            latest_temp = temp_data[-1]['value']
            if 36.1 <= latest_temp <= 37.2:
                scores['temperature'] = 90
            elif 35.5 <= latest_temp <= 38.0:
                scores['temperature'] = 70
            else:
                scores['temperature'] = 50
            valid_scores.append(scores['temperature'])
        
        # 血氧評分
        oxygen_data = processed_data.get('blood_oxygen', [])
        if oxygen_data:
            latest_oxygen = oxygen_data[-1]['value']
            if latest_oxygen >= 95:
                scores['bloodOxygen'] = 90
            elif latest_oxygen >= 90:
                scores['bloodOxygen'] = 70
            else:
                scores['bloodOxygen'] = 50
            valid_scores.append(scores['bloodOxygen'])
        
        # 計算總體評分
        if valid_scores:
            scores['overall'] = statistics.mean(valid_scores)
        else:
            scores['overall'] = 0
        
        return scores
    
    def _generate_recommendations(self, processed_data: Dict, target_person: str) -> List[Dict]:
        """生成個人化建議"""
        try:
            data_summary = self._create_data_summary(processed_data)
            
            # 基於完整統計數據提供建議
            data_summary = self._create_data_summary(processed_data)
            total_points = data_summary.get('data_points', 0)
            abnormal_counts = data_summary.get('abnormal_counts', {})
            statistics = data_summary.get('statistics', {})
            
            # 計算總異常次數
            total_abnormal = sum(abnormal_counts.values())
            
            # 構建統計摘要
            stats_summary = []
            for metric, stats in statistics.items():
                abnormal = abnormal_counts.get(metric, 0)
                if metric == 'blood_pressure':
                    stats_summary.append(f"血壓{stats['count']}筆({abnormal}次異常)")
                else:
                    metric_name = {'weight': '體重', 'blood_sugar': '血糖', 'temperature': '體溫', 'blood_oxygen': '血氧'}[metric]
                    stats_summary.append(f"{metric_name}{stats['count']}筆({abnormal}次異常)")
            
            summary_text = f"總計{total_points}筆，" + "，".join(stats_summary[:2])
            
            # 判斷優先級
            priority = "high" if total_abnormal > 0 else "medium"
            
            prompt = f"""健康管理建議：{summary_text}

提供2個基於完整數據的建議，JSON格式：
[
  {{"title": "健康監測", "content": "基於統計數據的監測建議", "priority": "{priority}"}},
  {{"title": "生活調整", "content": "根據異常模式的改善建議", "priority": "medium"}}
]

要求：每個建議內容不超過25字，基於完整數據分析。"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    top_p=1.0,
                    top_k=1,
                    max_output_tokens=400,  # 增加輸出長度限制
                ),
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE"
                    }
                ]
            )
            
            # 嘗試多種方式獲取回應內容
            text_content = None
            
            # 方法1: 直接獲取 text 屬性
            try:
                if hasattr(response, 'text') and response.text:
                    text_content = response.text
                    current_app.logger.info("成功通過 response.text 獲取建議內容")
            except Exception as e:
                current_app.logger.debug(f"無法通過 response.text 獲取建議內容: {e}")
            
            # 方法2: 通過 candidates 獲取
            if not text_content and hasattr(response, 'candidates') and response.candidates:
                try:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    text_content = part.text
                                    current_app.logger.info("成功通過 candidates 獲取建議內容")
                                    break
                except Exception as e:
                    current_app.logger.debug(f"無法通過 candidates 獲取建議內容: {e}")
            
            # 處理獲取到的內容
            if text_content:
                try:
                    clean_text = text_content.strip()
                    if clean_text.startswith('```json'):
                        clean_text = clean_text[7:]
                    if clean_text.endswith('```'):
                        clean_text = clean_text[:-3]
                    
                    recommendations = json.loads(clean_text.strip())
                    if isinstance(recommendations, list) and len(recommendations) > 0:
                        current_app.logger.info(f"成功解析 AI 建議: {len(recommendations)} 個")
                        return recommendations
                except Exception as parse_error:
                    current_app.logger.error(f"解析 AI 建議回應失敗: {parse_error}, 原始內容: {text_content[:200]}")
            
            current_app.logger.warning("無法獲取有效的 AI 建議回應，使用基本建議")
            
        except Exception as e:
            current_app.logger.error(f"生成健康建議失敗: {e}")
        
        # 回退到基本建議
        return self._generate_basic_recommendations(processed_data)
    
    def _create_data_summary(self, processed_data: Dict) -> Dict:
        """創建數據摘要 - 分析所有記錄而不只是最新一筆"""
        summary = {
            'data_points': 0,
            'latest_values': {},
            'all_values': {},  # 新增：儲存所有數值用於分析
            'statistics': {},  # 新增：統計數據
            'trends': processed_data.get('trends', {}),
            'abnormal_readings': [],
            'abnormal_counts': {}  # 新增：異常次數統計
        }
        
        # 計算總數據點數（所有類型的記錄總和）
        total_records = 0
        
        # 分析所有健康指標的完整數據
        for metric in ['weight', 'blood_sugar', 'temperature', 'blood_oxygen']:
            data = processed_data.get(metric, [])
            if data:
                # 最新數值
                summary['latest_values'][metric] = data[-1]['value']
                
                # 所有數值
                values = [record['value'] for record in data]
                summary['all_values'][metric] = values
                
                # 統計數據
                summary['statistics'][metric] = {
                    'count': len(values),
                    'avg': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values)
                }
                
                # 異常檢測
                abnormal_count = 0
                if metric == 'blood_sugar':
                    abnormal_count = sum(1 for v in values if v > 126)
                    if abnormal_count > 0:
                        summary['abnormal_readings'].append('血糖偏高')
                elif metric == 'temperature':
                    abnormal_count = sum(1 for v in values if v > 37.5)
                    if abnormal_count > 0:
                        summary['abnormal_readings'].append('體溫偏高')
                elif metric == 'blood_oxygen':
                    abnormal_count = sum(1 for v in values if v < 95)
                    if abnormal_count > 0:
                        summary['abnormal_readings'].append('血氧偏低')
                
                summary['abnormal_counts'][metric] = abnormal_count
                total_records += len(data)
        
        # 血壓完整分析
        bp_data = processed_data.get('blood_pressure', [])
        if bp_data:
            # 最新數值
            latest_bp = bp_data[-1]
            summary['latest_values']['blood_pressure'] = f"{latest_bp['systolic']}/{latest_bp['diastolic']}"
            
            # 所有數值
            systolic_values = [record['systolic'] for record in bp_data]
            diastolic_values = [record['diastolic'] for record in bp_data]
            summary['all_values']['blood_pressure'] = {
                'systolic': systolic_values,
                'diastolic': diastolic_values
            }
            
            # 統計數據
            summary['statistics']['blood_pressure'] = {
                'count': len(bp_data),
                'avg_systolic': sum(systolic_values) / len(systolic_values),
                'avg_diastolic': sum(diastolic_values) / len(diastolic_values),
                'min_systolic': min(systolic_values),
                'max_systolic': max(systolic_values),
                'min_diastolic': min(diastolic_values),
                'max_diastolic': max(diastolic_values)
            }
            
            # 異常檢測
            abnormal_count = sum(1 for s, d in zip(systolic_values, diastolic_values) if s > 140 or d > 90)
            if abnormal_count > 0:
                summary['abnormal_readings'].append('血壓偏高')
            summary['abnormal_counts']['blood_pressure'] = abnormal_count
            
            total_records += len(bp_data)
        
        summary['data_points'] = total_records
        
        return summary
    
    def _generate_basic_insights(self, processed_data: Dict) -> List[Dict]:
        """生成基本洞察（回退方案）"""
        insights = []
        trends = processed_data.get('trends', {})
        
        for metric, trend in trends.items():
            if trend == 'up':
                insights.append({
                    'type': 'trend',
                    'message': f'您的{self._get_metric_name(metric)}呈現上升趨勢',
                    'trend': {
                        'direction': 'up',
                        'description': '較前期有所上升'
                    }
                })
            elif trend == 'down':
                insights.append({
                    'type': 'improvement',
                    'message': f'您的{self._get_metric_name(metric)}呈現下降趨勢',
                    'trend': {
                        'direction': 'down',
                        'description': '較前期有所改善'
                    }
                })
        
        if not insights:
            insights.append({
                'type': 'normal',
                'message': '您的健康數據整體穩定，請繼續保持良好習慣'
            })
        
        return insights[:5]  # 最多5個洞察
    
    def _generate_basic_recommendations(self, processed_data: Dict) -> List[Dict]:
        """生成基本建議（回退方案）"""
        recommendations = [
            {
                'title': '規律運動',
                'content': '建議每週進行至少150分鐘的中等強度運動，如快走、游泳或騎自行車。',
                'priority': 'medium'
            },
            {
                'title': '均衡飲食',
                'content': '多攝取蔬菜水果，減少加工食品，控制鹽分和糖分攝取。',
                'priority': 'medium'
            },
            {
                'title': '定期監測',
                'content': '建議定期記錄健康數據，有助於及早發現健康變化。',
                'priority': 'low'
            }
        ]
        
        return recommendations
    
    def _get_metric_name(self, metric: str) -> str:
        """獲取指標中文名稱"""
        names = {
            'weight': '體重',
            'blood_pressure': '血壓',
            'blood_sugar': '血糖',
            'temperature': '體溫',
            'blood_oxygen': '血氧'
        }
        return names.get(metric, metric)
    
    def _generate_fallback_analysis(self, health_data: List[Dict]) -> Dict[str, Any]:
        """生成回退分析（當 AI 不可用時）"""
        return {
            'insights': [
                {
                    'type': 'normal',
                    'message': '您的健康數據已記錄，建議定期監測各項指標'
                }
            ],
            'scores': {
                'overall': 75,
                'weight': 75,
                'bloodPressure': 75,
                'bloodSugar': 75,
                'temperature': 75,
                'bloodOxygen': 75
            },
            'recommendations': [
                {
                    'title': '持續記錄',
                    'content': '建議持續記錄健康數據，以便追蹤健康狀況變化。',
                    'priority': 'medium'
                }
            ],
            'analysis_time': datetime.now().isoformat(),
            'data_points': len(health_data),
            'note': 'AI 分析服務暫時無法使用，顯示基本分析結果'
        }
    
    def _generate_error_response(self, error_message: str) -> Dict[str, Any]:
        """生成錯誤回應"""
        return {
            'insights': [
                {
                    'type': 'warning',
                    'message': 'AI 分析服務暫時無法使用，請稍後再試'
                }
            ],
            'scores': {
                'overall': 0,
                'weight': 0,
                'bloodPressure': 0,
                'bloodSugar': 0,
                'temperature': 0,
                'bloodOxygen': 0
            },
            'recommendations': [
                {
                    'title': '系統維護',
                    'content': '分析服務正在維護中，請稍後重新整理頁面。',
                    'priority': 'low'
                }
            ],
            'analysis_time': datetime.now().isoformat(),
            'data_points': 0,
            'error': error_message
        }