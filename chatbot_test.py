from google import genai
import os

# --- 1. API 키 설정 ---
# ** 중요 **: 'YOUR_API_KEY' 부분을 본인의 Google AI Studio API 키로 변경하세요.
# 실제 서비스에서는 환경 변수 사용을 강력히 권장합니다.
# (예: os.environ.get("GOOGLE_API_KEY"))
try:
    # genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    genai.configure(api_key="YOUR_API_KEY") 
except AttributeError:
    print("--------------------------------------------------")
    print("경고: GOOGLE_API_KEY가 설정되지 않았습니다.")
    print("코드 내 'YOUR_API_KEY'를 수정하거나 환경 변수를 설정해주세요.")
    print("--------------------------------------------------")
    # 이 예제에서는 키가 없어도 계속 진행하지만, main_chatbot() 호출 시 오류가 발생합니다.


# --- 2. Vector DB 검색 시뮬레이션 ---
# 실제 구현에서는 이 부분에 ChromaDB, FAISS, Pinecone 등의
# Vector DB 검색 로직이 들어가야 합니다.
def get_relevant_documents_from_vector_db(query: str) -> str:
    """
    Vector DB에서 관련 문서를 검색하는 함수 (시뮬레이션).
    실제 구현에서는 사용자 쿼리를 임베딩하고 Vector DB와 
    유사도 검색을 수행해야 합니다.
    """
    print(f"\n[Vector DB 시뮬레이션: '{query}' 검색 중...]")
    
    # 데모용 가상 회의록 데이터 (Vector DB에서 검색되었다고 가정)
    mock_db = {
        "프로젝트": """
        [회의록 발췌 1]
        - 일시: 2025년 11월 4일
        - 참석자: 김철수, 이영희, 박지성
        - 안건: 4분기 '프로젝트 제우스' 마케팅 전략
        - 결정 사항:
            1. '프로젝트 제우스'의 핵심 타겟 고객을 20대 초반으로 재설정한다. (담당: 이영희)
            2. SNS 광고 예산을 20% 증액한다. (담당: 김철수)
            3. 11월 20일까지 인플루언서 섭외를 완료한다. (담당: 박지성)
        - 특이사항: 예산 증액에 따른 재무팀 협의 필요.
        """,
        "알파": """
        [회의록 발췌 2]
        - 안건: 신규 '알파' 기능 개발 일정
        - 내용: '알파' 기능의 베타 테스트는 12월 1일 시작으로 확정.
        - 담당: 개발팀 (박지성)
        """,
        "베타": """
        [회의록 발췌 3]
        - 안건: '베타' 서비스 QA 현황
        - 내용: QA 과정에서 치명적인 버그 3건 발견.
        - 결정 사항: 릴리즈 일정을 11월 15일에서 11월 30일로 연기한다.
        """
    }
    
    # 간단한 키워드 기반 검색 시뮬레이션
    retrieved_context = ""
    for keyword, text in mock_db.items():
        if keyword in query or query in text:
            retrieved_context += text + "\n"
            
    if not retrieved_context:
        return "[관련된 회의록 내용을 찾지 못했습니다.]"
        
    return retrieved_context

# --- 3. Gemini 모델 호출 및 프롬프트 생성 ---

def create_prompt(query: str, context: str) -> str:
    """
    Gemini 모델에게 전달할 프롬프트 문자열을 생성합니다.
    (위 '핵심 프롬프트' 섹션 참조)
    """
    prompt = f"""
    당신은 회의록 내용을 바탕으로 사용자의 질문에 답변하는 전문 비서 챗봇입니다.

    [지시 사항]
    1.  **반드시** 아래 [검색된 회의록 내용] **안에서만** 정보를 찾아서 답변해야 합니다.
    2.  [검색된 회의록 내용]에 질문에 대한 정보가 전혀 없다면, "죄송합니다. 해당 내용을 회의록에서 찾을 수 없습니다."라고 명확하게 답변해야 합니다.
    3.  절대로 당신의 사전 지식이나 외부 정보를 사용해서 답변을 추측하거나 생성하지 마세요.
    4.  답변은 명확하고 간결하게 요약하여 제공하세요.

    ---

    [검색된 회의록 내용]:
    {context}

    ---

    [사용자 질문]:
    {query}

    ---

    [답변]:
    """
    return prompt

def get_answer_from_gemini(query: str, context: str):
    """
    Gemini 2.5 Flash 모델을 호출하여 답변을 생성합니다.
    """
    # 모델 초기화 (gemini-2.5-flash 사용)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # 프롬프트 생성
    prompt = create_prompt(query, context)
    
    # 모델 호출
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"--- Gemini API 호출 오류 ---")
        print(f"오류: {e}")
        print("API 키가 올바르게 설정되었는지, 인터넷 연결이 정상인지 확인하세요.")
        return "답변 생성 중 오류가 발생했습니다. API 키 설정을 확인해주세요."

# --- 4. 메인 실행 로직 (챗봇 시뮬레이션) ---
def main_chatbot():
    print("="*50)
    print("      회의록 검색 챗봇 (Gemini 2.5 Flash 기반 RAG)")
    print("="*50)
    print(" (종료하시려면 'exit' 또는 '종료'를 입력하세요.)")
    
    while True:
        user_query = input("\n[질문]: ")
        if user_query.lower() in ['exit', '종료']:
            print("\n[챗봇]: 챗봇을 종료합니다. 이용해주셔서 감사합니다.")
            break
        
        # 1. Vector DB에서 관련 문서 검색 (시뮬레이션)
        retrieved_context = get_relevant_documents_from_vector_db(user_query)
        print(f"[Vector DB 검색 결과 (요약)]: \n{retrieved_context[:200]}...")
        
        # 2. Gemini 모델로 답변 생성
        print("\n[Gemini 답변 생성 중...]")
        final_answer = get_answer_from_gemini(user_query, retrieved_context)
        
        # 3. 답변 출력
        print(f"\n[챗봇 답변]: {final_answer}")

# --- 스크립트 실행 ---
if __name__ == "__main__":
    main_chatbot()