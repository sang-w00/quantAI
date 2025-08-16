import requests
import json
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self, ollama_host: str = "http://localhost:11434", model: str = "gpt-oss:20b"):
        self.ollama_host = ollama_host
        self.model = model
        self.session = requests.Session()
        
        # Ollama 서버 연결 확인
        self._check_ollama_connection()
    
    def _check_ollama_connection(self):
        """Ollama 서버 연결 상태 확인"""
        try:
            response = self.session.get(f"{self.ollama_host}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                if self.model not in model_names:
                    logger.warning(f"모델 {self.model}이 Ollama에 설치되어 있지 않습니다. 사용 가능한 모델: {model_names}")
                else:
                    logger.info(f"Ollama 연결 성공. 모델 {self.model} 사용 가능.")
            else:
                logger.error(f"Ollama 서버 연결 실패: {response.status_code}")
        except Exception as e:
            logger.error(f"Ollama 서버 연결 확인 실패: {e}")
    
    def analyze_sentiment(self, text: str, max_retries: int = 3) -> float:
        """
        텍스트의 감성을 분석하여 -1 ~ 1 사이의 값을 반환
        -1: 매우 부정적
        0: 중립
        1: 매우 긍정적
        """
        if not text or text.strip() == "":
            logger.info("📝 빈 텍스트 입력, 중립값(0.0) 반환")
            return 0.0
        
        # 텍스트 길이 로깅
        logger.info(f"📝 감성분석 입력 텍스트: {len(text)} 문자")
        logger.info(f"📝 텍스트 미리보기: {text[:200]}...")
        
        # 프롬프트 설계
        prompt = f"""
Analyze the sentiment of the following financial news text and provide a sentiment score.

Instructions:
- Return only a numerical score between -1.0 and 1.0
- -1.0 means very negative (bad for stock price)
- 0.0 means neutral
- 1.0 means very positive (good for stock price)
- Focus on financial implications for the company
- Consider earnings, revenue, partnerships, product launches, legal issues, etc.

Text to analyze:
{text[:2000]}  

Sentiment Score:"""
        
        logger.info(f"🤖 프롬프트 생성 완료 ({len(prompt)} 문자)")
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 감성분석 시도 {attempt + 1}/{max_retries}")
                
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # 낮은 온도로 일관된 결과
                        "top_p": 0.9,
                        "max_tokens": 10  # 짧은 답변만 필요
                    }
                }
                
                response = self.session.post(
                    f"{self.ollama_host}/api/generate",
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result.get('response', '').strip()
                    
                    logger.info(f"🤖 모델 원본 응답: '{answer}'")
                    
                    # 숫자 추출
                    sentiment_score = self._extract_sentiment_score(answer)
                    if sentiment_score is not None:
                        logger.info(f"✅ 감성분석 성공: {sentiment_score:.4f}")
                        logger.info(f"📊 분석 결과 해석: {self._interpret_score(sentiment_score)}")
                        return sentiment_score
                    else:
                        logger.warning(f"⚠️  감성 점수 추출 실패 (시도 {attempt + 1})")
                        logger.warning(f"   원본 응답: '{answer}'")
                else:
                    logger.warning(f"⚠️  Ollama API 오류 (시도 {attempt + 1}): HTTP {response.status_code}")
                
            except requests.exceptions.Timeout:
                logger.warning(f"⏰ Ollama API 타임아웃 (시도 {attempt + 1})")
            except Exception as e:
                logger.warning(f"❌ 감성 분석 오류 (시도 {attempt + 1}): {e}")
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"⏳ {wait_time}초 대기 후 재시도...")
                time.sleep(wait_time)  # 지수 백오프
        
        logger.error(f"❌ 감성 분석 최종 실패. 중립값(0.0) 반환")
        return 0.0
    
    def _interpret_score(self, score: float) -> str:
        """감성 점수를 텍스트로 해석"""
        if score > 0.7:
            return "매우 긍정적 (강한 매수 신호)"
        elif score > 0.3:
            return "긍정적 (매수 신호)"
        elif score > 0.1:
            return "약간 긍정적"
        elif score > -0.1:
            return "중립적"
        elif score > -0.3:
            return "약간 부정적"
        elif score > -0.7:
            return "부정적 (매도 신호)"
        else:
            return "매우 부정적 (강한 매도 신호)"
    
    def _extract_sentiment_score(self, text: str) -> Optional[float]:
        """텍스트에서 감성 점수를 추출"""
        import re
        
        # 숫자 패턴 찾기 (-1.0 ~ 1.0 범위)
        patterns = [
            r'(-?[01]\.?\d*)',  # -1.0, 0.5, 1.0 등
            r'(-?[01])',        # -1, 0, 1 등
            r'(-?\d+\.?\d*)'    # 일반적인 숫자
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    score = float(match)
                    # -1 ~ 1 범위로 클리핑
                    score = max(-1.0, min(1.0, score))
                    return score
                except ValueError:
                    continue
        
        # 텍스트 기반 매핑
        text_lower = text.lower()
        if any(word in text_lower for word in ['very positive', 'extremely positive', 'bullish']):
            return 1.0
        elif any(word in text_lower for word in ['positive', 'good', 'up']):
            return 0.5
        elif any(word in text_lower for word in ['neutral', 'mixed', 'unchanged']):
            return 0.0
        elif any(word in text_lower for word in ['negative', 'bad', 'down']):
            return -0.5
        elif any(word in text_lower for word in ['very negative', 'extremely negative', 'bearish']):
            return -1.0
        
        return None
    
    def batch_analyze_sentiment(self, texts: list, batch_size: int = 1) -> list:
        """여러 텍스트의 감성을 배치로 분석"""
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = []
            
            for text in batch:
                sentiment = self.analyze_sentiment(text)
                batch_results.append(sentiment)
                time.sleep(0.5)  # Rate limiting
            
            results.extend(batch_results)
            logger.info(f"배치 {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1} 완료")
        
        return results

if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    
    # 테스트
    test_texts = [
        "Apple reports record quarterly earnings, beating analyst expectations.",
        "Tesla faces regulatory investigation over autopilot safety concerns.",
        "Microsoft announces new cloud partnership deal worth billions."
    ]
    
    for text in test_texts:
        sentiment = analyzer.analyze_sentiment(text)
        print(f"텍스트: {text[:50]}...")
        print(f"감성 점수: {sentiment}\n")
