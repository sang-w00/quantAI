# QuantAI - Stock Sentiment Analysis Tool

NASDAQ 100 주식에 대한 뉴스 감성 분석을 통해 투자 인사이트를 제공하는 Python 도구입니다.

## 🚀 주요 기능

- **뉴스 수집**: GNews API를 통한 실시간 뉴스 수집
- **감성 분석**: Ollama를 활용한 AI 기반 감성 분석
- **NASDAQ 100 지원**: 100개 주요 기업 자동 분석
- **영업일 필터링**: 주말/공휴일 제외한 데이터 처리
- **결과 시각화**: 감성 점수 및 트렌드 차트 생성
- **CSV 출력**: 분석 결과 데이터 저장

## 📋 시스템 요구사항

- Python 3.8+
- Linux/WSL 환경 (권장)
- 최소 4GB RAM
- 인터넷 연결

## 🛠️ 설치 및 설정

### 1. 저장소 클론

```bash
git clone https://github.com/YOUR_USERNAME/quantAI.git
cd quantAI
```

### 2. Python 가상환경 설정

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Linux/WSL)
source venv/bin/activate

# 또는 conda 사용
conda create -n quantai python=3.12
conda activate quantai
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. Ollama 설치 (감성 분석용)

```bash
# Ollama 설치
curl -fsSL https://ollama.ai/install.sh | sh

# 서비스 시작
sudo systemctl start ollama
sudo systemctl enable ollama

# 모델 다운로드 (선택사항 - 더 작은 모델)
ollama pull gpt-oss:20b
```

### 5. GNews API 키 설정

1. [GNews.io](https://gnews.io/)에서 무료 API 키 발급
2. `news_collector.py` 파일에서 API 키 수정:

```python
def __init__(self, gnews_api_key: str = "YOUR_API_KEY_HERE"):
```

## 🚀 사용법

### 기본 실행

```bash
# conda 환경 활성화 (선택사항)
conda activate quantai

# 메인 스크립트 실행
python stock_sentiment_main.py
```

### 고급 사용법

#### 1. 특정 기간 분석

```python
from datetime import datetime
from stock_sentiment_main import analyze_period

# 특정 기간 분석
start_date = "2024-06-01"
end_date = "2024-06-30"
analyze_period(start_date, end_date)
```

#### 2. 개별 뉴스 수집

```python
from news_collector import NewsCollector
from datetime import datetime

collector = NewsCollector()
news = collector.collect_company_news("Apple Inc.", "AAPL", datetime(2024, 6, 15))
print(f"수집된 뉴스: {len(news)}개")
```

#### 3. 감성 분석만 실행

```python
from sentiment_analyzer import SentimentAnalyzer

analyzer = SentimentAnalyzer()
text = "Apple reported strong quarterly earnings..."
sentiment = analyzer.analyze_sentiment(text)
print(f"감성 점수: {sentiment['score']}")
```

## 📁 프로젝트 구조

```
quantAI/
├── README.md                 # 프로젝트 설명서
├── requirements.txt          # Python 의존성
├── setup.sh                 # 자동 설치 스크립트
├── stock_sentiment_main.py  # 메인 실행 파일
├── news_collector.py        # 뉴스 수집 모듈
├── sentiment_analyzer.py    # 감성 분석 모듈
├── sentiment_visualizer.py  # 시각화 모듈
├── nasdaq100_companies.py   # NASDAQ 100 기업 정보
├── test_*.py               # 테스트 파일들
└── results/                # 분석 결과 저장 폴더
    ├── YYYY-MM-DD_to_YYYY-MM-DD/
    │   ├── sentiment_analysis.csv
    │   ├── sentiment_summary.csv
    │   └── visualizations/
    └── ...
```

## 🔧 설정 옵션

### Ollama 모델 변경

`sentiment_analyzer.py`에서 모델 변경 가능:

```python
OLLAMA_MODEL = "llama3.1:8b"  # 더 빠른 모델
# 또는
OLLAMA_MODEL = "gemma2:27b"   # 더 정확한 모델
```

### GNews API 설정

`news_collector.py`에서 검색 옵션 조정:

```python
params = {
    'lang': 'en',           # 언어 설정
    'country': 'us',        # 국가 설정
    'max': 100,            # 최대 기사 수
    'sortby': 'publishedAt' # 정렬 방식
}
```

## 📊 출력 파일

### 1. `sentiment_analysis.csv`
개별 기업의 상세 분석 결과:
- Date, Symbol, Company_Name
- News_Count, Average_Sentiment
- News_Text, Analysis_Details

### 2. `sentiment_summary.csv`
기간별 요약 통계:
- Symbol, Company_Name
- Total_News_Count, Average_Sentiment
- Positive_Count, Negative_Count, Neutral_Count

### 3. 시각화 파일
- `sentiment_distribution.png`: 감성 분포 차트
- `top_companies_sentiment.png`: 상위 기업 감성 순위
- `sentiment_trends.png`: 시간별 감성 트렌드

## 🐛 문제 해결

### 1. Ollama 연결 오류

```bash
# Ollama 서비스 상태 확인
sudo systemctl status ollama

# 수동 시작
ollama serve

# 포트 확인
curl http://localhost:11434
```

### 2. GNews API 오류

- API 키 유효성 확인
- 일일 호출 제한 확인 (무료: 100회/일)
- 네트워크 연결 상태 확인

### 3. 메모리 부족

```bash
# 더 작은 Ollama 모델 사용
ollama pull gemma2:2b

# 배치 크기 줄이기
# stock_sentiment_main.py에서 조정
```

### 4. 의존성 문제

```bash
# 가상환경 재생성
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 🔬 테스트

### 단위 테스트 실행

```bash
# Ollama 연결 테스트
python test_ollama_connection.py

# 단일 감성 분석 테스트
python test_single_sentiment.py

# 뉴스 수집 테스트
python news_collector.py
```

### 샘플 데이터 테스트

```bash
# 단일 날짜 테스트
python -c "
from stock_sentiment_main import test_single_date
test_single_date('2024-06-15')
"
```

## 📈 성능 최적화

### 1. 병렬 처리

```python
# 멀티스레딩으로 뉴스 수집 속도 향상
from concurrent.futures import ThreadPoolExecutor

# stock_sentiment_main.py에서 구현됨
```

### 2. 캐싱

```python
# 뉴스 데이터 캐싱으로 중복 호출 방지
# 결과를 로컬에 저장하여 재사용
```

### 3. 배치 처리

```python
# 대용량 데이터 처리 시 배치 단위로 분할
batch_size = 10  # 동시 처리할 기업 수
```

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의

- 이슈: [GitHub Issues](https://github.com/YOUR_USERNAME/quantAI/issues)
- 이메일: your.email@example.com

## 🙏 감사의 말

- [GNews API](https://gnews.io/) - 뉴스 데이터 제공
- [Ollama](https://ollama.ai/) - AI 모델 인프라
- [NASDAQ](https://www.nasdaq.com/) - 기업 정보 제공

---

**⚠️ 면책 조항**: 이 도구는 교육 및 연구 목적으로 제작되었습니다. 투자 결정은 본인의 책임하에 이루어져야 하며, 본 도구의 분석 결과에만 의존하여 투자 결정을 내리는 것은 권장하지 않습니다.
