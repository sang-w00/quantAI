import os
import requests
from datetime import datetime, timedelta, timezone
import time
from typing import List, Dict, Optional
import logging
import importlib

# Optional Polygon SDK (dynamic import to avoid hard dependency)
PolygonRESTClient = None
PolygonTickerNews = None

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsCollector:
    def __init__(self, polygon_api_key: Optional[str] = None):
        # Polygon Stocks News API
        self.polygon_api_key = polygon_api_key or os.getenv("POLYGON_API_KEY")
        self.polygon_base_url = "https://api.polygon.io/v2/reference/news"
        # Initialize SDK client if available
        self._polygon_client = None
        if self.polygon_api_key:
            try:
                polygon_mod = importlib.import_module('polygon')
                rest_client_cls = getattr(polygon_mod, 'RESTClient', None)
                if rest_client_cls:
                    global PolygonRESTClient
                    PolygonRESTClient = rest_client_cls
                    # Try to import TickerNews model
                    try:
                        models_mod = importlib.import_module('polygon.rest.models')
                        global PolygonTickerNews
                        PolygonTickerNews = getattr(models_mod, 'TickerNews', None)
                    except Exception:
                        PolygonTickerNews = None

                    self._polygon_client = PolygonRESTClient(self.polygon_api_key)
                    logger.info("Polygon SDK 클라이언트 사용")
            except Exception as e:
                logger.info(f"Polygon SDK 미사용(동적 임포트 실패 또는 미설치): {e}")

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # API 호출 제한 관리
        self.last_api_call = 0
        self.min_call_interval = 1.0  # 1초 간격

    @staticmethod
    def _to_rfc3339_z(dt: datetime) -> str:
        """Format datetime to RFC3339 (ISO8601) in UTC ending with 'Z'."""
        if dt.tzinfo is None:
            # Naive datetime as local time; convert to UTC
            try:
                offset_sec = -time.timezone if (time.daylight == 0) else -time.altzone
                local_tz = timezone(timedelta(seconds=offset_sec))
                dt = dt.replace(tzinfo=local_tz)
            except Exception:
                dt = dt.replace(tzinfo=timezone.utc)
        dt_utc = dt.astimezone(timezone.utc)
        return dt_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

    def _wait_for_rate_limit(self):
        """API 호출 간격 제한"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call

        if time_since_last_call < self.min_call_interval:
            wait_time = self.min_call_interval - time_since_last_call
            logger.info(f"⏳ API 호출 제한으로 {wait_time:.1f}초 대기")
            time.sleep(wait_time)

        self.last_api_call = time.time()

    def search_polygon(self, ticker: str, from_date: datetime, to_date: datetime, max_articles: int = 50) -> List[Dict]:
        """Polygon Stocks News API를 사용하여 뉴스 검색.

        우선 Polygon SDK가 설치되어 있으면 SDK를 사용하고,
        없으면 HTTP 요청으로 대체합니다.
        """
        self._wait_for_rate_limit()

        # Normalize and guard date range
        if from_date and to_date and from_date > to_date:
            from_date, to_date = to_date, from_date

        # Build RFC3339 strings in UTC
        gte = self._to_rfc3339_z(from_date) if from_date else None
        lte = self._to_rfc3339_z(to_date) if to_date else None

        if not self.polygon_api_key:
            logger.error("POLYGON_API_KEY가 설정되지 않았습니다. 환경변수 또는 생성자 인자로 제공하세요.")
            return []

        # Prefer SDK if available
        if self._polygon_client is not None:
            try:
                logger.info(
                    f"🔍 Polygon SDK 검색: '{ticker}' (기간: {gte or '-'} ~ {lte or '-'})"
                )
                items: List[Dict] = []

                # polygon-api-client는 제너레이터를 반환
                gen = self._polygon_client.list_ticker_news(
                    ticker=ticker,
                    published_utc_gte=gte,
                    published_utc_lte=lte,
                    order="desc",
                    sort="published_utc",
                    limit=min(max_articles, 1000),
                )
                count = 0
                for n in gen:
                    count += 1
                    # 모델 또는 dict 형태 모두 지원
                    if PolygonTickerNews is not None and isinstance(n, PolygonTickerNews):
                        published_date = None
                        try:
                            # SDK 모델의 published_utc는 datetime일 수 있음
                            published_date = (
                                n.published_utc if isinstance(n.published_utc, datetime)
                                else datetime.fromisoformat(str(n.published_utc).replace('Z', '+00:00'))
                            )
                        except Exception:
                            published_date = None

                        news_item = {
                            'title': getattr(n, 'title', '') or '',
                            'description': getattr(n, 'description', '') or '',
                            'content': None,
                            'link': getattr(n, 'article_url', '') or '',
                            'published_date': published_date,
                            'source': (getattr(getattr(n, 'publisher', None), 'name', None) or 'Unknown'),
                            'image': getattr(n, 'image_url', '') or '',
                        }
                    else:
                        # dict-like
                        pub_str = (n.get('published_utc') if isinstance(n, dict) else None)
                        published_date = None
                        if pub_str:
                            try:
                                published_date = datetime.fromisoformat(str(pub_str).replace('Z', '+00:00'))
                            except Exception:
                                published_date = None

                        publisher = (n.get('publisher') if isinstance(n, dict) else {}) or {}
                        news_item = {
                            'title': (n.get('title') if isinstance(n, dict) else '') or '',
                            'description': (n.get('description') if isinstance(n, dict) else '') or '',
                            'content': None,
                            'link': (n.get('article_url') if isinstance(n, dict) else '') or '',
                            'published_date': published_date,
                            'source': publisher.get('name', 'Unknown'),
                            'image': (n.get('image_url') if isinstance(n, dict) else '') or '',
                        }

                    if len(items) < max_articles:
                        items.append(news_item)
                    else:
                        break

                logger.info(f"📰 Polygon SDK: {len(items)}개 뉴스 발견 (원시 {count}개)")
                return items
            except Exception as e:
                logger.warning(f"Polygon SDK 호출 오류, HTTP로 대체: {e}")
                # Fall through to HTTP

        # HTTP fallback
        params = {
            'ticker': ticker,
            'order': 'desc',
            'sort': 'published_utc',
            'limit': min(max_articles, 1000),
            'apiKey': self.polygon_api_key,
        }
        if gte:
            params['published_utc.gte'] = gte
        if lte:
            params['published_utc.lte'] = lte

        try:
            logger.info(f"🔍 Polygon HTTP 검색: '{ticker}' (기간: {gte or '-'} ~ {lte or '-'})")
            response = requests.get(self.polygon_base_url, params=params, headers=self.headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                logger.info(f"📰 Polygon HTTP: {len(results)}개 뉴스 발견")

                news_items: List[Dict] = []
                for i, article in enumerate(results):
                    try:
                        published_date = None
                        pub_str = article.get('published_utc')
                        if pub_str:
                            published_date = datetime.fromisoformat(str(pub_str).replace('Z', '+00:00'))

                        publisher = article.get('publisher') or {}
                        news_item = {
                            'title': article.get('title', ''),
                            'description': article.get('description', ''),
                            'content': None,
                            'link': article.get('article_url', ''),
                            'published_date': published_date,
                            'source': publisher.get('name', 'Unknown'),
                            'image': article.get('image_url', ''),
                        }
                        news_items.append(news_item)

                        if i < 3:
                            logger.info(f"  📄 뉴스 {i+1}: {news_item['title'][:50]}...")
                            logger.info(f"      발행일: {published_date}")
                            logger.info(f"      출처: {news_item['source']}")
                    except Exception as e:
                        logger.warning(f"뉴스 항목 파싱 오류: {e}")
                        logger.warning(f"원본 데이터: {article}")
                        continue

                logger.info(f"✅ 총 {len(news_items)}개 뉴스 항목 파싱 완료")
                return news_items
            elif response.status_code == 403:
                logger.error("❌ Polygon API 인증 실패 - API 키를 확인하세요")
                return []
            elif response.status_code == 429:
                logger.warning("⚠️ Polygon API 호출 제한 초과 - 잠시 대기")
                time.sleep(60)
                return []
            else:
                logger.error(f"❌ Polygon API 오류: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Polygon HTTP 호출 오류: {e}")
            return []

    def collect_company_news(self, company_name: str, ticker: str, target_date: datetime) -> List[Dict]:
        """특정 회사의 특정 날짜 뉴스 수집 (Polygon API 사용)"""
        all_news: List[Dict] = []

        # 날짜 범위 설정 (당일 전체)
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        logger.info(f"📰 {ticker} 뉴스 수집 시작...")
        logger.info(f"📅 검색 기간: {start_date.strftime('%Y-%m-%d')} (당일만)")

        # Polygon은 티커 기반 검색 사용
        keywords = [ticker]

        # 각 키워드(티커)로 검색
        for i, keyword in enumerate(keywords, 1):
            try:
                logger.info(f"🔍 키워드 {i}: '{keyword}' 검색 중...")

                # Polygon API로 뉴스 검색 (정확한 일자 범위 전달)
                news_items = self.search_polygon(
                    ticker=keyword,
                    from_date=start_date,
                    to_date=end_date,
                    max_articles=100,
                )

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
        unique_news: List[Dict] = []

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
            sources: Dict[str, int] = {}
            for news in unique_news:
                source = news['source']
                sources[source] = sources.get(source, 0) + 1

            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  - {source}: {count}개")

        return unique_news

    def filter_news_by_date(self, news_items: List[Dict], target_date: datetime) -> List[Dict]:
        """특정 날짜(당일) 뉴스만 필터링"""
        # 정확히 당일만 포함
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        logger.info(f"📅 날짜 필터링 (당일만): {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        logger.info(f"📥 필터링 전 뉴스 수: {len(news_items)}")

        filtered_news: List[Dict] = []
        for i, news in enumerate(news_items):
            # 날짜가 없는 경우 포함 (최신 뉴스로 간주)
            if not news['published_date']:
                logger.info(f"  ⚠️  뉴스 {i+1}: 날짜 없음 -> 포함")
                filtered_news.append(news)
                continue

            # UTC 시간을 로컬 시간으로 변환 (필요시)
            pub_date = news['published_date']
            if pub_date.tzinfo:
                pub_date = pub_date.replace(tzinfo=None)

            # 날짜 비교 로깅
            is_in_range = start_date <= pub_date <= end_date

            # 처음 5개만 상세 로깅
            if i < 5:
                logger.info(f"  📰 뉴스 {i+1}: {pub_date.strftime('%Y-%m-%d')} -> {'포함' if is_in_range else '제외'}")

            if is_in_range:
                filtered_news.append(news)

        logger.info(f"📤 필터링 후 뉴스 수: {len(filtered_news)}")

        # 결과가 없어도 당일만 유지 (완화하지 않음)
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


if __name__ == "__main__":
    collector = NewsCollector(polygon_api_key="q96aIisakzHv_c7jRaoginkjRj8zGWu3")
    test_date = datetime(2024, 7, 15)
    print("=== Polygon Stocks News API 테스트 ===")
    news = collector.collect_company_news("Apple Inc.", "AAPL", test_date)
    print(f"수집된 뉴스 수: {len(news)}")
    if news:
        print("\n첫 번째 뉴스:")
        print(f"제목: {news[0]['title']}")
        print(f"설명: {news[0]['description'][:200]}...")
        print(f"출처: {news[0]['source']}")
        print(f"날짜: {news[0]['published_date']}")
