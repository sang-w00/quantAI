#!/usr/bin/env python3
"""
WSL에서 Windows Ollama 서버 연결 테스트
"""

import subprocess
import requests
import json

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
        print(f"Windows 호스트 IP 자동 감지 실패: {e}")
    
    return "172.19.144.1"

def test_ollama_connection():
    """Ollama 서버 연결 및 모델 테스트"""
    windows_ip = get_windows_host_ip()
    ollama_host = f"http://{windows_ip}:11434"
    
    print(f"Windows 호스트 IP: {windows_ip}")
    print(f"Ollama 호스트: {ollama_host}")
    
    # 1. 서버 연결 테스트
    try:
        response = requests.get(f"{ollama_host}/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama 서버 연결 성공!")
            print(f"사용 가능한 모델 수: {len(models)}")
            
            for model in models:
                print(f"  - {model['name']} ({model['details']['parameter_size']})")
        else:
            print(f"❌ Ollama 서버 연결 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama 서버 연결 오류: {e}")
        return False
    
    # 2. gpt-oss:20b 모델 테스트
    try:
        test_prompt = "Analyze the sentiment of this text: 'Apple reports strong quarterly earnings.' Return only a number between -1 and 1."
        
        payload = {
            "model": "gpt-oss:20b",
            "prompt": test_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "max_tokens": 10
            }
        }
        
        print("\n🔍 모델 테스트 중...")
        response = requests.post(f"{ollama_host}/api/generate", json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('response', '').strip()
            print(f"✅ 모델 응답 성공!")
            print(f"테스트 프롬프트: {test_prompt}")
            print(f"모델 응답: {answer}")
            return True
        else:
            print(f"❌ 모델 테스트 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 모델 테스트 오류: {e}")
        return False

if __name__ == "__main__":
    print("=== WSL -> Windows Ollama 연결 테스트 ===")
    success = test_ollama_connection()
    
    if success:
        print("\n🎉 모든 테스트 통과! 감성분석을 시작할 수 있습니다.")
        print("실행 명령: python stock_sentiment_main.py")
    else:
        print("\n❌ 테스트 실패. 다음을 확인해주세요:")
        print("1. Windows에서 Ollama가 실행 중인가?")
        print("2. Windows 방화벽이 11434 포트를 허용하는가?")
        print("3. gpt-oss:20b 모델이 설치되어 있는가?")
