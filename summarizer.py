# -*- coding: utf-8 -*-

# 1. 필요한 라이브러리 임포트
import os
import pandas as pd
import google.generativeai as genai
import io
import sys
from dotenv import load_dotenv
import argparse
from typing import Optional


# 2. 상수 정의 (매직 스트링 제거)
ENCODING = 'utf-8-sig'
RESULT_DIR = 'result'
REQUIRED_COLUMNS = ['speaker', 'start_time', 'text', 'confidence']
CSV_EXTENSION = '.csv'
PREVIEW_LENGTH = 500
MODEL_NAME = 'gemini-2.5-pro'
TRANSCRIPT_TIME_FORMAT = "[{time}] {speaker}: {text}"
SEPARATOR = "--- {message} ---"


# 3. 로깅 유틸리티 함수 (중복 제거)
def print_section(message: str) -> None:
    """섹션 제목을 출력합니다."""
    print(f"\n{SEPARATOR.format(message=message)}")


def print_error(message: str) -> None:
    """에러 메시지를 출력합니다."""
    print(f"오류: {message}")


def print_info(message: str) -> None:
    """일반 정보 메시지를 출력합니다."""
    print(message)


# 4. 인코딩 및 환경변수 설정
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding=ENCODING)
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding=ENCODING)
load_dotenv()


# 5. Gemini API 설정
try:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise KeyError
    genai.configure(api_key=api_key)
except KeyError:
    print_error("GOOGLE_API_KEY를 찾을 수 없습니다.")
    print_info(".env 파일에 GOOGLE_API_KEY가 설정되어 있는지 확인해주세요.")
    sys.exit(1)


# 6. 파일 경로 검증 함수 (중복 제거)
def validate_file_path(file_path: str) -> bool:
    """
    파일 경로의 유효성을 검증합니다.
    - 파일 존재 여부 확인
    - CSV 파일 확장자 확인
    """
    if not os.path.isfile(file_path):
        print_error(f"'{file_path}' 파일을 찾을 수 없습니다.")
        return False

    if not file_path.lower().endswith(CSV_EXTENSION):
        print_error(f"'{file_path}'는 CSV 파일이 아닙니다. CSV 파일을 지정해주세요.")
        return False

    return True


# 7. 입력 파일 경로를 받는 함수 (중복 제거)
def get_input_csv_path() -> Optional[str]:
    """
    커맨드 라인 인자로 입력된 CSV 파일 경로를 받습니다.
    경로가 유효한지 검증합니다.
    """
    parser = argparse.ArgumentParser(description="회의록 스크립트를 요약하고 마크다운 파일로 저장합니다.")
    parser.add_argument("path", type=str, help="처리할 CSV 파일의 경로 (필수)")
    args = parser.parse_args()

    if not validate_file_path(args.path):
        return None

    print_info(f"-- 파일 경로 확인 --\n   - {args.path}")
    return args.path


# 8. 데이터 로드 함수 (중복 제거)
def load_data(file_path: str) -> Optional[pd.DataFrame]:
    """
    CSV 파일로부터 데이터를 로드하고 상위 5개 행을 확인용으로 출력합니다.
    필수 컬럼: speaker, start_time, text, confidence
    """
    try:
        df = pd.read_csv(file_path, encoding=ENCODING)
        print_info("파일을 성공적으로 로드했습니다. 상위 5개 행은 다음과 같습니다:")
        print(df.head())

        # 필수 컬럼 확인
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]

        if missing_columns:
            print_error("CSV 파일에 필수 컬럼이 없습니다.")
            print_info(f"누락된 컬럼: {missing_columns}")
            print_info(f"현재 컬럼: {list(df.columns)}")
            return None

        return df
    except FileNotFoundError:
        print_error(f"{file_path} 에서 파일을 찾을 수 없습니다.")
        return None
    except pd.errors.ParserError as e:
        print_error(f"CSV 파일을 파싱할 수 없습니다. {e}")
        return None


# 9. 스크립트 포맷팅 함수 (중복 제거)
def format_transcript(df: pd.DataFrame) -> str:
    """
    CSV 데이터를 포맷팅된 스크립트 형식으로 변환합니다.
    형식: [HH:MM] Speaker: Text
    """
    formatted_lines = []
    for idx, row in df.iterrows():
        formatted_line = TRANSCRIPT_TIME_FORMAT.format(
            time=row['start_time'],
            speaker=row['speaker'],
            text=row['text']
        )
        formatted_lines.append(formatted_line)

    return "\n".join(formatted_lines)


