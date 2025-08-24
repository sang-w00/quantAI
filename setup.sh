#!/bin/bash

# QuantAI 자동 설치 스크립트
# Ubuntu/Debian/WSL 환경용

set -e

echo "🚀 QuantAI 설치를 시작합니다..."

# 시스템 업데이트
echo "📦 시스템 패키지 업데이트 중..."
sudo apt update

# Python 및 필수 패키지 설치
echo "🐍 Python 및 필수 도구 설치 중..."
sudo apt install -y python3 python3-pip python3-venv curl

# 가상환경 생성
echo "🏠 Python 가상환경 생성 중..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 가상환경 활성화
echo "⚡ 가상환경 활성화 중..."
source venv/bin/activate

# Python 패키지 설치
echo "📚 Python 패키지 설치 중..."
pip install --upgrade pip
pip install -r requirements.txt

# Ollama 설치
echo "🤖 Ollama 설치 중..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh
    
    # Ollama 서비스 시작
    echo "🔧 Ollama 서비스 설정 중..."
    sudo systemctl start ollama
    sudo systemctl enable ollama
    
    # 잠시 대기
    sleep 5
    
    # 기본 모델 다운로드 (선택사항)
    echo "📥 AI 모델 다운로드 중... (시간이 오래 걸릴 수 있습니다)"
    ollama pull llama3.1:8b
else
    echo "✅ Ollama가 이미 설치되어 있습니다."
fi

# 결과 디렉토리 생성
echo "📁 결과 디렉토리 생성 중..."
mkdir -p results

# 권한 설정
echo "🔐 권한 설정 중..."
chmod +x setup.sh

echo ""
echo "🎉 설치 완료!"
echo ""
echo "다음 단계를 따라 QuantAI를 사용하세요:"
echo ""
echo "1. Polygon API 키 설정:"
echo "   - https://polygon.io/ 에서 API 키 발급"
echo "   - 환경 변수로 설정: export POLYGON_API_KEY=\"YOUR_API_KEY\""
echo ""
echo "2. 가상환경 활성화:"
echo "   source venv/bin/activate"
echo ""
echo "3. 프로그램 실행:"
echo "   python stock_sentiment_main.py"
echo ""
echo "4. 테스트 실행:"
echo "   python test_ollama_connection.py"
echo "   python test_single_sentiment.py"
echo ""
echo "문제가 발생하면 README.md 파일의 문제 해결 섹션을 확인하세요."
echo ""
echo "Happy analyzing! 📈"

# Ollama 서비스 시작
echo "3. Ollama 서비스 시작..."
ollama serve &
OLLAMA_PID=$!
sleep 5

# gpt-oss:20b 모델 다운로드
echo "4. gpt-oss:20b 모델 다운로드 중... (시간이 오래 걸릴 수 있습니다)"
ollama pull gpt-oss:20b

echo "5. 설정 완료!"
echo ""
echo "사용법:"
echo "python stock_sentiment_main.py  # 감성분석 실행"
echo "python sentiment_visualizer.py  # 결과 시각화"
echo ""
echo "주의사항:"
echo "- 분석에는 매우 오랜 시간이 걸립니다 (수 시간~수 일)"
echo "- 중간에 중단되어도 임시 파일로 재개 가능합니다"
echo "- Ollama 서버가 계속 실행되어야 합니다"

# Ollama 서비스 종료 (백그라운드에서 계속 실행하려면 주석 처리)
# kill $OLLAMA_PID
