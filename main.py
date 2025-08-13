name: 📱 Fear & Greed Index Daily Alarm

# 실행 스케줄 설정
on:
  # 매일 오전 9시 (한국시간)에 실행
  # GitHub Actions는 UTC 기준이므로 0시 = 한국시간 9시
  schedule:
    - cron: '0 0 * * *'  # 매일 00:00 UTC = 한국시간 09:00
    
  # 수동 실행도 가능하도록 설정 (테스트용)
  workflow_dispatch:

jobs:
  send_alarm:
    name: 🚀 Fear & Greed Index 알림 전송
    runs-on: ubuntu-latest
    
    steps:
    # 1단계: 코드 체크아웃
    - name: 📥 코드 체크아웃
      uses: actions/checkout@v4
      
    # 2단계: Python 환경 설정
    - name: 🐍 Python 3.11 설정
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    # 3단계: 의존성 설치
    - name: 📦 라이브러리 설치
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        
    # 4단계: Fear & Greed Index 알림 실행
    - name: 📱 텔레그램 알림 전송
      env:
        TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
        TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
      run: |
        echo "🚀 Fear & Greed Index 알림 시작..."
        python main.py
        echo "✅ 알림 전송 완료!"
        
    # 5단계: 실행 결과 로깅
    - name: 📋 실행 완료 로그
      if: always()
      run: |
        echo "📅 실행 시간: $(date)"
        echo "🎯 Fear & Greed Index 알림이 실행되었습니다."