# 10. 텍스트 요약 함수 (중복 제거)
def summarize_text(formatted_transcript: str) -> Optional[str]:
    """
    Gemini 모델을 사용하여 전체 회의록 텍스트를 요약합니다.
    """
    print_section("Gemini 모델 요약 시작")
    model = genai.GenerativeModel(MODEL_NAME)

    prompt = f"""당신은 회의록을 전문적으로 요약하고 정리하는 AI 어시스턴트입니다.
아래 제공되는 "회의 스크립트"를 분석하여, 주어진 "마크다운 템플릿"의 각 항목을 채워주세요.

스크립트에서 직접 추출 불가능한 정보(예: 회의명, 일시, 기한)는 스크립트 내용을 바탕으로 적절히 추정하거나, 
추정이 불가능하면 '미정' 또는 '정보 없음'으로 표시해주세요.


--- 회의 스크립트 ---
{formatted_transcript}
--------------------


--- 마크다운 템플릿 (이 형식 정확히 따르세요) ---

# {{회의명}}

**일시**: {{일시}}  
**참석자**: {{참석자}}

---

## 회의 요약  
{{회의 전체 내용을 1~2줄로 간략히 요약하여, 주요 논의 방향과 핵심 결론을 함께 제시}}

---

## 핵심 논의 내용  

### {{첫 번째 핵심 주제}}  
{{해당 주제에 대한 논의 내용(현황, 주요 발언, 의견, 결론 등)}}

### {{두 번째 핵심 주제}}  
{{해당 주제에 대한 논의 내용(현황, 주요 발언, 의견, 결론 등)}}

*(필요 시 주제 추가)*

---

## 액션 아이템  
{{회의 결과를 바탕으로 자동 분담된 업무를 명확히 기재}}  

{{수행할 일 1: 담당자, 목적, 기한}}  
{{수행할 일 2: 담당자, 목적, 기한}}  

*(필요 시 항목 추가)*

---

## 향후 계획  
{{결정 사항에 따른 후속 단계, 우선순위, 마감일 등을 간결히 정리}}  
{{다음 회의에서 논의할 예정인 항목이나 보완 필요 사항 명시}}

---

[중요 출력 규칙]
- 절대로 서론, 인사, 부연 설명을 포함하지 마세요.
- 응답은 반드시 마크다운 제목인 '#'으로 시작해야 합니다.
- 오직 주어진 템플릿 형식에 맞춰 내용만 채워서 응답을 생성하세요.
- **모든 내용은 회의록 양식에 맞게, 구어체가 아닌 간결하고 명료한 서술체로 작성하세요.**
- 만약 특정 정보가 스크립트에 없으면 해당 섹션에 '정보 없음' 또는 '미정'으로 표시하세요.
- {{}}는 실제 내용으로 채워서 표시하지 마세요.
##############################
"""

    try:
        response = model.generate_content(prompt)
        print_info("요약 생성 완료!")
        return response.text
    except Exception as e:
        print_error(f"Gemini API 호출 중 오류 발생: {e}")
        return None


# 11. 파일 저장 함수 (중복 제거)
def save_summary_to_md(summary_content: str, input_filename: str) -> None:
    """
    요약 내용을 result 폴더에 마크다운 파일로 저장합니다.
    """
    print_section("요약 파일 저장 시작")
    os.makedirs(RESULT_DIR, exist_ok=True)
    base_filename = os.path.splitext(os.path.basename(input_filename))[0]
    output_filename = f"{base_filename}_summary.md"
    file_path = os.path.join(RESULT_DIR, output_filename)

    try:
        with open(file_path, 'w', encoding=ENCODING) as f:
            f.write(summary_content)
        print_info(f"요약 내용이 '{file_path}' 파일에 성공적으로 저장되었습니다.")
    except Exception as e:
        print_error(f"파일 저장 중 오류 발생: {e}")


# 12. 메인 실행 블록
if __name__ == "__main__":
    csv_file_path = get_input_csv_path()
    if csv_file_path:
        print_section("파이프라인 시작: 1. 데이터 로드")
        df = load_data(csv_file_path)

        if df is not None:
            print_section("파이프라인 시작: 2. 스크립트 포맷팅")
            formatted_transcript = format_transcript(df)
            print_info(f"스크립트 포맷팅 완료! (상위 {PREVIEW_LENGTH}자 미리보기)")
            print(formatted_transcript[:PREVIEW_LENGTH])

            print_section("파이프라인 시작: 3. 텍스트 요약")
            summary_result = summarize_text(formatted_transcript)

            if summary_result:
                print_section("최종 요약 결과")
                print(summary_result)

                print_section("파이프라인 시작: 4. 파일 저장")
                save_summary_to_md(summary_result, csv_file_path)