import requests
import os
from datetime import datetime, date
import calendar

class FearGreedNotifier:
    def __init__(self):
        """
        GitHub Actions 환경에서 실행되는 Fear & Greed Index 알림 클래스
        환경변수에서 토큰과 채팅 ID를 가져옵니다.
        """
        # GitHub Secrets에서 환경변수로 가져오기
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = "https://api.alternative.me/fng/"
        
        # 환경변수 확인
        if not self.telegram_token or not self.chat_id:
            raise ValueError("TELEGRAM_TOKEN 또는 TELEGRAM_CHAT_ID가 설정되지 않았습니다.")
        
        print("✅ 환경변수 로드 완료")
        
    def get_fear_greed_index(self):
        """
        Fear & Greed Index 데이터를 가져오는 함수
        
        Returns:
            dict: 지수 정보가 담긴 딕셔너리
        """
        try:
            print("📊 Fear & Greed Index 데이터 요청 중...")
            
            # API에서 데이터 요청
            response = requests.get(self.api_url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            current_data = data['data'][0]
            
            result = {
                'value': int(current_data['value']),
                'classification': current_data['value_classification'],
                'timestamp': current_data['timestamp'],
                'time_until_update': current_data.get('time_until_update', 'Unknown')
            }
            
            print(f"✅ 데이터 수신 완료: {result['value']}/100")
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 오류: {e}")
            return None
        except (KeyError, ValueError) as e:
            print(f"❌ 데이터 파싱 오류: {e}")
            return None
    
    def get_trend_analysis(self):
        """
        최근 7일간의 추이 분석
        """
        try:
            print("📈 추이 분석 중...")
            response = requests.get(f"{self.api_url}?limit=7", timeout=15)
            response.raise_for_status()
            
            data = response.json()
            values = [int(item['value']) for item in data['data']]
            
            if len(values) >= 2:
                current = values[0]
                previous = values[1]
                change = current - previous
                
                if change > 0:
                    trend = f"📈 전일 대비 +{change}포인트 상승"
                elif change < 0:
                    trend = f"📉 전일 대비 {change}포인트 하락"
                else:
                    trend = "➡️ 전일과 동일"
                
                # 7일 평균 계산
                avg_7days = sum(values) / len(values)
                
                return trend, avg_7days
            else:
                return "📊 추이 데이터 부족", 0
                
        except Exception as e:
            print(f"❌ 추이 분석 오류: {e}")
            return "📊 추이 분석 불가", 0
    
    def is_us_market_closed(self):
        """
        미국 주식시장 휴장일인지 확인하는 함수
        NYSE, NASDAQ 기준
        
        Returns:
            bool: 휴장일이면 True
        """
        today = datetime.now()
        month = today.month
        day = today.day
        weekday = today.weekday()  # 0=월요일, 6=일요일
        
        # 주말 체크 (토, 일)
        if weekday >= 5:
            return True
            
        # 고정 휴장일들
        fixed_holidays = [
            (1, 1),   # New Year's Day (신정)
            (7, 4),   # Independence Day (독립기념일)
            (12, 25), # Christmas Day (크리스마스)
        ]
        
        if (month, day) in fixed_holidays:
            print(f"🇺🇸 미국 주식시장 휴장일입니다: {month}월 {day}일")
            return True
        
        # 변동 휴장일들 (간단 버전)
        # Martin Luther King Jr. Day (1월 셋째 월요일)
        if month == 1 and weekday == 0:  # 1월의 월요일
            # 1월의 세 번째 월요일 계산
            first_monday = 7 - (date(today.year, 1, 1).weekday() + 1) % 7 + 1
            third_monday = first_monday + 14
            if day == third_monday:
                print("🇺🇸 Martin Luther King Jr. Day - 미국 휴장일")
                return True
        
        # Presidents' Day (2월 셋째 월요일)
        if month == 2 and weekday == 0:
            first_monday = 7 - (date(today.year, 2, 1).weekday() + 1) % 7 + 1
            third_monday = first_monday + 14
            if day == third_monday:
                print("🇺🇸 Presidents' Day - 미국 휴장일")
                return True
        
        # Memorial Day (5월 마지막 월요일)
        if month == 5 and weekday == 0:
            # 5월의 마지막 월요일 찾기
            last_day = calendar.monthrange(today.year, 5)[1]
            last_monday = last_day - (date(today.year, 5, last_day).weekday() + 1) % 7
            if day == last_monday:
                print("🇺🇸 Memorial Day - 미국 휴장일")
                return True
        
        # Labor Day (9월 첫째 월요일)
        if month == 9 and weekday == 0:
            first_monday = 7 - (date(today.year, 9, 1).weekday() + 1) % 7 + 1
            if day == first_monday:
                print("🇺🇸 Labor Day - 미국 휴장일")
                return True
        
        # Thanksgiving Day (11월 넷째 목요일)
        if month == 11 and weekday == 3:  # 목요일
            first_thursday = 7 - (date(today.year, 11, 1).weekday() + 4) % 7 + 1
            fourth_thursday = first_thursday + 21
            if day == fourth_thursday:
                print("🇺🇸 Thanksgiving Day - 미국 휴장일")
                return True
        
        return False
    
    def should_send_message(self):
        """
        메시지를 전송해야 하는지 확인
        미국 주식시장 기준
        
        Returns:
            bool: 전송해야 하면 True
        """
        if self.is_us_market_closed():
            print("🇺🇸 미국 주식시장 휴장일이므로 알림을 전송하지 않습니다.")
            return False
        print("📈 미국 주식시장 개장일 확인 완료!")
        return True
        """
        지수 값에 따른 해석과 투자 가이드
        
        Args:
            value (int): Fear & Greed Index 값 (0-100)
            
        Returns:
            tuple: (해석, 조언, 이모지) 튜플
        """
        if value <= 25:
            interpretation = "🔴 극도의 공포 (Extreme Fear)"
            advice = "📈 가치투자 기회! 우량주 매수를 고려해보세요. 역발상 투자의 황금 타이밍일 수 있습니다."
            emoji = "😱"
            strategy = "💰 점진적 매수 전략 추천"
        elif value <= 45:
            interpretation = "🟠 공포 (Fear)" 
            advice = "📊 관심 종목들의 밸류에이션을 확인해보세요. 좋은 기업이 할인된 가격에 나올 수 있습니다."
            emoji = "😰"
            strategy = "🎯 선별적 매수 고려"
        elif value <= 55:
            interpretation = "🟡 중립 (Neutral)"
            advice = "⚖️ 평소와 같이 꾸준한 투자를 유지하세요. 정기 적립투자에 좋은 시기입니다."
            emoji = "😐"
            strategy = "🔄 정기투자 유지"
        elif value <= 75:
            interpretation = "🟢 탐욕 (Greed)"
            advice = "⚠️ 과열 구간 진입. 신중한 매수가 필요하며, 고평가된 종목은 피하는 것이 좋습니다."
            emoji = "😊"
            strategy = "🚨 신중한 투자 필요"
        else:
            interpretation = "🔥 극도의 탐욕 (Extreme Greed)"
            advice = "🚨 고평가 구간! 일부 매도를 고려하고 현금 비중을 늘리는 것을 추천합니다."
            emoji = "🤑"
            strategy = "💸 차익실현 고려"
            
        return interpretation, advice, emoji, strategy
    
    def send_telegram_message(self, message):
        """
        텔레그램으로 메시지 전송
        
        Args:
            message (str): 전송할 메시지
            
        Returns:
            bool: 전송 성공 여부
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
        
        Returns:
            str: 완성된 메시지
        """
        # Fear & Greed Index 데이터 가져오기
        fear_greed_data = self.get_fear_greed_index()
        
        if not fear_greed_data:
            return "❌ Fear & Greed Index 데이터를 가져올 수 없습니다. 나중에 다시 시도해주세요."
        
        # 추이 분석
        trend, avg_7days = self.get_trend_analysis()
        
        # 현재 시간 (한국시간)
        current_time = datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")
        
        # 지수 해석
        interpretation, advice, emoji, strategy = self.interpret_index(fear_greed_data['value'])
        
        # 지수에 따른 진행바 생성
        value = fear_greed_data['value']
        filled_bars = value // 10
        progress_bar = "🟩" * filled_bars + "⬜" * (10 - filled_bars)
        
        # 7일 평균과 비교
        if avg_7days > 0:
            vs_avg = value - avg_7days
            if vs_avg > 5:
                avg_comment = f"📊 7일 평균({avg_7days:.1f})보다 높음 (+{vs_avg:.1f})"
            elif vs_avg < -5:
                avg_comment = f"📊 7일 평균({avg_7days:.1f})보다 낮음 ({vs_avg:.1f})"
            else:
                avg_comment = f"📊 7일 평균({avg_7days:.1f})과 비슷한 수준"
        else:
            avg_comment = "📊 평균 비교 데이터 없음"
        
        # 메시지 구성
        message = f"""
🌅 <b>오늘의 암호화폐 공포&탐욕 지수</b> {emoji}
📅 {current_time} (미국 시장 개장일)

📊 <b>현재 지수: {fear_greed_data['value']}/100</b>
{progress_bar}
{interpretation}

📈 <b>시장 분석</b>
• {trend}
• {avg_comment}
• 상태: {fear_greed_data['classification']}

💡 <b>가치투자자 가이드</b>
{advice}

🎯 <b>투자 전략</b>
{strategy}

🇺🇸 <b>미국 시장 연계 분석</b>
암호화폐와 미국 주식시장은 상관관계가 높으니
오늘 미국 시장 동향도 함께 체크해보세요!

📚 <b>투자 원칙 reminder</b>
"시장의 감정에 휘둘리지 말고, 기업의 본질적 가치에 집중하세요!"

📖 <b>워렌 버핏의 명언</b>
"다른 사람이 탐욕스러울 때 두려워하고, 
다른 사람이 두려워할 때 탐욕스러워하라"

🤖 <i>GitHub Actions 자동 전송 (미국 시장 개장일만) | 출처: Alternative.me</i>
        """
        
        return message.strip()
    
    def run(self):
        """
        메인 실행 함수
        """
        print("=" * 60)
        print("📱 Fear & Greed Index GitHub Actions 실행 시작")
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
        # Fear & Greed 알림 객체 생성 및 실행
        notifier = FearGreedNotifier()
        success = notifier.run()
        
        if success:
            print("\n🎉 GitHub Actions 실행 성공!")
        else:
            print("\n💥 GitHub Actions 실행 실패!")
            exit(1)  # 실패시 종료 코드 1 반환
            
    except Exception as e:
        print(f"\n💥 치명적 오류: {e}")
        exit(1)

if __name__ == "__main__":
    main()
