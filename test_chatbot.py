"""
챗봇 자동 테스트 스크립트
script_question.md의 질문들을 자동으로 테스트하고 결과를 저장합니다.
"""

import requests
import json
import time
from datetime import datetime
import re

# 설정
API_URL = "http://127.0.0.1:5050/api/chat"
QUESTIONS_FILE = "script_question.md"
RESULTS_FILE = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

# 브라우저에서 복사한 세션 쿠키 값을 여기에 붙여넣기
# Chrome 개발자 도구 > Application > Cookies > session 값
SESSION_COOKIE = ".eJwVjV1rwjAYhf9Lrp1NJgu2MNimFJ0OhQl-UCjxTdbGJXm7NPFm7L8vuTlwPjjPL1FWaEMqMqKjlD6yGWeUvnQ5nQJaMiFOWJUGTQRW0qRclE2UHOapGzx-aaPaQUOIPs_6EIaxKgrTz6YdYmdUHJUHdEG5kB8LUbwuujnC5uNg-319c_dLPEcD9cEvt-AXrFx9vkt8u8j6h6-_d6fz_SivJ3d8eh5L_gAJ69FklpBWu2QzodWSVOzvHxVTRTs.aQ6xSw.pkz9xOuXZvArbEVZhipsSNpj8Z0"  # 예: "eyJfZnJlc2giOmZhbHNlLCJ1c2VyX2lkIjoiMTIzIn0...."

def extract_questions_from_md(file_path):
    """
    script_question.md 파일에서 질문 리스트 추출

    Returns:
        list: [(번호, 질문, 난이도), ...]
    """
    questions = []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # ### 제목으로 시작하는 질문 블록 찾기
    pattern = r'###\s+(\d+)\.\s+(.+?)\n\n\*\*예상 검색 방식:\*\*\n.*?예상 성공률:\s+(.*?)\s+-'
    matches = re.findall(pattern, content, re.DOTALL)

    for match in matches:
        question_num = match[0]
        question_text = match[1].strip()
        difficulty = match[2].strip()

        questions.append((question_num, question_text, difficulty))

    return questions


def test_chatbot_question(question_text):
    """
    챗봇 API에 질문을 보내고 결과를 받아옵니다.

    Args:
        question_text (str): 질문 내용

    Returns:
        dict: {
            "success": bool,
            "answer": str,
            "sources": list,
            "error": str (optional),
            "response_time": float
        }
    """
    start_time = time.time()

    try:
        # 세션 쿠키를 포함한 요청
        cookies = {"session": SESSION_COOKIE} if SESSION_COOKIE != "여기에_세션_쿠키_붙여넣기" else {}

        response = requests.post(
            API_URL,
            json={"query": question_text},
            headers={"Content-Type": "application/json"},
            cookies=cookies,
            timeout=30
        )

        response_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            data['response_time'] = response_time
            return data
        else:
            return {
                "success": False,
                "answer": "",
                "sources": [],
                "error": f"HTTP {response.status_code}: {response.text}",
                "response_time": response_time
            }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "answer": "",
            "sources": [],
            "error": "Timeout (30초 초과)",
            "response_time": 30.0
        }

    except Exception as e:
        return {
            "success": False,
            "answer": "",
            "sources": [],
            "error": str(e),
            "response_time": time.time() - start_time
        }


def format_sources(sources):
    """
    출처 정보를 마크다운 형식으로 포맷팅

    Args:
        sources (list): 출처 정보 리스트

    Returns:
        str: 포맷팅된 출처 정보
    """
    if not sources or len(sources) == 0:
        return "출처 없음"

    formatted = []
    for i, source in enumerate(sources, 1):
        source_type = source.get('type', 'unknown')
        title = source.get('title', 'N/A')
        date = source.get('meeting_date', 'N/A')

        if source_type == 'chunk':
            start = source.get('start_time', 0)
            end = source.get('end_time', 0)
            formatted.append(f"   - [{i}] **{title}** ({date}) - {start:.0f}초~{end:.0f}초")
        else:  # subtopic
            topic = source.get('main_topic', 'N/A')
            formatted.append(f"   - [{i}] **{title}** ({date}) - 주제: {topic}")

    return "\n".join(formatted)


