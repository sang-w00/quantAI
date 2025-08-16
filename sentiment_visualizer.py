import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np
import os

def analyze_sentiment_results(result_dir: str = None, csv_filename: str = "nasdaq10_sentiment_analysis.csv"):
    """감성 분석 결과를 시각화하고 분석"""
    
    # 결과 디렉토리 자동 감지 또는 직접 지정
    if result_dir is None:
        # results 폴더에서 가장 최근 폴더 찾기
        results_base = "results"
        if os.path.exists(results_base):
            folders = [f for f in os.listdir(results_base) if os.path.isdir(os.path.join(results_base, f))]
            if folders:
                folders.sort(reverse=True)  # 최신 폴더가 앞에 오도록
                result_dir = os.path.join(results_base, folders[0])
                print(f"자동 감지된 결과 폴더: {result_dir}")
            else:
                result_dir = "."
                print("결과 폴더를 찾을 수 없어 현재 디렉토리를 사용합니다.")
        else:
            result_dir = "."
    
    csv_file = os.path.join(result_dir, csv_filename)
    
    if not os.path.exists(csv_file):
        print(f"파일을 찾을 수 없습니다: {csv_file}")
        return None, None, None, None
    
    # 데이터 로드
    df = pd.read_csv(csv_file, index_col=0)
    df.index = pd.to_datetime(df.index)
    
    print(f"데이터 형태: {df.shape}")
    print(f"분석 기간: {df.index.min()} ~ {df.index.max()}")
    print(f"결과 디렉토리: {result_dir}")
    
    # 1. 전체 감성 분포
    plt.figure(figsize=(15, 10))
    
    plt.subplot(2, 3, 1)
    all_values = df.values.flatten()
    plt.hist(all_values, bins=50, alpha=0.7)
    plt.title('전체 감성 점수 분포')
    plt.xlabel('감성 점수')
    plt.ylabel('빈도')
    
    # 2. 일별 평균 감성
    plt.subplot(2, 3, 2)
    daily_sentiment = df.mean(axis=1)
    plt.plot(daily_sentiment.index, daily_sentiment)
    plt.title('일별 평균 감성 추이')
    plt.xlabel('날짜')
    plt.ylabel('평균 감성 점수')
    plt.xticks(rotation=45)
    
    # 3. 기업별 평균 감성 (상위 10개)
    plt.subplot(2, 3, 3)
    company_sentiment = df.mean(axis=0).sort_values(ascending=False)
    company_sentiment.head(10).plot(kind='bar')
    plt.title('평균 감성 상위 10개 기업')
    plt.ylabel('평균 감성 점수')
    plt.xticks(rotation=45)
    
    # 4. 기업별 평균 감성 (하위 10개)
    plt.subplot(2, 3, 4)
    company_sentiment.tail(10).plot(kind='bar', color='red')
    plt.title('평균 감성 하위 10개 기업')
    plt.ylabel('평균 감성 점수')
    plt.xticks(rotation=45)
    
    # 5. 감성 변동성 (표준편차)
    plt.subplot(2, 3, 5)
    company_volatility = df.std(axis=0).sort_values(ascending=False)
    company_volatility.head(10).plot(kind='bar', color='orange')
    plt.title('감성 변동성 상위 10개 기업')
    plt.ylabel('감성 표준편차')
    plt.xticks(rotation=45)
    
    # 6. 뉴스 커버리지 (0이 아닌 값의 비율)
    plt.subplot(2, 3, 6)
    coverage = (df != 0).mean(axis=0).sort_values(ascending=False)
    coverage.head(10).plot(kind='bar', color='green')
    plt.title('뉴스 커버리지 상위 10개 기업')
    plt.ylabel('뉴스 있는 날의 비율')
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    # 결과 디렉토리에 이미지 저장
    overview_file = os.path.join(result_dir, 'sentiment_analysis_overview.png')
    plt.savefig(overview_file, dpi=300, bbox_inches='tight')
    print(f"분석 개요 이미지 저장: {overview_file}")
    plt.show()
    
    # 상세 분석 출력
    print("\n=== 상세 분석 결과 ===")
    print(f"전체 평균 감성: {all_values.mean():.4f}")
    print(f"전체 감성 표준편차: {all_values.std():.4f}")
    print(f"긍정 비율: {(all_values > 0).mean()*100:.1f}%")
    print(f"중립 비율: {(all_values == 0).mean()*100:.1f}%")
    print(f"부정 비율: {(all_values < 0).mean()*100:.1f}%")
    
    print(f"\n가장 긍정적인 기업 Top 5:")
    for i, (symbol, score) in enumerate(company_sentiment.head(5).items(), 1):
        print(f"{i}. {symbol}: {score:.4f}")
    
    print(f"\n가장 부정적인 기업 Top 5:")
    for i, (symbol, score) in enumerate(company_sentiment.tail(5).items(), 1):
        print(f"{i}. {symbol}: {score:.4f}")
    
    print(f"\n감성 변동성이 큰 기업 Top 5:")
    for i, (symbol, vol) in enumerate(company_volatility.head(5).items(), 1):
        print(f"{i}. {symbol}: {vol:.4f}")
    
    print(f"\n뉴스 커버리지가 높은 기업 Top 5:")
    for i, (symbol, cov) in enumerate(coverage.head(5).items(), 1):
        print(f"{i}. {symbol}: {cov*100:.1f}%")
    
    # 히트맵 생성 (월별 감성)
    plt.figure(figsize=(20, 12))
    
    # 월별 데이터 집계
    df_monthly = df.resample('M').mean()
    
    # 상위 20개 기업만 표시
    top_companies = company_sentiment.head(20).index
    
    sns.heatmap(df_monthly[top_companies].T, 
                cmap='RdYlGn', center=0, 
                annot=False, fmt='.2f',
                cbar_kws={'label': '감성 점수'})
    plt.title('월별 감성 히트맵 (상위 20개 기업)')
    plt.xlabel('월')
    plt.ylabel('기업')
    plt.tight_layout()
    
    # 결과 디렉토리에 히트맵 저장
    heatmap_file = os.path.join(result_dir, 'sentiment_heatmap.png')
    plt.savefig(heatmap_file, dpi=300, bbox_inches='tight')
    print(f"감성 히트맵 저장: {heatmap_file}")
    plt.show()
    
    return df, company_sentiment, company_volatility, coverage

if __name__ == "__main__":
    # 분석 실행
    print("=== 감성 분석 결과 시각화 ===")
    print("최신 결과 폴더를 자동으로 찾아 분석합니다...")
    df, sentiment, volatility, coverage = analyze_sentiment_results()
