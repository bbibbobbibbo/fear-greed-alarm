import requests
import os
from datetime import datetime, date
import calendar
import re
from bs4 import BeautifulSoup
import json
import time

class RobustCNNFearGreedNotifier:
    def __init__(self):
        """
        견고한 CNN Fear & Greed Index 추출기
        특정 값에 의존하지 않고 구조 기반으로 추출
        """
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.cnn_url = "https://edition.cnn.com/markets/fear-and-greed"
        
        if not self.telegram_token or not self.chat_id:
            raise ValueError("TELEGRAM_TOKEN 또는 TELEGRAM_CHAT_ID가 설정되지 않았습니다.")
        
        print("✅ 환경변수 로드 완료")
    
    def get_cnn_fear_greed_index(self):
        """
        CNN Fear & Greed Index를 견고하게 추출
        """
        try:
            print("📊 CNN Fear & Greed Index 데이터 요청 중...")
            
            # 다양한 User-Agent로 시도
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
            ]
            
            for attempt, user_agent in enumerate(user_agents, 1):
                print(f"🔄 시도 {attempt}/{len(user_agents)}: {user_agent[:50]}...")
                
                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'DNT': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none'
                }
                
                try:
                    response = requests.get(self.cnn_url, headers=headers, timeout=20)
                    response.raise_for_status()
                    
                    if len(response.text) > 50000:  # 충분한 내용이 로드됨
                        print(f"✅ CNN 페이지 로드 성공 ({len(response.text):,} 글자)")
                        break
                    else:
                        print(f"⚠️ 페이지 내용 부족 ({len(response.text)} 글자)")
                        
                except Exception as e:
                    print(f"❌ 시도 {attempt} 실패: {e}")
                    if attempt < len(user_agents):
                        time.sleep(2)  # 잠시 대기
                        continue
                    else:
                        raise
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 다단계 추출 시스템
            extraction_methods = [
                ('핵심 패턴', self._extract_core_patterns),
                ('JavaScript 객체', self._extract_js_objects), 
                ('DOM 구조', self._extract_dom_structure),
                ('메타데이터', self._extract_metadata),
                ('컨텍스트 분석', self._extract_contextual),
                ('백업 패턴', self._extract_backup_patterns)
            ]
            
            for method_name, extraction_func in extraction_methods:
                print(f"\n🔍 {method_name} 추출 시도...")
                try:
                    result = extraction_func(response.text, soup)
                    if result and self._validate_score(result):
                        print(f"✅ {method_name}에서 성공: {result['value']}")
                        result['extraction_method'] = method_name
                        return result
                    elif result:
                        print(f"⚠️ {method_name} 결과 검증 실패: {result.get('value', 'None')}")
                except Exception as e:
                    print(f"❌ {method_name} 오류: {e}")
                    continue
            
            print("❌ 모든 추출 방법 실패")
            return None
            
        except Exception as e:
            print(f"❌ CNN 데이터 추출 전체 오류: {e}")
            return None
    
    def _extract_core_patterns(self, html_text, soup):
        """
        핵심 Fear & Greed 패턴으로 추출
        """
        # CNN의 실제 구조를 반영한 정확한 패턴들
        core_patterns = [
            # JavaScript 변수/객체 패턴
            r'(?:fear.*greed|fearGread|fearAndGreed).*?["\']?(?:score|value|index|current)["\']?\s*[:=]\s*["\']?(\d{1,2})["\']?',
            r'["\'](?:score|value|index)["\']?\s*[:=]\s*["\']?(\d{1,2})["\']?.*?(?:fear|greed)',
            
            # HTML 데이터 속성 패턴
            r'data-(?:fear-greed-)?(?:score|value|index|current)["\s]*=["\s]*(\d{1,2})["\s]*',
            r'(?:id|class)["\s]*=["\s]*[^"]*(?:fear.*greed|greed.*fear)[^"]*["\s]*[^>]*>.*?(\d{1,2})',
            
            # JSON 구조 패턴
            r'\{[^}]*(?:fear|greed)[^}]*["\'](?:score|value|index)["\']?\s*:\s*["\']?(\d{1,2})["\']?[^}]*\}',
            r'\{[^}]*["\'](?:score|value|index)["\']?\s*:\s*["\']?(\d{1,2})["\']?[^}]*(?:fear|greed)[^}]*\}',
            
            # 스크립트 내 직접 할당 패턴
            r'(?:var|let|const)\s+(?:fear.*greed|score|index)\s*=\s*["\']?(\d{1,2})["\']?',
            r'(?:fear.*greed|score|index)\s*=\s*["\']?(\d{1,2})["\']?',
        ]
        
        for i, pattern in enumerate(core_patterns, 1):
            try:
                matches = list(re.finditer(pattern, html_text, re.IGNORECASE | re.DOTALL))
                
                if matches:
                    print(f"  패턴 {i}: {len(matches)}개 매치")
                    
                    for match in matches:
                        score = int(match.group(1))
                        
                        # 컨텍스트 검증
                        context = self._get_match_context(html_text, match, 300)
                        confidence = self._calculate_confidence(context, score)
                        
                        if confidence >= 0.7:  # 70% 이상 신뢰도
                            print(f"    ✅ 높은 신뢰도 점수: {score} (신뢰도: {confidence:.2f})")
                            return {
                                'value': score,
                                'classification': self._get_classification(score),
                                'source': 'CNN Fear & Greed Index',
                                'confidence': confidence,
                                'pattern_used': f'core_pattern_{i}',
                                'context_preview': context[:100] + '...'
                            }
                        elif confidence >= 0.4:
                            print(f"    📊 중간 신뢰도 점수: {score} (신뢰도: {confidence:.2f})")
                            # 일단 저장해두고 더 좋은 것이 없으면 사용
                            
            except Exception as e:
                print(f"  패턴 {i} 오류: {e}")
                continue
        
        return None
    
    def _extract_js_objects(self, html_text, soup):
        """
        JavaScript 객체에서 추출
        """
        script_tags = soup.find_all('script')
        print(f"  총 {len(script_tags)}개 스크립트 태그 분석...")
        
        # Fear & Greed 관련 스크립트만 필터링
        relevant_scripts = []
        for script in script_tags:
            if script.string:
                script_lower = script.string.lower()
                if any(keyword in script_lower for keyword in ['fear', 'greed', 'market', 'index']):
                    relevant_scripts.append(script.string)
        
        print(f"  관련 스크립트 {len(relevant_scripts)}개 발견")
        
        for i, script_content in enumerate(relevant_scripts):
            try:
                # JSON 객체 패턴 찾기
                json_patterns = [
                    r'\{[^{}]*(?:fear|greed)[^{}]*\}',
                    r'\{[^{}]*(?:score|value|index)[^{}]*\}',
                    r'(?:fearGreed|fearAndGreed|marketSentiment)\s*[:=]\s*(\{[^}]+\})',
                ]
                
                for pattern in json_patterns:
                    matches = re.finditer(pattern, script_content, re.IGNORECASE | re.DOTALL)
                    
                    for match in matches:
                        try:
                            # JSON 파싱 시도
                            json_str = match.group(1) if match.groups() else match.group(0)
                            
                            # JSON 정리 (JavaScript 객체를 JSON으로 변환)
                            json_str = re.sub(r'([{,]\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:', r'\1"\2":', json_str)
                            json_str = re.sub(r"'([^']*)'", r'"\1"', json_str)
                            
                            data = json.loads(json_str)
                            score = self._find_score_in_data(data)
                            
                            if score and 0 <= score <= 100:
                                print(f"    ✅ JSON 객체에서 점수 발견: {score}")
                                return {
                                    'value': score,
                                    'classification': self._get_classification(score),
                                    'source': 'CNN Fear & Greed Index',
                                    'confidence': 0.9,
                                    'extraction_method': 'js_object'
                                }
                                
                        except json.JSONDecodeError:
                            # JSON 파싱 실패는 정상적, 계속 진행
                            continue
                            
            except Exception as e:
                print(f"  스크립트 {i} 분석 오류: {e}")
                continue
        
        return None
    
    def _extract_dom_structure(self, html_text, soup):
        """
        DOM 구조 기반 추출
        """
        # Fear & Greed 관련 텍스트를 포함한 요소들 찾기
        fear_greed_elements = soup.find_all(text=re.compile(r'fear.*greed|greed.*fear', re.IGNORECASE))
        print(f"  Fear/Greed 텍스트 요소 {len(fear_greed_elements)}개 발견")
        
        candidates = []
        
        for element in fear_greed_elements:
            try:
                parent = element.parent
                if not parent:
                    continue
                
                # 부모와 형제 요소들에서 숫자 찾기
                for level in range(3):  # 3단계까지 올라가면서 확인
                    if not parent:
                        break
                    
                    # 현재 레벨의 모든 텍스트 수집
                    all_text = ' '.join(parent.get_text(separator=' ', strip=True).split())
                    
                    # 숫자 패턴 찾기
                    number_patterns = [
                        r'\b(\d{1,2})\b(?!\d)',  # 기본 1-2자리 숫자
                        r'(\d{1,2})(?:\.\d+)?',  # 소수점 포함
                        r'(?:score|index|value).*?(\d{1,2})',  # 키워드 뒤 숫자
                        r'(\d{1,2}).*?(?:score|index|value)',  # 숫자 뒤 키워드
                    ]
                    
                    for pattern in number_patterns:
                        numbers = re.findall(pattern, all_text)
                        for num_str in numbers:
                            try:
                                score = int(float(num_str))
                                if 0 <= score <= 100:
                                    # 컨텍스트 품질 평가
                                    context_quality = self._evaluate_context_quality(all_text, score)
                                    candidates.append({
                                        'score': score,
                                        'context': all_text[:200],
                                        'quality': context_quality,
                                        'level': level
                                    })
                            except ValueError:
                                continue
                    
                    parent = parent.parent
                    
            except Exception as e:
                print(f"  DOM 요소 분석 오류: {e}")
                continue
        
        # 가장 품질 좋은 후보 선택
        if candidates:
            best_candidate = max(candidates, key=lambda x: x['quality'])
            print(f"    ✅ DOM에서 최적 점수: {best_candidate['score']} (품질: {best_candidate['quality']:.2f})")
            
            if best_candidate['quality'] >= 0.6:
                return {
                    'value': best_candidate['score'],
                    'classification': self._get_classification(best_candidate['score']),
                    'source': 'CNN Fear & Greed Index',
                    'confidence': best_candidate['quality'],
                    'extraction_method': 'dom_structure'
                }
        
        return None
    
    def _extract_metadata(self, html_text, soup):
        """
        메타데이터에서 추출
        """
        # 메타 태그들 확인
        meta_tags = soup.find_all('meta')
        
        for meta in meta_tags:
            content = meta.get('content', '')
            name = meta.get('name', '')
            property_name = meta.get('property', '')
            
            all_meta_text = f"{name} {property_name} {content}".lower()
            
            if any(keyword in all_meta_text for keyword in ['fear', 'greed', 'market', 'sentiment']):
                numbers = re.findall(r'\b(\d{1,2})\b', content)
                for num_str in numbers:
                    score = int(num_str)
                    if 0 <= score <= 100:
                        print(f"    ✅ 메타데이터에서 점수: {score}")
                        return {
                            'value': score,
                            'classification': self._get_classification(score),
                            'source': 'CNN Fear & Greed Index',
                            'confidence': 0.7,
                            'extraction_method': 'metadata'
                        }
        
        return None
    
    def _extract_contextual(self, html_text, soup):
        """
        컨텍스트 분석 기반 추출
        """
        # 페이지를 줄 단위로 분석
        lines = html_text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Fear & Greed 관련 줄 찾기
            if any(keyword in line_lower for keyword in ['fear', 'greed']):
                # 앞뒤 5줄씩 컨텍스트 수집
                context_start = max(0, i - 5)
                context_end = min(len(lines), i + 6)
                context_lines = lines[context_start:context_end]
                context = ' '.join(context_lines)
                
                # 이 컨텍스트에서 가장 적절한 숫자 찾기
                numbers = re.findall(r'\b(\d{1,2})\b', context)
                
                if numbers:
                    # 숫자들의 적절성 평가
                    number_scores = []
                    for num_str in numbers:
                        score = int(num_str)
                        if 0 <= score <= 100:
                            appropriateness = self._evaluate_number_appropriateness(context, score, line_lower)
                            number_scores.append((score, appropriateness))
                    
                    if number_scores:
                        # 가장 적절한 점수 선택
                        best_score, best_appropriateness = max(number_scores, key=lambda x: x[1])
                        
                        if best_appropriateness >= 0.5:
                            print(f"    ✅ 컨텍스트에서 점수: {best_score} (적절성: {best_appropriateness:.2f})")
                            return {
                                'value': best_score,
                                'classification': self._get_classification(best_score),
                                'source': 'CNN Fear & Greed Index',
                                'confidence': best_appropriateness,
                                'extraction_method': 'contextual'
                            }
        
        return None
    
    def _extract_backup_patterns(self, html_text, soup):
        """
        백업 패턴들로 최후 시도
        """
        # 매우 관대한 패턴들 (false positive 위험 있지만 마지막 수단)
        backup_patterns = [
            r'(?:current|today|now).*?(\d{1,2})(?!\d)',
            r'(\d{1,2})(?!\d).*?(?:current|today|now)',
            r'market.*?(\d{1,2})(?!\d)',
            r'(\d{1,2})(?!\d).*?market',
            r'index.*?(\d{1,2})(?!\d)',
            r'(\d{1,2})(?!\d).*?index',
        ]
        
        page_numbers = []
        
        for pattern in backup_patterns:
            matches = re.finditer(pattern, html_text, re.IGNORECASE)
            for match in matches:
                score = int(match.group(1))
                if 20 <= score <= 90:  # 더 제한적인 범위
                    context = self._get_match_context(html_text, match, 200)
                    if any(keyword in context.lower() for keyword in ['fear', 'greed', 'market', 'emotion']):
                        page_numbers.append(score)
        
        if page_numbers:
            # 가장 자주 나타나는 숫자 선택
            from collections import Counter
            most_common = Counter(page_numbers).most_common(1)
            if most_common:
                score = most_common[0][0]
                print(f"    ✅ 백업 패턴에서 점수: {score} (빈도: {most_common[0][1]})")
                return {
                    'value': score,
                    'classification': self._get_classification(score),
                    'source': 'CNN Fear & Greed Index',
                    'confidence': 0.4,
                    'extraction_method': 'backup_pattern'
                }
        
        return None
    
    def _get_match_context(self, text, match, context_size):
        """매치 주변 컨텍스트 추출"""
        start = max(0, match.start() - context_size)
        end = min(len(text), match.end() + context_size)
        return text[start:end]
    
    def _calculate_confidence(self, context, score):
        """컨텍스트 기반 신뢰도 계산"""
        confidence = 0.0
        context_lower = context.lower()
        
        # Fear & Greed 키워드
        if 'fear' in context_lower and 'greed' in context_lower:
            confidence += 0.4
        elif 'fear' in context_lower or 'greed' in context_lower:
            confidence += 0.2
        
        # 관련 키워드들
        keywords = ['index', 'market', 'sentiment', 'emotion', 'score', 'current']
        keyword_count = sum(1 for keyword in keywords if keyword in context_lower)
        confidence += min(keyword_count * 0.1, 0.3)
        
        # 점수 범위 합리성
        if 20 <= score <= 80:
            confidence += 0.2
        elif 10 <= score <= 90:
            confidence += 0.1
        
        # 숫자가 적절한 위치에 있는지
        if re.search(r'(?:score|index|value).*?' + str(score), context_lower):
            confidence += 0.2
        elif re.search(str(score) + r'.*?(?:score|index|value)', context_lower):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _evaluate_context_quality(self, context, score):
        """컨텍스트 품질 평가"""
        return self._calculate_confidence(context, score)
    
    def _evaluate_number_appropriateness(self, context, score, trigger_line):
        """숫자의 적절성 평가"""
        appropriateness = 0.0
        
        # Fear & Greed 트리거 라인에 더 높은 점수
        if 'fear' in trigger_line and 'greed' in trigger_line:
            appropriateness += 0.5
        
        # 컨텍스트 품질
        appropriateness += self._calculate_confidence(context, score) * 0.5
        
        return appropriateness
    
    def _find_score_in_data(self, data):
        """JSON 데이터에서 점수 찾기"""
        if isinstance(data, dict):
            for key, value in data.items():
                if any(keyword in key.lower() for keyword in ['score', 'index', 'value', 'fear', 'greed']):
                    if isinstance(value, (int, str)) and str(value).isdigit():
                        score = int(value)
                        if 0 <= score <= 100:
                            return score
                
                result = self._find_score_in_data(value)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self._find_score_in_data(item)
                if result:
                    return result
        
        return None
    
    def _validate_score(self, result):
        """추출된 점수의 유효성 검증"""
        if not result or 'value' not in result:
            return False
        
        score = result['value']
        
        # 기본 범위 체크
        if not (0 <= score <= 100):
            return False
        
        # 신뢰도 체크
        confidence = result.get('confidence', 0.5)
        if confidence < 0.3:
            return False
        
        return True
    
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
            return "❌ CNN Fear & Greed Index 데이터를 가져올 수 없습니다. 사이트 구조가 변경되었거나 접속에 문제가 있을 수 있습니다."
        
        current_time = datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")
        interpretation, advice, emoji, strategy = self.interpret_index(fear_greed_data['value'])
        
        value = fear_greed_data['value']
        filled_bars = value // 10
        progress_bar = "🟩" * filled_bars + "⬜" * (10 - filled_bars)
        
        confidence = fear_greed_data.get('confidence', 0.5)
        confidence_text = f"신뢰도 {confidence:.0%}"
        
        extraction_method = fear_greed_data.get('extraction_method', '알 수 없음')
        
        message = f"""
🇺🇸 <b>미국 주식시장 Fear & Greed Index</b> {emoji}
📅 {current_time} ({confidence_text})

📊 <b>현재 지수: {fear_greed_data['value']}/100</b>
{progress_bar}
{interpretation}

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
🔍 <b>추출 방법:</b> {extraction_method}

🤖 <i>견고한 CNN 스크래퍼 v2.0 (미국 시장 개장일만)</i>
        """
        
        return message.strip()
    
    def run(self):
        """메인 실행"""
        print("=" * 60)
        print("🇺🇸 견고한 CNN Fear & Greed Index 스크래퍼 실행")
        print("=" * 60)
        
        try:
            if not self.should_send_message():
                print("✅ 휴장일 확인 - 알림 건너뛰기")
                return True
            
            message = self.create_daily_message()
            success = self.send_telegram_message(message)
            
            if success:
                print("✅ CNN 지수 추출 및 전송 완료!")
                return True
            else:
                print("❌ 메시지 전송 실패")
                return False
                
        except Exception as e:
            print(f"❌ 실행 오류: {e}")
            return False

def main():
    try:
        notifier = RobustCNNFearGreedNotifier()
        success = notifier.run()
        
        if success:
            print("\n🎉 견고한 CNN 스크래퍼 성공!")
        else:
            print("\n💥 실행 실패!")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 치명적 오류: {e}")
        exit(1)

if __name__ == "__main__":
    main()
