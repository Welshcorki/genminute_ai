import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
class STTManager:
    def __init__(self):
        load_dotenv() # 환경 변수 로드

    @staticmethod
    def _parse_mmss_to_seconds(time_str):
        """
        '분:초:밀리초' 형태의 문자열을 초 단위로 변환합니다.
        """
        try:
            parts = time_str.split(":")
            if len(parts) == 3:
                minutes = int(parts[0])
                seconds = int(parts[1])
                milliseconds = int(parts[2])
                return minutes * 60 + seconds + milliseconds / 1000.0
            else:
                return 0.0
        except:
            return 0.0
        
    
    def transcribe_audio(self, audio_path):
        """Google Gemini STT API로 음성 인식"""
        try:
            import threading
            import datetime
            thread_id = threading.current_thread().name
            timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp}][{thread_id}] 🎧 Gemini STT API로 음성 인식 중: {audio_path}")
            api_key = os.environ.get("GOOGLE_API_KEY")
            if api_key:
                client = genai.Client(api_key=api_key)
            else:
                client = genai.Client()

            with open(audio_path, "rb") as f:
                file_bytes = f.read()

            file_ext = os.path.splitext(audio_path)[1].lower()
            mime_type_map = {
                ".wav": "audio/wav", ".mp3": "audio/mp3",
                ".m4a": "audio/mp4", ".flac": "audio/flac",
            }
            mime_type = mime_type_map.get(file_ext, "audio/wav")

            prompt = """
            당신은 최고 수준의 정확도를 가진 전문적인 회의록 STT 시스템입니다. 제공된 오디오 파일을 듣고 다음의 지침에 따라 텍스트 변환 및 화자 분리 작업을 엄격하게 수행해 주십시오.

            I. 핵심 지침 (오류 방지)
            1. 충실도 우선: 제공된 오디오에서 실제 발화된 내용만을 인식하여 텍스트로 변환하는 작업에 최대한 집중하며, 구어체 발화를 문어체로 정제하지 마십시오.
            2. 금지 사항: 절대 문장 보정 오류(안 들리는 부분 임의 생성), 동사 생성/보정, 불필요한 단어 추가("그러니까", "이 지금", "뭐" 등 문맥 외 단어)를 하지 마십시오. 이 오류들은 회의록의 신뢰도를 심각하게 저해합니다.
            3. 단어 정확성 및 문맥 보정: 들리는 음운에 충실하되, 문맥상 명백히 오류이거나 회의록의 주제와 관련성이 현저히 높은 유사 발음 단어가 있다면, 문맥을 기반으로 더 적절한 단어로 보정하십시오. (예: 문맥이 '주식 투자'라면 '지구'를 '지분'으로, '예쁘게 쓰면'을 '예쁘게 스면'으로 보정) 단, 문맥적 유추가 불가능한 부분은 추측하지 마십시오.
            4. 불확실성 처리: 들리지 않거나 불분명한 부분은 추측하거나 보완하지 말고, 해당 텍스트를 공란으로 두어야 합니다.

            II. 화자 분리 (Diarization) 지침
            5. 화자 분리 원칙: 서로 다른 화자는 분리하되, 동일 화자가 잠시 톤이나 음량, 감정, 말투가 달라지더라도 같은 사람으로 판단되면 기존 speaker 번호를 유지하십시오. 완전히 다른 음색이 감지될 때만 새로운 speaker 번호를 부여합니다.
            6. 화자 구분: 각 발화에 대해 화자를 숫자로 구분합니다. 발화자의 등장 순서대로 새로운 번호를 할당합니다.
            7. 끼어들기 및 교대 감지: 짧은 맞장구나 감탄사(예: "네", "아", "그렇죠")는 독립 화자로 분리하지 말고, 직전 화자와 동일 인물일 가능성을 우선 고려하십시오. 단, 동시에 겹치는 명확한 목소리가 있다면 별도 화자로 구분합니다.
            8. 겹침 처리: 화자가 겹치는 경우, 두 화자 모두 각각의 start_time_mmss 값을 기록하여 겹친 시점이 모두 JSON에 반영되도록 하세요.
            9. 동일 화자 재개: 다른 화자의 짧은 끼어들기 직후 주 화자(A)가 다시 이어 말할 경우, A의 음색·말투·발성 특징이 기존과 동일하다면 반드시 같은 speaker 번호를 유지합니다.

            III. 출력 형식 지침
            10. 각 발화에 대해 음성 인식의 신뢰도를 0.0~1.0 사이의 값으로 평가합니다.
            11. start_time_mmss는 "분:초:밀리초" (예: "0:05:200", "1:23:450") 형태로 출력합니다.
            12. 최종 결과는 아래의 JSON 형식과 정확히 일치해야 합니다. 각 JSON 객체는 'speaker', 'start_time_mmss', 'confidence', 'text' 키를 포함해야 합니다.
            13. speaker가 동일한 경우 하나의 행으로 만듭니다. 단, 문장이 5개를 넘어갈 경우 다음 대화로 분리한다.

            출력 형식:
            [
                {
                    "speaker": 1,
                    "start_time_mmss": "0:00:000",
                    "confidence": 0.95,
                    "text": "안녕하세요. 회의를 시작하겠습니다."
                },
                {
                    "speaker": 2,
                    "start_time_mmss": "0:05:200",
                    "confidence": 0.92,
                    "text": "네, 좋습니다."
                }
            ]
            JSON 배열만 출력하고, 추가 설명이나 마크다운 코드 블록은 포함하지 마세요.
            """

            print("🤖 Gemini 2.5 Pro로 음성 인식 중...")
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[prompt, types.Part.from_bytes(data=file_bytes, mime_type=mime_type)],
            )

            # response.text가 None인지 체크
            if response.text is None:
                print("⚠️ Gemini 응답이 비어있습니다. 응답 상태 확인:")
                print(f"   - candidates: {response.candidates if hasattr(response, 'candidates') else 'N/A'}")
                print(f"   - prompt_feedback: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'N/A'}")

                # 안전 필터링 체크
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    print(f"⚠️ 프롬프트가 차단되었을 수 있습니다: {response.prompt_feedback}")

                raise ValueError("Gemini API가 빈 응답을 반환했습니다. 안전 필터링 또는 API 오류일 수 있습니다.")

            cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()

            # JSON 파싱 시도
            try:
                result_list = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                print(f"❌ JSON 파싱 실패: {e}")
                print(f"📝 오류 위치: line {e.lineno}, column {e.colno}")

                # 응답 일부 출력 (디버깅용)
                lines = cleaned_response.split('\n')
                if e.lineno <= len(lines):
                    error_line = lines[e.lineno - 1]
                    print(f"📄 오류 발생 줄: {error_line}")
                    if e.colno > 0:
                        print(f"    {' ' * (e.colno - 1)}^ 여기")

                # 전체 응답 저장 (디버깅용)
                error_log_path = os.path.join(os.path.dirname(__file__), '..', 'gemini_error_response.txt')
                with open(error_log_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_response)
                print(f"📁 전체 응답이 저장되었습니다: {error_log_path}")

                raise ValueError(f"Gemini 응답이 올바른 JSON 형식이 아닙니다: {e}")

            normalized_segments = []
            for idx, segment in enumerate(result_list):
                normalized_segments.append({
                    "id": idx,
                    "speaker": segment.get("speaker", 1),
                    "start_time": self._parse_mmss_to_seconds(segment.get("start_time_mmss", "0:00:000")),
                    "confidence": segment.get("confidence", 0.0),
                    "text": segment.get("text", ""),
                })
            print("✅ Gemini 음성 인식 완료")
            
            return normalized_segments

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ Gemini 오류 발생: {e}")
            return None

    def subtopic_generate(self, title: str, transcript_text: str):
        prompt_text = f"""당신은 제공된 대화 스크립트 내용을 분석하여, 구조화된 주제별 요약본으로 변환하는 AI 어시스턴트입니다.

            **입력 파일 형식:**
            입력 내용은 여러 화자(1,2,3,...)가 참여하는 원본 대화 내용입니다.

            **출력 요구사항:**
            당신은 입력 파일을 다음과 같은 규칙에 따라 요약본으로 변환해야 합니다.

            1.  회의 제목 : {title}
            2.  주제별 그룹화 : 스크립트 전체 내용을 분석하여 주요 논의 주제를 파악합니다.
            3.  소주제 제목 형식 (중요): 각 주요 주제별로 핵심 내용을 요약하는 제목을 **반드시 "### 제목" 형식**으로 생성합니다. (예: `### 대주주 주식 양도세 기준 논란`)
            4.  내용 요약: 각 주제 제목 아래에 관련된 핵심 주장, 사실, 의견을 글머리 기호(`*`)를 사용하여 요약합니다.
            5.  문체 변환: 원본의 구어체(대화체)를 간결하고 공식적인 서술형 문어체(요약문 스타일)로 변경합니다.
            6.  화자 및 군더더기 제거: 'A:', 'B:'와 같은 화자 표시와 '그러니까', '어,', '자,', '[웃음]' 등 대화의 군더더기를 모두 제거하고 내용만 정제하여 요약합니다.
            7.  제목과 내용 간격: 소주제 제목(### 제목)과 첫 번째 글머리 기호(*) 사이에는 공백 줄을 두지 않습니다. 제목 바로 다음 줄에 내용을 작성합니다.
            8.  문단 간격: 서로 다른 소주제 사이에는 줄바꿈을 2개 넣어 가독성을 높입니다.
            9.  정확한 인용 (필수):
                * 요약된 모든 문장이나 구절 끝에는 반드시 원본 스크립트의 번호를 형식으로 변환하여 삽입해야 합니다.
                * 하나의 글머리 기호가 여러 소스의 내용을 종합한 경우, 모든 관련 소스 번호를 인용해야 합니다. [cite_start](예: `[cite: 1, 2]`)
                * 인용은 요약된 내용과 원본 소스 간의 사실 관계가 정확히 일치해야 합니다.

            **출력 예시:**
            ### 첫 번째 주요 주제
            * 첫 번째 논의 내용 요약 [cite: 1]
            * 두 번째 논의 내용 요약 [cite: 2, 3]

            ### 두 번째 주요 주제
            * 관련 논의 내용 요약 [cite: 4]

            작업 수행:
            이제 다음 [스크립트 내용]을 분석하여 위의 요구사항을 모두 준수하는 주제별 요약본을 생성해 주십시오.
            {transcript_text}"""

        print(f"======prompt_text========")
        print(prompt_text)

        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY가 .env 파일에 설정되지 않았습니다.")

        client = genai.Client(api_key=api_key)
        model = "gemini-2.5-pro"

        import threading
        import datetime
        thread_id = threading.current_thread().name
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}][{thread_id}] 🤖 Gemini를 통해 요약 생성 중...")
        try:
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=prompt_text),
                        ],
                    ),
                ],
            )
            summary_content = response.text.strip()
            print("✅ Gemini 요약 생성 완료.")
            return summary_content
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ Gemini 요약 생성 중 오류 발생: {e}")
            return None

    def generate_minutes(self, title: str, transcript_text: str, summary_content: str):
        """
        문단 요약을 기반으로 정식 회의록을 생성합니다.

        Args:
            title (str): 회의 제목
            transcript_text (str): 원본 회의 스크립트
            summary_content (str): 이미 생성된 문단 요약 내용

        Returns:
            str: 생성된 회의록 내용 (마크다운 형식)
        """
        prompt_text = f"""당신은 회의록을 전문적으로 작성하는 AI 어시스턴트입니다.
아래 제공되는 "회의 스크립트"와 "문단 요약"을 분석하여, 주어진 "마크다운 템플릿"의 각 항목을 채워주세요.

스크립트에서 직접 추출 불가능한 정보(예: 회의명, 일시, 기한)는 스크립트 내용을 바탕으로 적절히 추정하거나,
추정이 불가능하면 '미정' 또는 '정보 없음'으로 표시해주세요.


--- 회의 제목 ---
{title}
--------------------


--- 문단 요약 ---
{summary_content}
--------------------


--- 회의 스크립트 ---
{transcript_text}
--------------------


--- 마크다운 템플릿 (이 형식 정확히 따르세요) ---

# {{회의명}}

**일시**: {{일시}}  
**참석자**: {{참석자}}


## 회의 요약  
{{회의의 핵심 주제, 논의 방향, 주요 결론이 모두 포함되도록 전체 내용을 **하나의 간결한 문단으로 요약**}}


## 핵심 논의 내용  

### {{첫 번째 핵심 주제}}  
{{해당 주제에 대한 논의 내용(현황, 주요 발언, 의견, 결론 등)}}

### {{두 번째 핵심 주제}}  
{{해당 주제에 대한 논의 내용(현황, 주요 발언, 의견, 결론 등)}}

*(필요 시 주제 추가)*


## 액션 아이템  
{{회의 결과를 바탕으로 자동 분담된 업무를 명확히 기재}}  

* {{수행할 과제 1 (**담당자:** OOO, **기한:** OOO)}}  
* {{수행할 과제 2 (**담당자:** OOO, **기한:** OOO)}}  

*(필요 시 항목 추가)*


## 향후 계획  
{{결정 사항에 따른 후속 단계, 우선순위, 마감일 등을 간결히 정리}}  
{{다음 회의에서 논의할 예정인 항목이나 보완 필요 사항 명시}}

[중요 출력 규칙]
- 절대로 서론, 인사, 부연 설명을 포함하지 마세요.
- 응답은 반드시 마크다운 제목인 '#'으로 시작해야 합니다.
- 오직 주어진 템플릿 형식에 맞춰 내용만 채워서 응답을 생성하세요.
- **모든 내용은 회의록 양식에 맞게, 구어체가 아닌 간결하고 명료한 서술체로 작성하세요.**
- **'액션 아이템' 섹션은 템플릿에 표시된 대로 반드시 글머리 기호(예: `* `)를 사용하되, **담당자(화자 이름)를 제외하고 수행할 과제와 기한만**을 나열하세요.**
- 만약 특정 정보가 스크립트에 없으면 해당 섹션에 '정보 없음' 또는 '미정'으로 표시하세요.
- {{}}는 실제 내용으로 채워서 표시하지 마세요.
##############################
"""

        print(f"======회의록 생성 prompt========")
        print(prompt_text[:500] + "...")

        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY가 .env 파일에 설정되지 않았습니다.")

        client = genai.Client(api_key=api_key)
        model = "gemini-2.5-pro"

        print("🤖 Gemini를 통해 회의록 생성 중...")
        try:
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=prompt_text),
                        ],
                    ),
                ],
            )
            minutes_content = response.text.strip()
            print("✅ Gemini 회의록 생성 완료.")
            return minutes_content
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ Gemini 회의록 생성 중 오류 발생: {e}")
            return None

    @staticmethod
    def parse_script(script_text):
        """
        스크립트 텍스트를 파싱하여 segments 형식으로 변환합니다.

        지원 형식:
        - "화자1: 텍스트" 또는 "1: 텍스트"
        - "A: 텍스트" 또는 "화자A: 텍스트"
        - "[화자1] 텍스트" 또는 "[1] 텍스트"

        Args:
            script_text (str): 스크립트 텍스트 (여러 줄)

        Returns:
            list: segments 형식의 리스트 (transcribe_audio와 동일한 형식)
        """
        import re

        lines = script_text.strip().split('\n')
        segments = []
        current_time = 0.0
        time_increment = 5.0  # 각 발화 간격을 5초로 가정
        speaker_map = {}  # 화자 문자열 -> 숫자 매핑
        next_speaker_id = 1

        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # 패턴 1: "화자1: 텍스트" 또는 "1: 텍스트"
            match = re.match(r'^(?:화자\s*)?(\d+)\s*:\s*(.+)$', line)
            if match:
                speaker_num = int(match.group(1))
                text = match.group(2).strip()
            else:
                # 패턴 2: "A: 텍스트" 또는 "화자A: 텍스트"
                match = re.match(r'^(?:화자\s*)?([A-Za-z가-힣]+)\s*:\s*(.+)$', line)
                if match:
                    speaker_label = match.group(1)
                    text = match.group(2).strip()

                    # 화자 레이블을 숫자로 매핑
                    if speaker_label not in speaker_map:
                        speaker_map[speaker_label] = next_speaker_id
                        next_speaker_id += 1
                    speaker_num = speaker_map[speaker_label]
                else:
                    # 패턴 3: "[화자1] 텍스트" 또는 "[1] 텍스트"
                    match = re.match(r'^\[(?:화자\s*)?(\d+)\]\s*(.+)$', line)
                    if match:
                        speaker_num = int(match.group(1))
                        text = match.group(2).strip()
                    else:
                        # 패턴 4: "[A] 텍스트" 또는 "[화자A] 텍스트"
                        match = re.match(r'^\[(?:화자\s*)?([A-Za-z가-힣]+)\]\s*(.+)$', line)
                        if match:
                            speaker_label = match.group(1)
                            text = match.group(2).strip()

                            if speaker_label not in speaker_map:
                                speaker_map[speaker_label] = next_speaker_id
                                next_speaker_id += 1
                            speaker_num = speaker_map[speaker_label]
                        else:
                            # 화자 표시 없이 텍스트만 있는 경우 (이전 화자 계속)
                            print(f"⚠️ 화자를 찾을 수 없는 줄 (건너뜀): {line}")
                            continue

            # segments에 추가
            segments.append({
                "id": idx,
                "speaker": speaker_num,
                "start_time": current_time,
                "confidence": 1.0,  # 스크립트는 신뢰도 100%
                "text": text
            })

            current_time += time_increment

        print(f"✅ 스크립트 파싱 완료: {len(segments)}개 세그먼트 생성")
        if speaker_map:
            print(f"   화자 매핑: {speaker_map}")

        return segments




