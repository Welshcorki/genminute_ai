import os
from google import genai
from dotenv import load_dotenv

# .env 파일 로드
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)


class ChatManager:
    """
    회의록 기반 챗봇 매니저
    SelfQueryRetriever를 사용하여 관련 문서를 검색하고,
    Gemini 2.5 Flash로 답변을 생성합니다.
    """

    def __init__(self, vector_db_manager, retriever_type="similarity"):
        """
        Args:
            vector_db_manager (VectorDBManager): 벡터 DB 매니저 인스턴스
            retriever_type (str, optional): 검색 리트리버 타입.
                                            "similarity", "mmr", "self_query", "similarity_score_threshold" 중 선택.
                                            Defaults to "similarity".
        """
        self.vdb_manager = vector_db_manager
        self.retriever_type = retriever_type

        # Gemini API 클라이언트 초기화
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY가 .env 파일에 설정되지 않았습니다.")

        self.gemini_client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash"

        print(f"✅ ChatManager 초기화 완료: retriever_type='{self.retriever_type}'")

    def search_documents(self, query: str, meeting_id: str = None, accessible_meeting_ids: list = None) -> dict:
        """
        meeting_chunks와 meeting_subtopic에서 각각 3개씩 검색

        Args:
            query (str): 사용자 질문
            meeting_id (str, optional): 특정 회의로 제한할 경우
            accessible_meeting_ids (list, optional): 사용자가 접근 가능한 meeting_id 목록

        Returns:
            dict: {
                "chunks": [Document, ...],
                "subtopics": [Document, ...],
                "total_count": int
            }
        """
        # title 키워드 필터링 비활성화
        # 이유: Similarity search가 이미 의미론적으로 관련된 문서를 찾아주므로,
        #       단순한 키워드 추출로 오히려 좋은 결과를 제거할 수 있음
        title_keywords = []

        # (참고) 필요시 특정 패턴만 추출하도록 개선 가능:
        # - 고유명사 (예: "사자회담")
        # - 따옴표로 묶인 단어
        # - NLP 기반 주제어 추출

        if meeting_id:
            # 특정 노트로 제한 (검색 후 필터링)
            pass  # filter_criteria는 None으로 유지, 검색 후 meeting_id로 필터링
        elif accessible_meeting_ids:
            # 접근 가능한 노트들로 제한 (여러 노트에서 검색)
            # Vector DB가 $in 연산자를 지원하지 않을 수 있으므로, 각 노트별로 검색 후 결합
            print(f"🔍 {len(accessible_meeting_ids)}개 노트에서 검색 중...")
            all_chunks = []
            all_subtopics = []

            # 설정된 retriever_type 사용
            try:
                chunk_result = self.vdb_manager.search(
                    db_type="chunks",
                    query=query,
                    k=len(accessible_meeting_ids) * 10,  # 넉넉하게 검색
                    retriever_type=self.retriever_type,
                    filter_criteria=None
                )
                # 접근 가능한 meeting_id로 필터링
                all_chunks = [doc for doc in chunk_result
                             if doc.metadata.get('meeting_id') in accessible_meeting_ids]

                subtopic_result = self.vdb_manager.search(
                    db_type="subtopic",
                    query=query,
                    k=len(accessible_meeting_ids) * 10,  # 넉넉하게 검색
                    retriever_type=self.retriever_type,
                    filter_criteria=None
                )
                # 접근 가능한 meeting_id로 필터링
                all_subtopics = [doc for doc in subtopic_result
                                if doc.metadata.get('meeting_id') in accessible_meeting_ids]

                # title 키워드로 부분 일치 필터링
                if title_keywords:
                    print(f"📌 title 필터링 적용: {title_keywords}")
                    filtered_chunks = []
                    for doc in all_chunks:
                        doc_title = doc.metadata.get('title', '').lower()
                        if any(keyword.lower() in doc_title for keyword in title_keywords):
                            filtered_chunks.append(doc)

                    filtered_subtopics = []
                    for doc in all_subtopics:
                        doc_title = doc.metadata.get('meeting_title', '').lower()
                        if any(keyword.lower() in doc_title for keyword in title_keywords):
                            filtered_subtopics.append(doc)

                    print(f"   필터링 전: chunks={len(all_chunks)}, subtopic={len(all_subtopics)}")
                    print(f"   필터링 후: chunks={len(filtered_chunks)}, subtopic={len(filtered_subtopics)}")

                    all_chunks = filtered_chunks
                    all_subtopics = filtered_subtopics

            except Exception as e:
                # 검색 실패 시 빈 결과 반환
                print(f"⚠️ 검색 실패: {e}")
                all_chunks = []
                all_subtopics = []

            # 상위 3개씩만 선택
            chunks_results = all_chunks[:3]
            subtopic_results = all_subtopics[:3]

            print(f"✅ 검색 완료: chunks={len(chunks_results)}개, subtopic={len(subtopic_results)}개")

            return {
                "chunks": chunks_results,
                "subtopics": subtopic_results,
                "total_count": len(chunks_results) + len(subtopic_results)
            }

        try:
            # 단일 노트 검색 또는 전체 검색
            # 설정된 retriever_type 사용
            chunks_results = self.vdb_manager.search(
                db_type="chunks",
                query=query,
                k=20 if meeting_id else 10,  # 넉넉하게 검색 후 필터링
                retriever_type=self.retriever_type,
                filter_criteria=None
            )

            subtopic_results = self.vdb_manager.search(
                db_type="subtopic",
                query=query,
                k=20 if meeting_id else 10,  # 넉넉하게 검색 후 필터링
                retriever_type=self.retriever_type,
                filter_criteria=None
            )

            # meeting_id가 지정된 경우, 해당 노트로 필터링
            if meeting_id:
                chunks_results = [doc for doc in chunks_results
                                 if doc.metadata.get('meeting_id') == meeting_id]
                subtopic_results = [doc for doc in subtopic_results
                                   if doc.metadata.get('meeting_id') == meeting_id]

            # title 키워드로 부분 일치 필터링
            if title_keywords:
                print(f"📌 title 필터링 적용: {title_keywords}")
                filtered_chunks = []
                for doc in chunks_results:
                    doc_title = doc.metadata.get('title', '').lower()
                    # 키워드 중 하나라도 title에 포함되면 선택
                    if any(keyword.lower() in doc_title for keyword in title_keywords):
                        filtered_chunks.append(doc)

                filtered_subtopics = []
                for doc in subtopic_results:
                    doc_title = doc.metadata.get('meeting_title', '').lower()
                    if any(keyword.lower() in doc_title for keyword in title_keywords):
                        filtered_subtopics.append(doc)

                print(f"   필터링 전: chunks={len(chunks_results)}, subtopic={len(subtopic_results)}")
                print(f"   필터링 후: chunks={len(filtered_chunks)}, subtopic={len(filtered_subtopics)}")

                chunks_results = filtered_chunks
                subtopic_results = filtered_subtopics

            # 상위 3개만 선택
            chunks_results = chunks_results[:3]
            subtopic_results = subtopic_results[:3]

            print(f"✅ 검색 완료: chunks={len(chunks_results)}개, subtopic={len(subtopic_results)}개")

            return {
                "chunks": chunks_results,
                "subtopics": subtopic_results,
                "total_count": len(chunks_results) + len(subtopic_results)
            }

        except Exception as e:
            print(f"❌ 문서 검색 중 오류: {e}")
            return {
                "chunks": [],
                "subtopics": [],
                "total_count": 0
            }

    def format_context(self, search_results: dict) -> str:
        """
        검색된 문서들을 컨텍스트 문자열로 포맷팅

        Args:
            search_results (dict): search_documents()의 반환값

        Returns:
            str: 포맷팅된 컨텍스트
        """
        context_parts = []

        # Chunks 추가
        if search_results["chunks"]:
            context_parts.append("=== 회의 대화 내용 ===")
            for i, doc in enumerate(search_results["chunks"], 1):
                metadata = doc.metadata
                context_parts.append(
                    f"\n[문서 {i}]\n"
                    f"회의: {metadata.get('title', 'N/A')}\n"
                    f"일시: {metadata.get('meeting_date', 'N/A')}\n"
                    f"시간: {metadata.get('start_time', 0):.0f}초 - {metadata.get('end_time', 0):.0f}초\n"
                    f"내용:\n{doc.page_content}\n"
                )

        # Subtopics 추가
        if search_results["subtopics"]:
            context_parts.append("\n=== 회의 주제별 요약 ===")
            for i, doc in enumerate(search_results["subtopics"], 1):
                metadata = doc.metadata
                context_parts.append(
                    f"\n[요약 {i}]\n"
                    f"회의: {metadata.get('meeting_title', 'N/A')}\n"
                    f"일시: {metadata.get('meeting_date', 'N/A')}\n"
                    f"주제: {metadata.get('main_topic', 'N/A')}\n"
                    f"내용:\n{doc.page_content}\n"
                )

        if not context_parts:
            return "검색된 회의록 내용이 없습니다."

        return "\n".join(context_parts)

    def generate_answer(self, query: str, context: str) -> dict:
        """
        Gemini 2.5 Flash를 사용하여 답변 생성

        Args:
            query (str): 사용자 질문
            context (str): 검색된 문서 컨텍스트

        Returns:
            dict: {
                "success": bool,
                "answer": str,
                "error": str (optional)
            }
        """
        # 프롬프트 생성
        prompt = f"""
당신은 회의록 내용을 바탕으로 사용자의 질문에 답변하는 전문 비서 챗봇입니다.

[지시 사항]
1. **반드시** 아래 [검색된 회의록 내용] **안에서만** 정보를 찾아서 답변해야 합니다.
2. [검색된 회의록 내용]에 질문에 대한 정보가 전혀 없다면, "죄송합니다. 해당 내용을 회의록에서 찾을 수 없습니다."라고 명확하게 답변해야 합니다.
3. 절대로 당신의 사전 지식이나 외부 정보를 사용해서 답변을 추측하거나 생성하지 마세요.
4. 답변은 명확하고 간결하게 요약하여 제공하세요.

---

[검색된 회의록 내용]:
{context}

---

[사용자 질문]:
{query}

---

[답변]:
"""

        try:
            # Gemini 2.5 Flash로 답변 생성
            response = self.gemini_client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            answer = response.text.strip()

            print(f"✅ 답변 생성 완료 (길이: {len(answer)}자)")

            return {
                "success": True,
                "answer": answer
            }

        except Exception as e:
            print(f"❌ 답변 생성 중 오류: {e}")
            return {
                "success": False,
                "answer": "죄송합니다. 답변 생성 중 오류가 발생했습니다.",
                "error": str(e)
            }

    def process_query(self, query: str, meeting_id: str = None, accessible_meeting_ids: list = None) -> dict:
        """
        사용자 질의를 처리하여 답변 반환

        Args:
            query (str): 사용자 질문
            meeting_id (str, optional): 특정 회의로 제한
            accessible_meeting_ids (list, optional): 사용자가 접근 가능한 meeting_id 목록

        Returns:
            dict: {
                "success": bool,
                "answer": str,
                "sources": list,
                "error": str (optional)
            }
        """
        print(f"🤖 챗봇 질의 처리 시작: '{query}'")

        # 1. 관련 문서 검색
        search_results = self.search_documents(query, meeting_id, accessible_meeting_ids)

        if search_results["total_count"] == 0:
            return {
                "success": True,
                "answer": "죄송합니다. 해당 질문과 관련된 회의록 내용을 찾을 수 없습니다.",
                "sources": []
            }

        # 2. 컨텍스트 포맷팅
        context = self.format_context(search_results)

        # 3. 답변 생성
        result = self.generate_answer(query, context)

        if not result["success"]:
            return result

        # 4. 출처 정보 추가
        sources = []

        # Chunks 출처
        for doc in search_results["chunks"]:
            meta = doc.metadata
            sources.append({
                "type": "chunk",
                "meeting_id": meta.get("meeting_id"),
                "title": meta.get("title"),
                "meeting_date": meta.get("meeting_date"),
                "start_time": meta.get("start_time"),
                "end_time": meta.get("end_time")
            })

        # Subtopics 출처
        for doc in search_results["subtopics"]:
            meta = doc.metadata
            sources.append({
                "type": "subtopic",
                "meeting_id": meta.get("meeting_id"),
                "title": meta.get("meeting_title"),
                "meeting_date": meta.get("meeting_date"),
                "main_topic": meta.get("main_topic")
            })

        return {
            "success": True,
            "answer": result["answer"],
            "sources": sources
        }
