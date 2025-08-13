import requests
import os
from datetime import datetime
import re

class CNNDebugger:
    def __init__(self):
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.cnn_url = "https://edition.cnn.com/markets/fear-and-greed"
        
        if not self.telegram_token or not self.chat_id:
            raise ValueError("환경변수 설정 오류")
        
        print("✅ 환경변수 로드 완료")
    
    def debug_cnn_html(self):
        """
        CNN 페이지의 실제 HTML 구조 분석
        """
        try:
            print("🔍 CNN HTML 구조 디버깅 시작...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(self.cnn_url, headers=headers, timeout=20)
            print(f"HTTP 상태: {response.status_code}")
            
            if response.status_code != 200:
                return f"❌ HTTP 오류: {response.status_code}"
            
            response.encoding = 'utf-8'
            html_content = response.text
            
            print(f"페이지 크기: {len(html_content):,} 글자")
            
            # === 디버깅 정보 수집 ===
            debug_info = []
            debug_info.append("🔍 CNN 페이지 분석 결과")
            debug_info.append("=" * 40)
            
            # 1. Fear & Greed 키워드 검색
            fear_count = html_content.lower().count('fear')
            greed_count = html_content.lower().count('greed')
            debug_info.append(f"📊 키워드 카운트:")
            debug_info.append(f"  - 'fear': {fear_count}번")
            debug_info.append(f"  - 'greed': {greed_count}번")
            
            if fear_count == 0 and greed_count == 0:
                debug_info.append("❌ Fear & Greed 키워드 없음 - 잘못된 페이지")
                return "\n".join(debug_info)
            
            # 2. 모든 숫자 찾기
            all_numbers = re.findall(r'\b(\d{1,2})\b', html_content)
            unique_numbers = sorted(list(set(all_numbers)), key=int)
            debug_info.append(f"\n🔢 발견된 숫자들 ({len(unique_numbers)}개):")
            debug_info.append(f"  {', '.join(unique_numbers)}")
            
            # 3. Fear/Greed 근처 숫자들
            fear_greed_numbers = []
            fear_greed_matches = list(re.finditer(r'fear|greed', html_content, re.IGNORECASE))
            
            for match in fear_greed_matches[:5]:  # 처음 5개만
                start = max(0, match.start() - 100)
                end = min(len(html_content), match.end() + 100)
                context = html_content[start:end]
                context_numbers = re.findall(r'\b(\d{1,2})\b', context)
                if context_numbers:
                    fear_greed_numbers.extend(context_numbers)
            
            unique_fg_numbers = sorted(list(set(fear_greed_numbers)), key=int)
            debug_info.append(f"\n🎯 Fear/Greed 근처 숫자들:")
            debug_info.append(f"  {', '.join(unique_fg_numbers) if unique_fg_numbers else '없음'}")
            
            # 4. 관련 클래스명 찾기
            class_patterns = [
                r'class=["\']([^"\']*(?:fear|greed|gauge|index|market)[^"\']*)["\']',
                r'class=["\']([^"\']*dial[^"\']*)["\']',
                r'class=["\']([^"\']*score[^"\']*)["\']',
                r'class=["\']([^"\']*value[^"\']*)["\']',
            ]
            
            found_classes = set()
            for pattern in class_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                found_classes.update(matches)
            
            relevant_classes = [cls for cls in found_classes if any(keyword in cls.lower() 
                              for keyword in ['fear', 'greed', 'gauge', 'dial', 'score', 'value', 'market', 'index'])]
            
            debug_info.append(f"\n🏷️ 관련 클래스명들 ({len(relevant_classes)}개):")
            for cls in sorted(relevant_classes)[:10]:  # 처음 10개만
                debug_info.append(f"  - {cls}")
            
            # 5. 특정 패턴 검색 결과
            test_patterns = [
                ('market-fng-gauge__dial-number-value', r'market-fng-gauge__dial-number-value'),
                ('dial-number-value', r'dial-number-value'),
                ('fear.*greed.*숫자', r'fear.*greed.*?(\d{1,2})'),
                ('data-* 속성', r'data-[^=]*=["\'][^"\']*(\d{1,2})[^"\']*["\']'),
            ]
            
            debug_info.append(f"\n🔍 패턴 검색 결과:")
            for name, pattern in test_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
                debug_info.append(f"  - {name}: {len(matches)}개 매치")
                if matches and name != 'fear.*greed.*숫자':  # 너무 많은 출력 방지
                    debug_info.append(f"    → {matches[:3]}")  # 처음 3개만
            
            # 6. HTML 샘플 (Fear/Greed 근처)
            debug_info.append(f"\n📄 Fear/Greed 근처 HTML 샘플:")
            for match in fear_greed_matches[:2]:  # 처음 2개만
                start = max(0, match.start() - 200)
                end = min(len(html_content), match.end() + 200)
                sample = html_content[start:end]
                # 특수문자 정리
                sample = re.sub(r'[^\w\s<>/="\'-]', '', sample)
                debug_info.append(f"  샘플 {fear_greed_matches.index(match)+1}:")
                debug_info.append(f"    {sample[:300]}...")
            
            return "\n".join(debug_info)
            
        except Exception as e:
            return f"❌ 디버깅 오류: {e}"
    
    def send_telegram_message(self, message):
        try:
            print("📤 텔레그램 전송 중...")
            
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            
            # 메시지가 너무 길면 분할
            max_length = 4000  # 텔레그램 메시지 길이 제한
            
            if len(message) <= max_length:
                payload = {
                    'chat_id': self.chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
                response = requests.post(url, data=payload, timeout=10)
                response.raise_for_status()
            else:
                # 메시지 분할 전송
                parts = [message[i:i+max_length] for i in range(0, len(message), max_length)]
                for i, part in enumerate(parts):
                    payload = {
                        'chat_id': self.chat_id,
                        'text': f"📋 디버깅 리포트 {i+1}/{len(parts)}\n\n{part}",
                        'parse_mode': 'HTML'
                    }
                    response = requests.post(url, data=payload, timeout=10)
                    response.raise_for_status()
            
            print("✅ 텔레그램 전송 성공!")
            return True
            
        except Exception as e:
            print(f"❌ 텔레그램 전송 실패: {e}")
            return False
    
    def run(self):
        print("=" * 50)
        print("🔍 CNN HTML 구조 디버깅")
        print("=" * 50)
        
        # HTML 구조 분석
        debug_result = self.debug_cnn_html()
        
        # 결과를 텔레그램으로 전송
        success = self.send_telegram_message(debug_result)
        
        if success:
            print("🎉 디버깅 정보 전송 완료!")
            return True
        else:
            print("💥 디버깅 정보 전송 실패")
            return False

def main():
    try:
        debugger = CNNDebugger()
        success = debugger.run()
        
        if not success:
            exit(1)
            
    except Exception as e:
        print(f"💥 치명적 오류: {e}")
        exit(1)

if __name__ == "__main__":
    main()
