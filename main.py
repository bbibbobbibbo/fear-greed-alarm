import requests
import os
from datetime import datetime, date
import calendar
import re
from bs4 import BeautifulSoup
import json

class CNNFearGreedNotifier:
    def __init__(self):
        """
        CNN Fear & Greed Index 텔레그램 알림 클래스
        미국 주식시장 기반 지수 사용
        """
        # GitHub Secrets에서 환경변수로 가져오기
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.cnn_url = "https://edition.cnn.com/markets/fear-and-greed"
        
        # 환경변수 확인
        if not self.telegram_token or not self.chat_id:
            raise ValueError("TELEGRAM_TOKEN 또는 TELEGRAM_CHAT_ID가 설정되지 않았습니다.")
        
        print("✅ 환경변수 로드 완료")
        
    def get_cnn_fear_greed_index(self):
        """
        CNN Fear & Greed Index 데이터를 스크래핑으로 가져오는 함수
        
        Returns:
            dict: 지수 정보가 담긴 딕셔너리
        """
        try:
            print("📊 CNN Fear & Greed Index 데이터 요청 중...")
            
            # User-Agent 설정 (봇 차단 방지)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # CNN 페이지 요청
            response = requests.get(self.cnn_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # BeautifulSoup으로 HTML 파싱
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 방법 1: JSON 데이터 찾기 (스크립트 태그에서)
            fear_greed_data = self._extract_from_script_tags(soup)
            if fear_greed_data:
                return fear_greed_data
            
            # 방법 2: HTML 요소에서 직접 추출
            fear_greed_data = self._extract_from_html_elements(soup)
            if fear_greed_data:
                return fear_greed_data
            
            # 방법 3: 텍스트 패턴 매칭
            fear_greed_data = self._extract_from_text_patterns(response.text)
            if fear_greed_data:
                return fear_greed_data
            
            print("❌ CNN 데이터를 추출할 수 없습니다.")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"❌ CNN 사이트 접속 오류: {e}")
            return None
        except Exception as e:
            print(f"❌ 데이터 파싱 오류: {e}")
            return None
    
    def _extract_from_script_tags(self, soup):
        """
        스크립트 태그에서 JSON 데이터 추출
        """
        try:
            # 스크립트 태그들을 검색
            script_tags = soup.find_all('script')
            
            for script in script_tags:
                if script.string and 'fear' in script.string.lower():
                    text = script.string
                    
                    # JSON 패턴 찾기
                    json_patterns = [
                        r'"fearAndGreedScore"[:\s]*(\d+)',
                        r'"score"[:\s]*(\d+)',
                        r'"currentScore"[:\s]*(\d+)',
                        r'fearGreed["\']?[:\s]*(\d+)',
                    ]
                    
                    for pattern in json_patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            score = int(match.group(1))
                            if 0 <= score <= 100:
                                print(f"✅ 스크립트에서 지수 발견: {score}")
                                return {
                                    'value': score,
                                    'classification': self._get_classification(score),
                                    'source': 'CNN Fear & Greed Index',
                                    'extraction_method': 'script_tag'
                                }
            
            return None
            
        except Exception as e:
            print(f"스크립트 추출 오류: {e}")
            return None
    
    def _extract_from_html_elements(self, soup):
        """
        HTML 요소에서 직접 추출
        """
        try:
            # 가능한 CSS 선택자들
            selectors = [
                '[data-module="FearGreedIndex"]',
                '.fear-greed-score',
                '.fear-greed-number',
                '.gauge-score',
                '.index-score',
                'div[class*="fear"]',
                'span[class*="score"]',
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    
                    # 숫자 패턴 찾기
                    numbers = re.findall(r'\b(\d{1,2})\b', text)
                    for num_str in numbers:
                        score = int(num_str)
                        if 0 <= score <= 100:
                            print(f"✅ HTML 요소에서 지수 발견: {score}")
                            return {
                                'value': score,
                                'classification': self._get_classification(score),
                                'source': 'CNN Fear & Greed Index',
                                'extraction_method': 'html_element'
                            }
            
            return None
            
        except Exception as e:
            print(f"HTML 요소 추출 오류: {e}")
            return None
    
    def _extract_from_text_patterns(self, html_text):
        """
        텍스트 패턴 매칭으로 추출
        """
        try:
            # 다양한 패턴으로 검색
            patterns = [
                r'Fear\s*(?:&|and)\s*Greed\s*(?:Index)?[:\s]*(\d{1,2})',
                r'Current\s*(?:Score|Index)[:\s]*(\d{1,2})',
                r'Index[:\s]*(\d{1,2})',
                r'"score"[:\s]*(\d{1,2})',
                r'data-score["\s]*=["\s]*(\d{1,2})',
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, html_text, re.IGNORECASE)
                for match in matches:
                    score = int(match.group(1))
                    if 0 <= score <= 100:
                        print(f"✅ 텍스트 패턴에서 지수 발견: {score}")
                        return {
                            'value': score,
                            'classification': self._get_classification(score),
                            'source': 'CNN Fear & Greed Index',
                            'extraction_method': 'text_pattern'
                        }
            
            return None
            
        except Exception as e:
            print(f"텍스트 패턴 추출 오류: {e}")
            return None
    
    def _get_classification(self, value):
        """
        CNN 기준 분류 (미국 주식시장)
        """
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
    
    def get_fallback_data(self):
        """
        CNN에서 데이터를 가져올 수 없을 때 대체 데이터
        """
        try:
            print("🔄 대체 데이터 소스 시도 중...")
            
            # MarketWatch Fear & Greed 시도
            marketwatch_url = "https://www.marketwatch.com/investing/index/spx"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(marketwatch_url, headers=headers, timeout=10)
            
            # VIX 지수를 기반으로 간단한 Fear & Greed 추정
            vix_pattern = r'VIX[^\d]*(\d+\.?\d*)'
            vix_match = re.search(vix_pattern, response.text, re.IGNORECASE)
            
            if vix_match:
                vix_value = float(vix_match.group(1))
                # VIX를 Fear & Greed로 변환 (간단한 공식)
                # VIX 낮음 = 탐욕, VIX 높음 = 공포
                if vix_value < 15:
                    fear_greed = 75  # 탐욕
                elif vix_value < 20:
                    fear_greed = 60  # 약간 탐욕
                elif vix_value < 25:
                    fear_greed = 50  # 중립
                elif vix_value < 30:
                    fear_greed = 35  # 공포
                else:
                    fear_greed = 20  # 극도의 공포
                
                print(f"✅ VIX {vix_value} 기반 Fear & Greed: {fear_greed}")
                return {
                    'value': fear_greed,
                    'classification': self._get_classification(fear_greed),
                    'source': f'VIX-based estimate (VIX: {vix_value})',
                    'extraction_method': 'fallback_vix'
                }
            
            return None
            
        except Exception as e:
            print(f"대체 데이터 오류: {e}")
            return None
    
    def interpret_index(self, value):
        """
        CNN Fear & Greed Index 해석 (미국 주식시장 기준)
        
        Args:
            value (int): Fear & Greed Index 값 (0-100)
            
        Returns:
            tuple: (해석, 조언, 이모지, 전략) 튜플
        """
        if value <= 25:
            interpretation = "🔴 극도의 공포 (Extreme Fear)"
            advice = "📈 미국 주식시장이 극도로 두려워하고 있습니다. 워렌 버핏의 조언대로 '남이 두려워할 때 탐욕스러워하라'는 시점일 수 있습니다."
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
        """
        미국 주식시장 휴장일인지 확인하는 함수
        """
        today = datetime.now()
        month = today.month
        day = today.day
        weekday = today.weekday()  # 0=월요일, 6=일요일
        
        # 주말 체크 (토, 일)
        if weekday >= 5:
            print(f"🇺🇸 주말입니다 ({['월','화','수','목','금','토','일'][weekday]}요일)")
            return True
            
        # 고정 휴장일들
        fixed_holidays = [
            (1, 1),   # New Year's Day
            (7, 4),   # Independence Day
            (12, 25), # Christmas Day
        ]
        
        if (month, day) in fixed_holidays:
            print(f"🇺🇸 미국 주식시장 휴장일입니다: {month}월 {day}일")
            return True
        
        return False
    
    def should_send_message(self):
        """
        메시지를 전송해야 하는지 확인
        """
        if self.is_us_market_closed():
            print("🇺🇸 미국 주식시장 휴장일이므로 알림을 전송하지 않습니다.")
            return False
        print("📈 미국 주식시장 개장일 확인 완료!")
        return True
    
    def send_telegram_message(self, message):
        """
        텔레그램으로 메시지 전송
        """
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
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 텔레그램 전송 실패: {e}")
            return False
    
    def create_daily_message(self):
        """
        매일 전송할 메시지 생성
        """
        # CNN Fear & Greed Index 데이터 가져오기
        fear_greed_data = self.get_cnn_fear_greed_index()
        
        # CNN에서 실패하면 대체 데이터 시도
        if not fear_greed_data:
            fear_greed_data = self.get_fallback_data()
        
        if not fear_greed_data:
            return "❌ Fear & Greed Index 데이터를 가져올 수 없습니다. CNN 사이트에 접속할 수 없거나 구조가 변경되었을 수 있습니다."
        
        # 현재 시간 (한국시간)
        current_time = datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")
        
        # 지수 해석
        interpretation, advice, emoji, strategy = self.interpret_index(fear_greed_data['value'])
        
        # 지수에 따른 진행바 생성
        value = fear_greed_data['value']
        filled_bars = value // 10
        progress_bar = "🟩" * filled_bars + "⬜" * (10 - filled_bars)
        
        # 메시지 구성
        message = f"""
🇺🇸 <b>미국 주식시장 Fear & Greed Index</b> {emoji}
📅 {current_time} (CNN 데이터 기반)

📊 <b>현재 지수: {fear_greed_data['value']}/100</b>
{progress_bar}
{interpretation}

💡 <b>가치투자자 가이드</b>
{advice}

🎯 <b>투자 전략</b>
{strategy}

📈 <b>CNN Fear & Greed Index 구성요소</b>
• 주식 가격 모멘텀 (Stock Price Momentum)
• 주식 가격 강도 (Stock Price Strength)  
• 주식 시장 폭 (Stock Price Breadth)
• 풋/콜 옵션 비율 (Put/Call Options)
• 정크본드 수요 (Junk Bond Demand)
• 시장 변동성 VIX (Market Volatility)
• 안전자산 수요 (Safe Haven Demand)

📚 <b>워렌 버핏의 투자 원칙</b>
"다른 사람이 탐욕스러울 때 두려워하고, 
다른 사람이 두려워할 때 탐욕스러워하라"

🔗 <b>데이터 출처</b>
{fear_greed_data['source']}

🤖 <i>GitHub Actions 자동 전송 (미국 시장 개장일만)</i>
        """
        
        return message.strip()
    
    def run(self):
        """
        메인 실행 함수
        """
        print("=" * 60)
        print("🇺🇸 CNN Fear & Greed Index GitHub Actions 실행 시작")
        print("=" * 60)
        
        try:
            # 미국 주식시장 휴장일 체크
            if not self.should_send_message():
                print("✅ 미국 주식시장 휴장일 체크 완료 - 알림 건너뛰기")
                return True
            
            print("📊 미국 주식시장 개장일 확인 완료 - 알림 전송을 시작합니다")
            
            # 메시지 생성 및 전송
            message = self.create_daily_message()
            success = self.send_telegram_message(message)
            
            if success:
                print("✅ 일일 리포트 전송 완료!")
                return True
            else:
                print("❌ 메시지 전송 실패")
                return False
                
        except Exception as e:
            print(f"❌ 실행 중 오류 발생: {e}")
            return False

def main():
    """
    GitHub Actions에서 실행되는 메인 함수
    """
    try:
        # CNN Fear & Greed 알림 객체 생성 및 실행
        notifier = CNNFearGreedNotifier()
        success = notifier.run()
        
        if success:
            print("\n🎉 GitHub Actions 실행 성공!")
        else:
            print("\n💥 GitHub Actions 실행 실패!")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 치명적 오류: {e}")
        exit(1)

if __name__ == "__main__":
    main()
