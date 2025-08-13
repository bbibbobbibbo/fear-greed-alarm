import requests
import os
from datetime import datetime, date
import calendar
import re
from bs4 import BeautifulSoup
import time

class PreciseCNNFearGreedNotifier:
    def __init__(self):
        """
        정확한 CSS 셀렉터 기반 CNN Fear & Greed Index 추출
        """
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.cnn_url = "https://edition.cnn.com/markets/fear-and-greed"
        
        if not self.telegram_token or not self.chat_id:
            raise ValueError("TELEGRAM_TOKEN 또는 TELEGRAM_CHAT_ID가 설정되지 않았습니다.")
        
        print("✅ 환경변수 로드 완료")
    
    def get_cnn_fear_greed_index(self):
        """
        실제 CSS 셀렉터를 사용한 정확한 추출
        """
        try:
            print("📊 CNN Fear & Greed Index 데이터 요청 중...")
            
            # 다양한 User-Agent로 시도
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            
            for attempt, user_agent in enumerate(user_agents, 1):
                print(f"🔄 시도 {attempt}/{len(user_agents)}...")
                
                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'DNT': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1'
                }
                
                try:
                    response = requests.get(self.cnn_url, headers=headers, timeout=25)
                    response.raise_for_status()
                    
                    if len(response.text) > 100000:  # 충분한 내용 로드 확인
                        print(f"✅ CNN 페이지 로드 성공 ({len(response.text):,} 글자)")
                        break
                    else:
                        print(f"⚠️ 페이지 내용 부족 ({len(response.text):,} 글자), 재시도...")
                        
                except Exception as e:
                    print(f"❌ 시도 {attempt} 실패: {e}")
                    if attempt < len(user_agents):
                        time.sleep(3)  # 3초 대기 후 재시도
                        continue
                    else:
                        raise
            
            # BeautifulSoup으로 HTML 파싱
            soup = BeautifulSoup(response.content, 'html.parser')
            print("✅ HTML 파싱 완료")
            
            # 방법 1: 정확한 CSS 셀렉터로 추출
            result = self._extract_with_exact_selectors(soup)
            if result:
                return result
            
            # 방법 2: 클래스명만으로 추출 (백업)
            result = self._extract_with_class_names(soup)
            if result:
                return result
            
            # 방법 3: 텍스트 패턴으로 추출 (최후 수단)
            result = self._extract_with_patterns(response.text)
            if result:
                return result
            
            print("❌ 모든 추출 방법 실패")
            return None
            
        except Exception as e:
            print(f"❌ CNN 데이터 추출 오류: {e}")
            return None
    
    def _extract_with_exact_selectors(self, soup):
        """
        정확한 CSS 셀렉터로 추출 (가장 확실한 방법)
        """
        try:
            print("🎯 정확한 CSS 셀렉터로 추출 시도...")
            
            # 지수 값 추출: .market-fng-gauge__dial-number-value
            score_element = soup.select_one('.market-fng-gauge__dial-number-value')
            
            if score_element:
                score_text = score_element.get_text(strip=True)
                print(f"✅ 지수 요소 발견: '{score_text}'")
                
                # 숫자 추출
                score_match = re.search(r'\b(\d{1,2})\b', score_text)
                if score_match:
                    score = int(score_match.group(1))
                    print(f"✅ 지수 값 추출 성공: {score}")
                    
                    # 업데이트 시간 추출: .market-fng-gauge__timestamp
                    timestamp_element = soup.select_one('.market-fng-gauge__timestamp')
                    update_time = "업데이트 시간 불명"
                    
                    if timestamp_element:
                        update_text = timestamp_element.get_text(strip=True)
                        print(f"✅ 업데이트 시간 발견: '{update_text}'")
                        update_time = update_text
                    else:
                        print("⚠️ 업데이트 시간 요소를 찾을 수 없음")
                    
                    if 0 <= score <= 100:
                        return {
                            'value': score,
                            'classification': self._get_classification(score),
                            'source': 'CNN Fear & Greed Index',
                            'update_time': update_time,
                            'extraction_method': 'exact_css_selector',
                            'confidence': 1.0
                        }
                    else:
                        print(f"❌ 유효하지 않은 점수 범위: {score}")
                else:
                    print(f"❌ 지수 텍스트에서 숫자를 찾을 수 없음: '{score_text}'")
            else:
                print("❌ .market-fng-gauge__dial-number-value 요소를 찾을 수 없음")
            
            return None
            
        except Exception as e:
            print(f"정확한 셀렉터 추출 오류: {e}")
            return None
    
    def _extract_with_class_names(self, soup):
        """
        클래스명 기반 백업 추출
        """
        try:
            print("🔄 클래스명 기반 백업 추출 시도...")
            
            # Fear & Greed 관련 클래스들 찾기
            potential_classes = [
                'market-fng-gauge__dial-number-value',
                'market-fng-gauge__dial-number',
                'fng-gauge',
                'fear-greed',
                'dial-number',
                'gauge-value'
            ]
            
            for class_name in potential_classes:
                elements = soup.find_all(class_=lambda x: x and class_name in x)
                
                if elements:
                    print(f"  📋 '{class_name}' 관련 요소 {len(elements)}개 발견")
                    
                    for element in elements:
                        text = element.get_text(strip=True)
                        print(f"    텍스트: '{text}'")
                        
                        # 숫자 패턴 찾기
                        numbers = re.findall(r'\b(\d{1,2})\b', text)
                        for num_str in numbers:
                            score = int(num_str)
                            if 0 <= score <= 100:
                                print(f"✅ 클래스 기반 점수 발견: {score}")
                                return {
                                    'value': score,
                                    'classification': self._get_classification(score),
                                    'source': 'CNN Fear & Greed Index',
                                    'extraction_method': f'class_based_{class_name}',
                                    'confidence': 0.8
                                }
            
            return None
            
        except Exception as e:
            print(f"클래스명 기반 추출 오류: {e}")
            return None
    
    def _extract_with_patterns(self, html_text):
        """
        텍스트 패턴 기반 최후 추출
        """
        try:
            print("🔄 텍스트 패턴 기반 최후 추출 시도...")
            
            # CNN 특화 패턴들
            patterns = [
                r'market-fng-gauge__dial-number-value[^>]*>(\d{1,2})',
                r'dial-number-value[^>]*>(\d{1,2})',
                r'fear.*greed.*?(\d{1,2})',
                r'(\d{1,2}).*?fear.*greed',
                r'gauge.*?(\d{1,2})',
                r'index.*?(\d{1,2})',
            ]
            
            for i, pattern in enumerate(patterns, 1):
                matches = list(re.finditer(pattern, html_text, re.IGNORECASE | re.DOTALL))
                
                if matches:
                    print(f"  패턴 {i}: {len(matches)}개 매치")
                    
                    for match in matches:
                        score = int(match.group(1))
                        if 0 <= score <= 100:
                            # 컨텍스트 확인
                            start = max(0, match.start() - 200)
                            end = min(len(html_text), match.end() + 200)
                            context = html_text[start:end]
                            
                            # Fear & Greed 관련 키워드 확인
                            keywords = ['fear', 'greed', 'market', 'gauge', 'index']
                            keyword_count = sum(1 for keyword in keywords if keyword in context.lower())
                            
                            if keyword_count >= 2:
                                print(f"✅ 패턴 기반 점수 발견: {score} (키워드 {keyword_count}개)")
                                return {
                                    'value': score,
                                    'classification': self._get_classification(score),
                                    'source': 'CNN Fear & Greed Index',
                                    'extraction_method': f'pattern_{i}',
                                    'confidence': 0.6
                                }
            
            return None
            
        except Exception as e:
            print(f"패턴 기반 추출 오류: {e}")
            return None
    
    def _get_classification(self, value):
        """점수 분류"""
        if value <= 25:
            return "Extreme Fear"
        elif value <= 45:
            return "Fear"
        elif value <= 55:
            return "Neutral"
        elif value <= 75:
            return "Greed"
        else:
            return "Extreme Greed"
    
    def interpret_index(self, value):
        """지수 해석"""
        if value <= 25:
            interpretation = "🔴 극도의 공포 (Extreme Fear)"
            advice = "📈 시장이 극도로 두려워하고 있습니다. 워렌 버핏의 조언대로 '남이 두려워할 때 탐욕스러워하라'는 시점일 수 있습니다."
            emoji = "😱"
            strategy = "💰 우량 대형주 점진적 매수 고려"
        elif value <= 45:
            interpretation = "🟠 공포 (Fear)"
            advice = "📊 시장에 공포 심리가 확산되고 있습니다. 가치주들의 밸류에이션을 확인하고 저평가된 우량기업을 찾아보세요."
            emoji = "😰"
            strategy = "🎯 가치주 중심 선별적 매수"
        elif value <= 55:
            interpretation = "🟡 중립 (Neutral)"
            advice = "⚖️ 시장이 균형을 이루고 있습니다. 평소와 같이 꾸준한 분산투자와 정기적립을 유지하세요."
            emoji = "😐"
            strategy = "🔄 정기투자 및 리밸런싱"
        elif value <= 75:
            interpretation = "🟢 탐욕 (Greed)"
            advice = "⚠️ 시장에 탐욕이 커지고 있습니다. 고평가된 종목들을 점검하고 신중한 매수 접근이 필요합니다."
            emoji = "😊"
            strategy = "🚨 보수적 접근, 현금 비중 확대"
        else:
            interpretation = "🔥 극도의 탐욕 (Extreme Greed)"
            advice = "🚨 시장이 과열되었습니다. 일부 차익실현을 고려하고 다음 기회를 위해 현금을 준비하는 것이 좋겠습니다."
            emoji = "🤑"
            strategy = "💸 차익실현 및 현금 확보"
            
        return interpretation, advice, emoji, strategy
    
    def is_us_market_closed(self):
        """미국 시장 휴장일 확인"""
        today = datetime.now()
        weekday = today.weekday()
        
        if weekday >= 5:  # 주말
            return True
            
        month, day = today.month, today.day
        holidays = [(1, 1), (7, 4), (12, 25)]
        
        return (month, day) in holidays
    
    def should_send_message(self):
        """메시지 전송 여부"""
        if self.is_us_market_closed():
            print("🇺🇸 미국 주식시장 휴장일이므로 알림을 전송하지 않습니다.")
            return False
        return True
    
    def send_telegram_message(self, message):
        """텔레그램 메시지 전송"""
        try:
            print("📤 텔레그램 메시지 전송 중...")
            
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=payload, timeout=15)
            response.raise_for_status()
            
            print("✅ 텔레그램 메시지 전송 성공!")
            return True
            
        except Exception as e:
            print(f"❌ 텔레그램 전송 실패: {e}")
            return False
    
    def create_daily_message(self):
        """일일 메시지 생성"""
        fear_greed_data = self.get_cnn_fear_greed_index()
        
        if not fear_greed_data:
            return "❌ CNN Fear & Greed Index 데이터를 가져올 수 없습니다. 사이트 접속에 문제가 있거나 구조가 변경되었을 수 있습니다."
        
        current_time = datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")
        interpretation, advice, emoji, strategy = self.interpret_index(fear_greed_data['value'])
        
        value = fear_greed_data['value']
        filled_bars = value // 10
        progress_bar = "🟩" * filled_bars + "⬜" * (10 - filled_bars)
        
        # 신뢰도 표시
        confidence = fear_greed_data.get('confidence', 0.5)
        if confidence >= 0.9:
            confidence_text = "🎯 정확한 추출"
        elif confidence >= 0.7:
            confidence_text = "📊 높은 신뢰도"
        else:
            confidence_text = "⚠️ 백업 방법"
        
        # 업데이트 시간
        update_time = fear_greed_data.get('update_time', '업데이트 시간 불명')
        
        message = f"""
🇺🇸 <b>미국 주식시장 Fear & Greed Index</b> {emoji}
📅 {current_time} ({confidence_text})

📊 <b>현재 지수: {fear_greed_data['value']}/100</b>
{progress_bar}
{interpretation}

🕐 <b>CNN 업데이트 시간</b>
{update_time}

💡 <b>가치투자자 가이드</b>
{advice}

🎯 <b>투자 전략</b>
{strategy}

📈 <b>CNN Fear & Greed Index 구성요소</b>
• 주식 가격 모멘텀 • 주식 가격 강도 • 시장 폭
• 풋/콜 옵션 비율 • 정크본드 수요 • VIX 변동성
• 안전자산 수요

📚 <b>워렌 버핏의 투자 원칙</b>
"다른 사람이 탐욕스러울 때 두려워하고, 
다른 사람이 두려워할 때 탐욕스러워하라"

🔗 <b>데이터 출처:</b> CNN Fear & Greed Index
🔍 <b>추출 방법:</b> {fear_greed_data.get('extraction_method', 'CSS 셀렉터')}

🤖 <i>정확한 CSS 셀렉터 기반 v3.0 (미국 시장 개장일만)</i>
        """
        
        return message.strip()
    
    def run(self):
        """메인 실행"""
        print("=" * 60)
        print("🎯 정확한 CSS 셀렉터 기반 CNN 스크래퍼 실행")
        print("=" * 60)
        
        try:
            if not self.should_send_message():
                print("✅ 휴장일 확인 - 알림 건너뛰기")
                return True
            
            message = self.create_daily_message()
            success = self.send_telegram_message(message)
            
            if success:
                print("✅ 정확한 CNN 지수 추출 및 전송 완료!")
                return True
            else:
                print("❌ 메시지 전송 실패")
                return False
                
        except Exception as e:
            print(f"❌ 실행 오류: {e}")
            return False

def main():
    try:
        notifier = PreciseCNNFearGreedNotifier()
        success = notifier.run()
        
        if success:
            print("\n🎉 정확한 CSS 셀렉터 기반 추출 성공!")
        else:
            print("\n💥 실행 실패!")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 치명적 오류: {e}")
        exit(1)

if __name__ == "__main__":
    main()
