import requests
from datetime import datetime, timedelta
import time
from typing import List, Dict
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsCollector:
    def __init__(self, gnews_api_key: str = "44cc3fd97fb6417d55aeb8d962f7a831"):
        self.gnews_api_key = gnews_api_key
        self.gnews_base_url = "https://gnews.io/api/v4/search"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # API 호출 제한 관리
        self.last_api_call = 0
        self.min_call_interval = 1.0  # 1초 간격
        
    def _wait_for_rate_limit(self):
        """API 호출 간격 제한"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        
        if time_since_last_call < self.min_call_interval:
            wait_time = self.min_call_interval - time_since_last_call
            logger.info(f"⏳ API 호출 제한으로 {wait_time:.1f}초 대기")
            time.sleep(wait_time)
        
        self.last_api_call = time.time()
        
    def search_gnews(self, query: str, from_date: datetime, to_date: datetime, max_articles: int = 10) -> List[Dict]:
        """GNews API를 사용하여 뉴스 검색"""
        self._wait_for_rate_limit()
        
        # 날짜 형식 변환 (YYYY-MM-DD)
        from_str = from_date.strftime('%Y-%m-%d')
        to_str = to_date.strftime('%Y-%m-%d')
        
        # API 파라미터 설정
        params = {
            'q': query,
            'token': self.gnews_api_key,
            'lang': 'en',
            'country': 'us',
            'max': min(max_articles, 100),  # API 최대 100개 제한
            'from': from_str,
            'to': to_str,
            'sortby': 'relevance'
        }
        
        try:
            logger.info(f"🔍 GNews API 검색: '{query}' ({from_str} ~ {to_str})")
            
            response = requests.get(self.gnews_base_url, params=params, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                logger.info(f"📰 GNews API: {len(articles)}개 뉴스 발견")
                
                # 뉴스 데이터 변환
                news_items = []
                for article in articles:
                    try:
                        # 날짜 파싱
                        published_date = None
                        if 'publishedAt' in article:
                            published_date = datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00'))
                        
                        news_item = {
                            'title': article.get('title', ''),
                            'description': article.get('description', ''),
                            'content': article.get('content', ''),
                            'link': article.get('url', ''),
                            'published_date': published_date,
                            'source': article.get('source', {}).get('name', 'Unknown'),
                            'image': article.get('image', '')
                        }
                        news_items.append(news_item)
                        
                    except Exception as e:
                        logger.warning(f"뉴스 항목 파싱 오류: {e}")
                        continue
                
                return news_items
                
            elif response.status_code == 403:
                logger.error("❌ GNews API 인증 실패 - API 키를 확인하세요")
                return []
            elif response.status_code == 429:
                logger.warning("⚠️ GNews API 호출 제한 초과 - 잠시 대기")
                time.sleep(60)  # 1분 대기
                return []
            else:
                logger.error(f"❌ GNews API 오류: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"GNews API 호출 오류: {e}")
            return []
    
    def get_company_keywords(self, company_name: str, ticker: str) -> List[str]:
        """회사별 검색 키워드 생성"""
        keywords = [ticker]
        
        # 기본 회사명
        keywords.append(f'"{company_name}"')
        
        # 특별한 경우 처리
        special_mappings = {
            'AAPL': ['Apple Inc', 'iPhone', 'iPad', 'Mac'],
            'MSFT': ['Microsoft', 'Windows', 'Office', 'Azure'],
            'GOOGL': ['Google', 'Alphabet', 'YouTube', 'Android'],
            'GOOG': ['Google', 'Alphabet', 'YouTube', 'Android'],
            'META': ['Meta', 'Facebook', 'Instagram', 'WhatsApp'],
            'TSLA': ['Tesla', 'Elon Musk', 'electric vehicle'],
            'AMZN': ['Amazon', 'AWS', 'Jeff Bezos'],
            'NVDA': ['NVIDIA', 'GPU', 'graphics card', 'AI chip'],
            'NFLX': ['Netflix', 'streaming'],
            'AVGO': ['Broadcom']
        }
        
        if ticker in special_mappings:
            keywords.extend(special_mappings[ticker])
        
        return keywords

if __name__ == "__main__":
    collector = NewsCollector()
    test_date = datetime(2024, 7, 15)
    print("=== GNews API 테스트 ===")
    news = collector.collect_company_news("Apple Inc.", "AAPL", test_date)
    print(f"수집된 뉴스 수: {len(news)}")
    if news:
        print("\n첫 번째 뉴스:")
        print(f"제목: {news[0]['title']}")
        print(f"설명: {news[0]['description'][:200]}...")
        print(f"출처: {news[0]['source']}")
        print(f"날짜: {news[0]['published_date']}")
    
    def filter_news_by_company(self, news_items: List[Dict], company_name: str, ticker: str) -> List[Dict]:
        """회사명이나 티커가 포함된 뉴스만 필터링 (개선된 매칭)"""
        filtered_news = []
        
        # 검색 키워드 준비 (더 포괄적)
        keywords = [
            ticker.upper(),
            ticker.lower(),
            company_name.lower(),
            # 일반적인 회사명 변형들
            company_name.replace(' Inc.', '').replace(' Corporation', '').replace(' Corp.', '').replace(' Ltd.', '').lower(),
            company_name.split()[0].lower() if ' ' in company_name else company_name.lower()
        ]
        
        # 특별한 경우 처리
        special_mappings = {
            'AAPL': ['apple', 'iphone', 'ipad', 'mac'],
            'MSFT': ['microsoft', 'windows', 'office', 'azure'],
            'GOOGL': ['google', 'alphabet', 'youtube', 'android'],
            'GOOG': ['google', 'alphabet', 'youtube', 'android'],
            'META': ['meta', 'facebook', 'instagram', 'whatsapp'],
            'TSLA': ['tesla', 'elon musk', 'electric vehicle', 'ev'],
            'AMZN': ['amazon', 'aws', 'bezos'],
            'NVDA': ['nvidia', 'gpu', 'ai chip', 'graphics'],
            'NFLX': ['netflix', 'streaming'],
            'AVGO': ['broadcom']
        }
        
        if ticker in special_mappings:
            keywords.extend(special_mappings[ticker])
        
        for news in news_items:
            title_lower = news['title'].lower()
            desc_lower = news['description'].lower()
            combined_text = f"{title_lower} {desc_lower}"
            
            # 키워드 중 하나라도 포함되어 있으면 선택
            if any(keyword in combined_text for keyword in keywords):
                filtered_news.append(news)
        
        return filtered_news
    
    def filter_news_by_date(self, news_items: List[Dict], target_date: datetime) -> List[Dict]:
        """특정 날짜의 뉴스만 필터링"""
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        filtered_news = []
        for news in news_items:
            if news['published_date'] and start_date <= news['published_date'] <= end_date:
                filtered_news.append(news)
        
        return filtered_news
    
    def collect_company_news(self, company_name: str, ticker: str, target_date: datetime) -> List[Dict]:
        """특정 회사의 특정 날짜 뉴스 수집 (GNews API 사용)"""
        all_news = []
        
        # 날짜 범위 설정 (전후 1일씩 포함하여 3일 범위)
        start_date = target_date - timedelta(days=1)
        end_date = target_date + timedelta(days=1)
        
        logger.info(f"📰 {ticker} 뉴스 수집 시작...")
        logger.info(f"📅 검색 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        
        # 회사별 키워드 가져오기
        keywords = self.get_company_keywords(company_name, ticker)
        
        # 각 키워드로 검색
        for i, keyword in enumerate(keywords[:3], 1):  # 상위 3개 키워드만 사용
            try:
                logger.info(f"🔍 키워드 {i}: '{keyword}' 검색 중...")
                
                # GNews API로 뉴스 검색
                news_items = self.search_gnews(keyword, start_date, end_date, max_articles=20)
                
                if news_items:
                    # 대상 날짜 필터링
                    filtered_news = self.filter_news_by_date(news_items, target_date)
                    all_news.extend(filtered_news)
                    
                    logger.info(f"  ✅ '{keyword}': {len(filtered_news)}개 관련 뉴스")
                else:
                    logger.info(f"  ❌ '{keyword}': 뉴스 없음")
                
                # API 호출 제한 대기
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"키워드 '{keyword}' 검색 실패: {e}")
                continue
        
        # 중복 제거 (제목과 URL 기준)
        seen_items = set()
        unique_news = []
        
        for news in all_news:
            # 제목과 URL을 결합한 키 생성
            key = f"{news['title'].strip().lower()}_{news['link']}"
            
            if key not in seen_items and len(news['title'].strip()) > 10:
                seen_items.add(key)
                unique_news.append(news)
        
        logger.info(f"🎯 {ticker} ({target_date.strftime('%Y-%m-%d')}): 총 {len(unique_news)}개 유니크 뉴스 수집")
        
        # 수집된 뉴스 요약 로깅
        if unique_news:
            logger.info(f"📊 뉴스 출처 분포:")
            sources = {}
            for news in unique_news:
                source = news['source']
                sources[source] = sources.get(source, 0) + 1
            
            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  - {source}: {count}개")
        
        return unique_news
    
    def filter_news_by_date(self, news_items: List[Dict], target_date: datetime) -> List[Dict]:
        """특정 날짜의 뉴스만 필터링 (3일 범위)"""
        # 날짜 범위를 3일로 확대 (전날, 당일, 다음날)
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999) + timedelta(days=1)
        
        filtered_news = []
        for news in news_items:
            # 날짜가 없는 경우 포함 (최신 뉴스로 간주)
            if not news['published_date']:
                filtered_news.append(news)
                continue
            
            # UTC 시간을 로컬 시간으로 변환 (필요시)
            pub_date = news['published_date']
            if pub_date.tzinfo:
                pub_date = pub_date.replace(tzinfo=None)
            
            if start_date <= pub_date <= end_date:
                filtered_news.append(news)
        
        return filtered_news
    
    def get_news_text(self, news_items: List[Dict]) -> str:
        """뉴스 리스트를 하나의 텍스트로 결합"""
        if not news_items:
            return ""
        
        texts = []
        for news in news_items:
            # 제목, 설명, 내용을 모두 결합
            text_parts = []
            
            if news.get('title'):
                text_parts.append(news['title'])
            
            if news.get('description'):
                text_parts.append(news['description'])
            
            if news.get('content'):
                # content가 있으면 description 대신 사용
                text_parts.append(news['content'])
            
            # 텍스트 결합 및 정리
            text = '. '.join(text_parts)
            # 불필요한 공백 제거
            text = ' '.join(text.split())
            
            if len(text) > 50:  # 너무 짧은 텍스트 제외
                texts.append(text)
        
        combined_text = ' | '.join(texts)
        
        # 텍스트 길이 제한 (토큰 제한 고려)
        if len(combined_text) > 8000:
            combined_text = combined_text[:8000] + "..."
        
        return combined_text
    
    def get_news_text(self, news_items: List[Dict]) -> str:
        """뉴스 리스트를 하나의 텍스트로 결합"""
        if not news_items:
            return ""
        
        texts = []
        for news in news_items:
            # 제목과 설명을 결합
            text = f"{news['title']}. {news['description']}"
            # HTML 태그 제거
            text = BeautifulSoup(text, 'html.parser').get_text()
            # 불필요한 공백 제거
            text = ' '.join(text.split())
            texts.append(text)
        
        return ' '.join(texts)

if __name__ == "__main__":
    collector = NewsCollector()
    test_date = datetime(2024, 1, 15)
    news = collector.collect_company_news("Apple Inc.", "AAPL", test_date)
    print(f"수집된 뉴스 수: {len(news)}")
    if news:
        print("첫 번째 뉴스:")
        print(f"제목: {news[0]['title']}")
        print(f"설명: {news[0]['description'][:200]}...")
