#!/usr/bin/env python3
"""
단일 기업 감성분석 테스트 (상세 로깅 확인용)
"""

import sys
import os
sys.path.append('/home/sangwoo/workspace/quantAI')

from datetime import datetime
from stock_sentiment_main import setup_result_directory, setup_logging, StockSentimentAnalyzer, get_windows_host_ip

def test_single_company():
    # 테스트 설정
    START_DATE = "2024-07-15"
    END_DATE = "2024-07-15"
    
    # 결과 디렉토리 설정
    result_dir = setup_result_directory(START_DATE, END_DATE)
    
    # 로깅 설정
    logger = setup_logging(result_dir)
    
    # Ollama 설정
    windows_ip = get_windows_host_ip()
    OLLAMA_HOST = f"http://{windows_ip}:11434"
    
    print(f"=== 단일 기업 감성분석 테스트 ===")
    print(f"테스트 날짜: {START_DATE}")
    print(f"결과 디렉토리: {result_dir}")
    
    # 분석기 초기화
    analyzer = StockSentimentAnalyzer(ollama_host=OLLAMA_HOST, result_dir=result_dir)
    
    # AAPL 하나만 테스트
    test_date = datetime(2024, 7, 15)
    
    logger.info("🚀 단일 기업 감성분석 테스트 시작")
    logger.info(f"테스트 대상: AAPL (Apple Inc.)")
    logger.info(f"테스트 날짜: {test_date.strftime('%Y-%m-%d')}")
    
    try:
        sentiment_score = analyzer.analyze_single_day_company("AAPL", "Apple Inc.", test_date)
        
        print(f"\n✅ 테스트 완료!")
        print(f"AAPL 감성 점수: {sentiment_score:.4f}")
        print(f"로그 파일: {result_dir}/sentiment_analysis.log")
        
        logger.info(f"🎉 테스트 완료: AAPL 감성점수 = {sentiment_score:.4f}")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        logger.error(f"테스트 실패: {e}")

if __name__ == "__main__":
    test_single_company()
