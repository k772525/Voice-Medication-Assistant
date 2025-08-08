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
            
            # 生成 AI 分析
            insights = self._generate_health_insights(processed_data, target_person)
            scores = self._calculate_health_scores(processed_data)
            recommendations = self._generate_recommendations(processed_data, target_person)
            
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
            
            prompt = f"""
你是一位專業的健康分析師。請分析以下健康數據，為 {target_person} 提供專業的健康洞察。

健康數據摘要：
{json.dumps(data_summary, ensure_ascii=False, indent=2)}

請生成 3-5 個健康洞察，每個洞察包含：
1. type: 洞察類型 (trend/warning/improvement/stable/risk/normal)
2. message: 洞察內容 (繁體中文，簡潔明瞭)
3. trend: 趨勢資訊 (如果適用)
   - direction: up/down/stable
   - description: 趨勢描述

請以 JSON 格式回傳：
[
  {{
    "type": "trend",
    "message": "您的血壓在過去一週呈現上升趨勢",
    "trend": {{
      "direction": "up",
      "description": "較前期上升 5%"
    }}
  }}
]

注意：
- 訊息要具體且有建設性
- 避免過於技術性的術語
- 重點關注異常值和趨勢變化
- 如果數據正常，也要給予正面回饋
"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=1024,
                )
            )
            
            if response.text:
                clean_text = response.text.strip()
                if clean_text.startswith('```json'):
                    clean_text = clean_text[7:]
                if clean_text.endswith('```'):
                    clean_text = clean_text[:-3]
                
                insights = json.loads(clean_text.strip())
                return insights if isinstance(insights, list) else []
            
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
            
            prompt = f"""
你是一位專業的健康顧問。請根據以下健康數據，為 {target_person} 提供個人化的健康建議。

健康數據摘要：
{json.dumps(data_summary, ensure_ascii=False, indent=2)}

請生成 2-4 個具體的健康建議，每個建議包含：
1. title: 建議標題 (簡潔明瞭)
2. content: 建議內容 (具體可行的建議)
3. priority: 優先級 (high/medium/low)

請以 JSON 格式回傳：
[
  {{
    "title": "控制血壓",
    "content": "建議減少鹽分攝取，每日鹽分不超過6克，多食用新鮮蔬果，並保持規律運動。",
    "priority": "high"
  }}
]

注意：
- 建議要具體且可執行
- 根據數據異常情況設定優先級
- 避免過於醫療化的建議
- 重點關注生活方式改善
"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=1024,
                )
            )
            
            if response.text:
                clean_text = response.text.strip()
                if clean_text.startswith('```json'):
                    clean_text = clean_text[7:]
                if clean_text.endswith('```'):
                    clean_text = clean_text[:-3]
                
                recommendations = json.loads(clean_text.strip())
                return recommendations if isinstance(recommendations, list) else []
            
        except Exception as e:
            current_app.logger.error(f"生成健康建議失敗: {e}")
        
        # 回退到基本建議
        return self._generate_basic_recommendations(processed_data)
    
    def _create_data_summary(self, processed_data: Dict) -> Dict:
        """創建數據摘要"""
        summary = {
            'data_points': 0,
            'latest_values': {},
            'trends': processed_data.get('trends', {}),
            'abnormal_readings': []
        }
        
        # 最新數值
        for metric in ['weight', 'blood_sugar', 'temperature', 'blood_oxygen']:
            data = processed_data.get(metric, [])
            if data:
                summary['latest_values'][metric] = data[-1]['value']
                summary['data_points'] += len(data)
        
        # 血壓
        bp_data = processed_data.get('blood_pressure', [])
        if bp_data:
            latest_bp = bp_data[-1]
            summary['latest_values']['blood_pressure'] = f"{latest_bp['systolic']}/{latest_bp['diastolic']}"
            summary['data_points'] += len(bp_data)
        
        # 異常讀數檢測
        if summary['latest_values'].get('blood_pressure'):
            bp = bp_data[-1]
            if bp['systolic'] > 140 or bp['diastolic'] > 90:
                summary['abnormal_readings'].append('血壓偏高')
        
        if summary['latest_values'].get('blood_sugar', 0) > 126:
            summary['abnormal_readings'].append('血糖偏高')
        
        if summary['latest_values'].get('temperature', 0) > 37.5:
            summary['abnormal_readings'].append('體溫偏高')
        
        if summary['latest_values'].get('blood_oxygen', 100) < 95:
            summary['abnormal_readings'].append('血氧偏低')
        
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