import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import logging
from typing import Dict, List
from tqdm import tqdm
import time
import subprocess
import holidays

from nasdaq100_companies import get_nasdaq100_companies
from news_collector import NewsCollector
from sentiment_analyzer import SentimentAnalyzer

def get_windows_host_ip():
    """WSL에서 Windows 호스트 IP 주소를 자동으로 찾는 함수"""
    try:
        result = subprocess.run(['ip', 'route', 'show'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'default' in line:
                parts = line.split()
                if len(parts) >= 3:
                    return parts[2]
    except Exception as e:
        logging.warning(f"Windows 호스트 IP 자동 감지 실패: {e}")
    
    # 기본값 반환
    return "172.19.144.1"

def get_windows_host_ip():
    """WSL에서 Windows 호스트 IP 주소를 자동으로 찾는 함수"""
    try:
        result = subprocess.run(['ip', 'route', 'show'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'default' in line:
                parts = line.split()
                if len(parts) >= 3:
                    return parts[2]
    except Exception as e:
        logging.warning(f"Windows 호스트 IP 자동 감지 실패: {e}")
    
    # 기본값 반환
    return "172.19.144.1"

def setup_result_directory(start_date: str, end_date: str) -> str:
    """결과 저장을 위한 디렉토리 구조 생성"""
    # 기간을 폴더명으로 사용 (YYYY-MM-DD_to_YYYY-MM-DD)
    period_folder = f"{start_date}_to_{end_date}"
    result_dir = os.path.join("results", period_folder)
    
    # 디렉토리 생성
    os.makedirs(result_dir, exist_ok=True)
    
    return result_dir

def setup_logging(result_dir: str):
    """로깅 설정 (결과 디렉토리에 로그 파일 저장)"""
    log_file = os.path.join(result_dir, "sentiment_analysis.log")
    
    # 기존 핸들러 제거
    logging.getLogger().handlers.clear()
    
    # 새로운 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

# 초기 로깅 설정 (임시)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockSentimentAnalyzer:
    def __init__(self, ollama_host: str = "http://localhost:11434", model: str = "gpt-oss:20b", result_dir: str = "."):
        self.news_collector = NewsCollector(polygon_api_key="q96aIisakzHv_c7jRaoginkjRj8zGWu3")
        self.sentiment_analyzer = SentimentAnalyzer(ollama_host, model)
        self.nasdaq100_symbols, self.company_names = get_nasdaq100_companies()
        self.result_dir = result_dir
        
        # 미국 공휴일 설정
        self.us_holidays = holidays.US()
        
    def is_business_day(self, date: datetime) -> bool:
        """영업일인지 확인 (주말 및 공휴일 제외)"""
        # 주말 확인 (토요일=5, 일요일=6)
        if date.weekday() >= 5:
            return False
        
        # 공휴일 확인
        if date.date() in self.us_holidays:
            return False
            
        return True
        
    def generate_date_range(self, start_date: str, end_date: str) -> List[datetime]:
        """날짜 범위 생성 (영업일만, 주말 및 공휴일 제외)"""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        dates = []
        current = start
        while current <= end:
            # 영업일만 추가
            if self.is_business_day(current):
                dates.append(current)
            current += timedelta(days=1)
        
        return dates
    
    def analyze_single_day_company(self, symbol: str, company_name: str, target_date: datetime) -> float:
        """특정 날짜, 특정 회사의 감성 분석"""
        try:
            # 뉴스 수집
            news_items = self.news_collector.collect_company_news(company_name, symbol, target_date)
            
            # 뉴스 상세 로깅
            logger.info(f"=== {symbol} ({target_date.strftime('%Y-%m-%d')}) 뉴스 분석 ===")
            
            if not news_items:
                logger.info(f"{symbol}: 뉴스 없음, 중립값(0) 반환")
                logger.info(f"{'='*50}")
                return 0.0
            
            # 각 뉴스 아이템 상세 로깅
            logger.info(f"📰 수집된 뉴스 {len(news_items)}개:")
            for i, news in enumerate(news_items, 1):
                logger.info(f"  [{i}] 제목: {news['title']}")
                logger.info(f"      출처: {news['source']}")
                logger.info(f"      날짜: {news['published_date']}")
                logger.info(f"      설명: {news['description'][:200]}{'...' if len(news['description']) > 200 else ''}")
                logger.info(f"      링크: {news['link']}")
                logger.info(f"      ---")
            
            # 뉴스 텍스트 결합
            news_text = self.news_collector.get_news_text(news_items)
            
            if not news_text.strip():
                logger.info(f"{symbol}: 빈 텍스트, 중립값(0) 반환")
                logger.info(f"{'='*50}")
                return 0.0
            
            # 결합된 뉴스 텍스트 로깅
            logger.info(f"📝 결합된 뉴스 텍스트 (총 {len(news_text)} 문자):")
            logger.info(f"텍스트 시작 500자: {news_text[:500]}...")
            if len(news_text) > 1000:
                logger.info(f"텍스트 끝 500자: ...{news_text[-500:]}")
            logger.info(f"---")
            
            # 감성 분석 시작 로깅
            logger.info(f"🤖 감성분석 시작 (모델: gpt-oss:20b)")
            
            # 감성 분석
            sentiment_score = self.sentiment_analyzer.analyze_sentiment(news_text)
            
            # 감성 분석 결과 상세 로깅
            logger.info(f"🎯 {symbol} 감성분석 완료:")
            logger.info(f"   📊 감성 점수: {sentiment_score:.4f}")
            logger.info(f"   📈 분석 텍스트 길이: {len(news_text):,} 문자")
            logger.info(f"   📰 뉴스 개수: {len(news_items)}개")
            
            # 감성 점수 상세 해석
            if sentiment_score > 0.5:
                interpretation = "매우 긍정적 🚀"
                market_impact = "주가 상승 요인"
            elif sentiment_score > 0.2:
                interpretation = "긍정적 📈"
                market_impact = "약간의 주가 상승 요인"
            elif sentiment_score > -0.2:
                interpretation = "중립적 ➡️"
                market_impact = "주가에 중립적 영향"
            elif sentiment_score > -0.5:
                interpretation = "부정적 📉"
                market_impact = "약간의 주가 하락 요인"
            else:
                interpretation = "매우 부정적 💥"
                market_impact = "주가 하락 요인"
            
            logger.info(f"   💡 해석: {interpretation}")
            logger.info(f"   📊 시장 영향: {market_impact}")
            
            # 점수 범주별 분류
            if sentiment_score > 0:
                logger.info(f"   ✅ 분류: 긍정적 뉴스 (+{sentiment_score:.4f})")
            elif sentiment_score < 0:
                logger.info(f"   ❌ 분류: 부정적 뉴스 ({sentiment_score:.4f})")
            else:
                logger.info(f"   ⚪ 분류: 중립적 뉴스 (0.0000)")
            
            # 신뢰도 평가 (뉴스 개수 기반)
            if len(news_items) >= 5:
                confidence = "높음"
            elif len(news_items) >= 3:
                confidence = "보통"
            else:
                confidence = "낮음"
            
            logger.info(f"   🎯 신뢰도: {confidence} (뉴스 {len(news_items)}개 기반)")
            logger.info(f"{'='*70}")
            
            return sentiment_score
            
        except Exception as e:
            error_msg = f"{symbol} ({target_date.strftime('%Y-%m-%d')}) 분석 오류: {e}"
            logger.error(error_msg)
            logger.error(f"{'='*50}")
            return 0.0
    
    def analyze_period(self, start_date: str, end_date: str, output_filename: str = "nasdaq100_sentiment.csv") -> pd.DataFrame:
        """기간 동안의 모든 기업 감성 분석"""
        dates = self.generate_date_range(start_date, end_date)
        
        # 결과 디렉토리에 파일 저장
        output_file = os.path.join(self.result_dir, output_filename)
        temp_file = os.path.join(self.result_dir, f"{output_filename}.temp")
        
        logger.info(f"분석 기간: {start_date} ~ {end_date} ({len(dates)}일)")
        logger.info(f"분석 대상: 나스닥 100 기업 {len(self.nasdaq100_symbols)}개")
        logger.info(f"총 분석 작업: {len(dates) * len(self.nasdaq100_symbols)}개")
        logger.info(f"결과 저장 위치: {output_file}")
        
        # 결과 데이터프레임 초기화
        df = pd.DataFrame(index=[d.strftime('%Y-%m-%d') for d in dates], 
                         columns=self.nasdaq100_symbols)
        df = df.fillna(0.0)  # 기본값 0으로 설정
        
        # 진행상황 추적
        total_tasks = len(dates) * len(self.nasdaq100_symbols)
        completed_tasks = 0
        
        with tqdm(total=total_tasks, desc="감성 분석 진행") as pbar:
            for date in dates:
                date_str = date.strftime('%Y-%m-%d')
                logger.info(f"날짜 {date_str} 분석 시작")
                
                for symbol in self.nasdaq100_symbols:
                    company_name = self.company_names[symbol]
                    
                    try:
                        sentiment_score = self.analyze_single_day_company(symbol, company_name, date)
                        df.loc[date_str, symbol] = sentiment_score
                        
                        # 중간 저장 (10개 작업마다)
                        if completed_tasks % 10 == 0:
                            df.to_csv(temp_file)
                        
                    except Exception as e:
                        logger.error(f"{symbol} ({date_str}) 처리 오류: {e}")
                        df.loc[date_str, symbol] = 0.0
                    
                    completed_tasks += 1
                    pbar.update(1)
                    
                    # Rate limiting (너무 빠른 요청 방지)
                    time.sleep(1)
                
                # 하루 완료 후 저장
                df.to_csv(temp_file)
                logger.info(f"날짜 {date_str} 분석 완료")
        
        # 최종 저장
        df.to_csv(output_file)
        logger.info(f"분석 완료. 결과 저장: {output_file}")
        
        # 임시 파일 삭제
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        return df
    
    def load_and_resume(self, output_filename: str, start_date: str, end_date: str) -> pd.DataFrame:
        """기존 분석 결과를 로드하고 미완료 부분을 이어서 분석"""
        output_file = os.path.join(self.result_dir, output_filename)
        temp_file = os.path.join(self.result_dir, f"{output_filename}.temp")
        
        if os.path.exists(temp_file):
            logger.info(f"임시 파일에서 분석 재개: {temp_file}")
            df = pd.read_csv(temp_file, index_col=0)
        elif os.path.exists(output_file):
            logger.info(f"기존 파일에서 분석 재개: {output_file}")
            df = pd.read_csv(output_file, index_col=0)
        else:
            logger.info("새로운 분석 시작")
            return self.analyze_period(start_date, end_date, output_filename)
        
        # 미완료 부분 찾기
        dates = self.generate_date_range(start_date, end_date)
        
        for date in dates:
            date_str = date.strftime('%Y-%m-%d')
            
            if date_str not in df.index:
                logger.info(f"누락된 날짜 {date_str}부터 분석 재개")
                # 나머지 기간 분석
                remaining_start = date_str
                remaining_df = self.analyze_period(remaining_start, end_date, output_filename)
                return remaining_df
        
        logger.info("모든 분석이 완료되었습니다.")
        return df
    
    def get_summary_statistics(self, df: pd.DataFrame) -> Dict:
        """분석 결과 요약 통계"""
        summary = {
            'total_days': len(df),
            'total_companies': len(df.columns),
            'total_analysis_points': df.size,
            'zero_values_count': (df == 0).sum().sum(),
            'positive_sentiment_ratio': (df > 0).sum().sum() / df.size,
            'negative_sentiment_ratio': (df < 0).sum().sum() / df.size,
            'neutral_sentiment_ratio': (df == 0).sum().sum() / df.size,
            'mean_sentiment_by_company': df.mean().to_dict(),
            'mean_sentiment_by_date': df.mean(axis=1).to_dict()
        }
        
        return summary

def main():
    # 테스트 설정 (상위 10개 기업)
    START_DATE = "2025-08-01"  # 시작 날짜
    END_DATE = "2025-08-21"    # 종료 날짜 
    OUTPUT_FILENAME = "nasdaq10_sentiment_analysis.csv"
    
    # 결과 디렉토리 설정
    result_dir = setup_result_directory(START_DATE, END_DATE)
    
    # 로깅 설정 (결과 디렉토리에 로그 저장)
    logger = setup_logging(result_dir)
    
    # WSL에서 Windows 호스트의 Ollama 서버 접근
    windows_ip = get_windows_host_ip()
    OLLAMA_HOST = f"http://{windows_ip}:11434"
    
    # Ollama 설정 확인
    print("=== 나스닥 10 주식 감성분석 테스트 ===")
    print("Windows에서 실행 중인 Ollama 서버에 연결합니다.")
    print(f"감지된 Windows 호스트 IP: {windows_ip}")
    print(f"Ollama 호스트: {OLLAMA_HOST}")
    print(f"테스트 기간: {START_DATE} ~ {END_DATE}")
    print("테스트 대상: 나스닥 상위 10개 기업")
    print(f"결과 저장 위치: {result_dir}/")
    print("Windows에서 Ollama가 실행 중인지 확인해주세요.")
    print("모델 다운로드: ollama pull gpt-oss:20b")
    input("준비가 되면 Enter를 눌러주세요...")
    
    # 분석기 초기화
    analyzer = StockSentimentAnalyzer(ollama_host=OLLAMA_HOST, result_dir=result_dir)
    
    # 상위 10개 기업만 선택 (시가총액 기준)
    top_10_symbols = ['AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'GOOG', 'META', 'TSLA', 'AVGO', 'COST']
    analyzer.nasdaq100_symbols = top_10_symbols
    
    print(f"선택된 기업: {', '.join(top_10_symbols)}")
    
    # 분석 정보 로깅
    logger.info("="*50)
    logger.info("나스닥 10 주식 감성분석 시작")
    logger.info(f"분석 기간: {START_DATE} ~ {END_DATE}")
    logger.info(f"분석 대상: {', '.join(top_10_symbols)}")
    logger.info(f"결과 디렉토리: {result_dir}")
    logger.info("="*50)
    
    # 분석 실행 (재개 가능)
    try:
        df = analyzer.load_and_resume(OUTPUT_FILENAME, START_DATE, END_DATE)
        
        # 결과 요약
        summary = analyzer.get_summary_statistics(df)
        
        # 요약 정보 출력 및 로깅
        summary_text = f"""
=== 분석 결과 요약 ===
분석 기간: {START_DATE} ~ {END_DATE}
총 분석일수: {summary['total_days']}일
총 기업수: {summary['total_companies']}개
총 분석 포인트: {summary['total_analysis_points']}개
뉴스 없음(0값): {summary['zero_values_count']}개 ({summary['neutral_sentiment_ratio']*100:.1f}%)
긍정 감성: {summary['positive_sentiment_ratio']*100:.1f}%
부정 감성: {summary['negative_sentiment_ratio']*100:.1f}%

결과 파일: {os.path.join(result_dir, OUTPUT_FILENAME)}
로그 파일: {os.path.join(result_dir, 'sentiment_analysis.log')}
        """
        
        print(summary_text)
        logger.info(summary_text)
        
        # 요약 통계를 JSON 파일로 저장
        import json
        summary_file = os.path.join(result_dir, "analysis_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"요약 통계 저장: {summary_file}")
        print("분석 완료!")
        
    except KeyboardInterrupt:
        logger.info("사용자에 의해 분석이 중단되었습니다.")
        print("분석이 중단되었습니다. 임시 파일이 저장되어 나중에 재개할 수 있습니다.")
    except Exception as e:
        logger.error(f"분석 중 오류 발생: {e}")
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    main()