def write_results_to_markdown(results, output_file):
    """
    테스트 결과를 마크다운 파일로 저장

    Args:
        results (list): 테스트 결과 리스트
        output_file (str): 출력 파일 경로
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        # 헤더
        f.write(f"# 챗봇 테스트 결과\n\n")
        f.write(f"**테스트 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**총 질문 수**: {len(results)}개\n\n")

        # 성공률 통계
        success_count = sum(1 for r in results if r['result']['success'])
        f.write(f"**성공**: {success_count}개 / **실패**: {len(results) - success_count}개\n\n")

        avg_response_time = sum(r['result']['response_time'] for r in results) / len(results)
        f.write(f"**평균 응답 시간**: {avg_response_time:.2f}초\n\n")

        f.write("---\n\n")

        # 각 질문별 결과
        for item in results:
            q_num = item['question_num']
            question = item['question']
            difficulty = item['difficulty']
            result = item['result']

            f.write(f"## Q{q_num}. {question}\n\n")
            f.write(f"**예상 난이도**: {difficulty}\n\n")
            f.write(f"**응답 시간**: {result['response_time']:.2f}초\n\n")

            if result['success']:
                f.write(f"**답변**:\n\n")
                f.write(f"{result['answer']}\n\n")

                f.write(f"**출처**:\n\n")
                f.write(f"{format_sources(result.get('sources', []))}\n\n")
            else:
                f.write(f"❌ **오류**: {result.get('error', '알 수 없는 오류')}\n\n")

            f.write("---\n\n")

        # 성공률 요약 (난이도별)
        f.write("## 난이도별 성공률\n\n")

        high_results = [r for r in results if "높음" in r['difficulty']]
        medium_results = [r for r in results if "중간" in r['difficulty']]

        if high_results:
            high_success = sum(1 for r in high_results if r['result']['success'])
            f.write(f"- ✅ **높음**: {high_success}/{len(high_results)} ({high_success/len(high_results)*100:.1f}%)\n")

        if medium_results:
            medium_success = sum(1 for r in medium_results if r['result']['success'])
            f.write(f"- ⚠️ **중간**: {medium_success}/{len(medium_results)} ({medium_success/len(medium_results)*100:.1f}%)\n")

        f.write("\n")


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("챗봇 자동 테스트 시작")
    print("=" * 60)

    # 세션 쿠키 확인
    if SESSION_COOKIE == "여기에_세션_쿠키_붙여넣기":
        print("\n⚠️  세션 쿠키가 설정되지 않았습니다!")
        print("\n다음 단계를 따라주세요:")
        print("1. 브라우저에서 http://127.0.0.1:5050 로그인")
        print("2. F12 > Application > Cookies > session 값 복사")
        print("3. test_chatbot.py의 SESSION_COOKIE 변수에 붙여넣기")
        print("\n예시:")
        print('SESSION_COOKIE = "eyJfZnJlc2giOmZhbHNlLCJ1c2VyX2lkIjoiMTIzIn0..."')
        return

    print(f"\n🔐 세션 쿠키 설정됨 (길이: {len(SESSION_COOKIE)}자)")

    # 1. 질문 추출
    print(f"\n📖 {QUESTIONS_FILE}에서 질문 추출 중...")
    questions = extract_questions_from_md(QUESTIONS_FILE)
    print(f"✅ {len(questions)}개 질문 추출 완료\n")

    # 2. 각 질문 테스트
    results = []

    for i, (q_num, question, difficulty) in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] Q{q_num}: {question[:50]}...")
        print(f"   난이도: {difficulty}")

        result = test_chatbot_question(question)

        results.append({
            'question_num': q_num,
            'question': question,
            'difficulty': difficulty,
            'result': result
        })

        if result['success']:
            print(f"   ✅ 성공 (응답시간: {result['response_time']:.2f}초)")
            print(f"   답변 길이: {len(result['answer'])}자")
        else:
            print(f"   ❌ 실패: {result.get('error', '알 수 없는 오류')}")

        print()

        # API 부하 방지를 위한 딜레이
        if i < len(questions):
            time.sleep(1)

    # 3. 결과 저장
    print(f"💾 결과를 {RESULTS_FILE}에 저장 중...")
    write_results_to_markdown(results, RESULTS_FILE)
    print(f"✅ 저장 완료\n")

    # 4. 요약 출력
    print("=" * 60)
    print("테스트 요약")
    print("=" * 60)

    success_count = sum(1 for r in results if r['result']['success'])
    print(f"총 질문 수: {len(results)}개")
    print(f"성공: {success_count}개 ({success_count/len(results)*100:.1f}%)")
    print(f"실패: {len(results) - success_count}개")

    avg_time = sum(r['result']['response_time'] for r in results) / len(results)
    print(f"평균 응답 시간: {avg_time:.2f}초")

    print(f"\n📄 상세 결과는 {RESULTS_FILE}을 확인하세요.")
    print("=" * 60)


if __name__ == "__main__":
    main()
