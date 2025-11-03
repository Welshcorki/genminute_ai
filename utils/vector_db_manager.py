
import chromadb
import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from dotenv import load_dotenv

from langchain_classic.retrievers.self_query.base import SelfQueryRetriever
from langchain_classic.chains.query_constructor.base import AttributeInfo

# 텍스트 분할을 위한 import (의미적 청킹 대안)
from langchain_text_splitters import RecursiveCharacterTextSplitter
import numpy as np

# Gemini API import
from google import genai


# 이 파일의 상위 디렉토리에 있는 .env 파일을 찾아 로드
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

class VectorDBManager:
    COLLECTION_NAMES = {
        'chunks': 'meeting_chunks',
        'subtopic': 'meeting_subtopic',
    }

    def __init__(self, persist_directory="./database/vector_db"):
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")

        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_function = OpenAIEmbeddings()

        # Initialize LLM for SelfQueryRetriever
        self.llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), temperature=0)

        self.vectorstores = {
            key: Chroma(
                client=self.client,
                collection_name=name,
                embedding_function=self.embedding_function,
            )
            for key, name in self.COLLECTION_NAMES.items()
        }

        # Define metadata field information for SelfQueryRetriever
        self.metadata_field_infos = {
            "chunks": [
                AttributeInfo(name="meeting_id", description="The unique identifier for the meeting", type="string"),
                AttributeInfo(name="dialogue_id", description="The unique identifier for the dialogue within the meeting", type="string"),
                AttributeInfo(name="chunk_index", description="The index of the chunk within the meeting", type="integer"),
                AttributeInfo(name="title", description="The title of the meeting", type="string"),
                AttributeInfo(name="meeting_date", description="The date of the meeting in ISO format (YYYY-MM-DD)", type="string"),
                AttributeInfo(name="audio_file", description="The name of the audio file for the meeting", type="string"),
                AttributeInfo(name="start_time", description="The start time of the chunk in seconds", type="float"),
                AttributeInfo(name="end_time", description="The end time of the chunk in seconds", type="float"),
                AttributeInfo(name="speaker_count", description="The number of different speakers in the chunk", type="integer"),
            ],
            "subtopic": [
                AttributeInfo(name="meeting_id", description="The unique identifier for the meeting", type="string"),
                AttributeInfo(name="meeting_title", description="The title of the meeting", type="string"),
                AttributeInfo(name="meeting_date", description="The date of the meeting in ISO format (YYYY-MM-DD)", type="string"),
                AttributeInfo(name="audio_file", description="The name of the audio file for the meeting", type="string"),
                AttributeInfo(name="main_topic", description="The main topic of the summarized sub-chunk", type="string"),
                AttributeInfo(name="summaery_index", description="The index of the summary sub-chunk", type="integer"),
            ],
        }

        # Define document content descriptions for SelfQueryRetriever
        self.document_content_descriptions = {
            "chunks": "Semantically grouped chunks of meeting transcript dialogue with speaker labels and timestamps",
            "subtopic": "Summarized sub-topic of a meeting transcript",
        }

        print(f"✅ VectorDBManager for collections {list(self.COLLECTION_NAMES.values())} initialized.")

    def _clean_text_with_gemini(self, formatted_text: str) -> str:
        """
        Gemini 2.5 Flash를 사용해서 [Speaker X, MM:SS] 형식의 정보를 제거합니다.

        Args:
            formatted_text (str): [Speaker X, MM:SS] 형식이 포함된 텍스트

        Returns:
            str: 순수한 대화 텍스트 (speaker와 시간 정보 제거)
        """
        try:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                print("⚠️ GOOGLE_API_KEY가 설정되지 않았습니다. 원본 텍스트를 반환합니다.")
                return formatted_text

            client = genai.Client(api_key=api_key)

            prompt = f"""다음 텍스트에서 [Speaker X, MM:SS] 형식의 모든 정보를 제거하고, 순수한 대화 내용만 추출해주세요.
각 줄은 하나의 발언을 나타냅니다. 발언 내용만 남기고 화자와 시간 정보는 모두 제거해주세요.

입력 예시:
[Speaker 0, 00:15] 안녕하세요. 오늘 회의를 시작하겠습니다.
[Speaker 1, 00:30] 네, 반갑습니다.

출력 예시:
안녕하세요. 오늘 회의를 시작하겠습니다.
네, 반갑습니다.

처리할 텍스트:
{formatted_text}

순수한 대화 내용만 출력해주세요. 설명이나 추가 텍스트 없이 대화 내용만 반환하세요."""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            cleaned_text = response.text.strip()
            print(f"✅ Gemini로 텍스트 정제 완료 (원본 {len(formatted_text)}자 → 정제 {len(cleaned_text)}자)")
            return cleaned_text

        except Exception as e:
            print(f"⚠️ Gemini 텍스트 정제 중 오류 발생: {e}")
            print(f"📝 원본 텍스트를 사용합니다.")
            return formatted_text

    def add_meeting_as_chunk(self, meeting_id, title, meeting_date, audio_file, segments):
        """
        회의 대화 내용을 스마트하게 청크로 묶어 DB에 저장합니다.
        화자 변경, 시간 간격을 고려하여 청킹하며, Gemini를 사용해서 speaker와 시간 정보를 제거합니다.

        Args:
            meeting_id (str): 회의 ID
            title (str): 회의 제목
            meeting_date (str): 회의 일시
            audio_file (str): 오디오 파일명
            segments (list): 회의 대화 세그먼트 리스트
                각 세그먼트는 {'speaker_label', 'start_time', 'segment', ...} 포함
        """
        chunk_vdb = self.vectorstores['chunks']

        try:
            # 1. 스마트 청킹: 화자 변경과 시간 간격을 고려
            chunks = self._create_smart_chunks(segments, max_chunk_size=1000, time_gap_threshold=60)

            print(f"📦 스마트 청킹으로 {len(chunks)}개의 청크 생성 완료")

            # 2. Gemini로 각 청크의 텍스트 정제 (speaker와 시간 정보 제거)
            print(f"🤖 Gemini 2.5 Flash로 텍스트 정제 중...")
            for chunk in chunks:
                chunk['text'] = self._clean_text_with_gemini(chunk['text'])

            # 3. 각 청크를 Vector DB에 저장
            chunk_texts = []
            chunk_metadatas = []
            chunk_ids = []

            for i, chunk_info in enumerate(chunks):
                chunk_texts.append(chunk_info['text'])
                chunk_metadatas.append({
                    "meeting_id": meeting_id,
                    "dialogue_id": f"{meeting_id}_chunk_{i}",
                    "chunk_index": i,
                    "title": title,
                    "meeting_date": meeting_date,
                    "audio_file": audio_file,
                    "start_time": chunk_info['start_time'],
                    "end_time": chunk_info['end_time'],
                    "speaker_count": chunk_info['speaker_count']
                })
                chunk_ids.append(f"{meeting_id}_chunk_{i}")

            # Vector DB에 추가
            chunk_vdb.add_texts(
                texts=chunk_texts,
                metadatas=chunk_metadatas,
                ids=chunk_ids
            )

            print(f"✅ {len(chunks)}개의 스마트 청크를 meeting_chunks DB에 저장 완료 (meeting_id: {meeting_id})")

        except Exception as e:
            print(f"⚠️ 스마트 청킹 중 오류 발생: {e}")
            print(f"📝 대신 기본 청킹 방식을 사용합니다.")

            # 에러 발생 시 폴백: RecursiveCharacterTextSplitter 사용
            formatted_segments = []
            for seg in segments:
                speaker = seg.get('speaker_label', 'Unknown')
                start_time = seg.get('start_time', 0)
                text = seg.get('segment', '')
                minutes = int(start_time // 60)
                seconds = int(start_time % 60)
                time_str = f"{minutes:02d}:{seconds:02d}"
                formatted_text = f"[Speaker {speaker}, {time_str}] {text}"
                formatted_segments.append(formatted_text)

            full_text = "\n".join(formatted_segments)

            # RecursiveCharacterTextSplitter로 청킹
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n[Speaker", "\n\n", "\n", " ", ""]
            )

            split_chunks = text_splitter.split_text(full_text)

            # Gemini로 텍스트 정제
            print(f"🤖 Gemini 2.5 Flash로 폴백 텍스트 정제 중...")
            cleaned_chunks = [self._clean_text_with_gemini(chunk) for chunk in split_chunks]

            chunk_texts = []
            chunk_metadatas = []
            chunk_ids = []

            for i, chunk_text in enumerate(cleaned_chunks):
                chunk_texts.append(chunk_text)
                chunk_metadatas.append({
                    "meeting_id": meeting_id,
                    "dialogue_id": f"{meeting_id}_chunk_{i}",
                    "chunk_index": i,
                    "title": title,
                    "meeting_date": meeting_date,
                    "audio_file": audio_file
                })
                chunk_ids.append(f"{meeting_id}_chunk_{i}")

            chunk_vdb.add_texts(
                texts=chunk_texts,
                metadatas=chunk_metadatas,
                ids=chunk_ids
            )

            print(f"✅ {len(split_chunks)}개의 청크를 meeting_chunks DB에 저장 완료 (폴백 모드)")

    def _create_smart_chunks(self, segments, max_chunk_size=1000, time_gap_threshold=60):
        """
        화자 변경, 시간 간격을 고려한 스마트 청킹

        Args:
            segments (list): 회의 대화 세그먼트 리스트
            max_chunk_size (int): 최대 청크 크기 (문자 수)
            time_gap_threshold (int): 시간 간격 임계값 (초)

        Returns:
            list: 청크 정보 리스트 [{'text': str, 'start_time': float, 'end_time': float, 'speaker_count': int}]
        """
        chunks = []
        current_chunk = []
        current_chunk_text = ""
        current_speaker = None
        last_time = 0
        speakers_in_chunk = set()

        for seg in segments:
            speaker = seg.get('speaker_label', 'Unknown')
            start_time = seg.get('start_time', 0)
            text = seg.get('segment', '')

            # 시간을 MM:SS 형식으로 변환
            minutes = int(start_time // 60)
            seconds = int(start_time % 60)
            time_str = f"{minutes:02d}:{seconds:02d}"

            # 포맷팅된 텍스트
            formatted_text = f"[Speaker {speaker}, {time_str}] {text}"

            # 청크 분리 조건:
            # 1. 현재 청크 크기가 max_chunk_size를 초과
            # 2. 시간 간격이 time_gap_threshold 초과 (긴 침묵이나 주제 전환 가능성)
            # 3. 화자가 변경되고 현재 청크가 충분히 큼 (500자 이상)

            time_gap = start_time - last_time
            should_split = False

            if len(current_chunk_text) + len(formatted_text) > max_chunk_size:
                should_split = True
            elif time_gap > time_gap_threshold and len(current_chunk_text) > 200:
                should_split = True
            elif speaker != current_speaker and len(current_chunk_text) > 500:
                # 화자 변경 시 적당한 크기면 분리
                should_split = True

            if should_split and current_chunk:
                # 현재 청크 저장
                chunks.append({
                    'text': current_chunk_text.strip(),
                    'start_time': current_chunk[0].get('start_time', 0),
                    'end_time': current_chunk[-1].get('start_time', 0),
                    'speaker_count': len(speakers_in_chunk)
                })

                # 새 청크 시작
                current_chunk = []
                current_chunk_text = ""
                speakers_in_chunk = set()

            # 현재 청크에 추가
            current_chunk.append(seg)
            current_chunk_text += formatted_text + "\n"
            speakers_in_chunk.add(speaker)
            current_speaker = speaker
            last_time = start_time

        # 마지막 청크 저장
        if current_chunk:
            chunks.append({
                'text': current_chunk_text.strip(),
                'start_time': current_chunk[0].get('start_time', 0),
                'end_time': current_chunk[-1].get('start_time', 0),
                'speaker_count': len(speakers_in_chunk)
            })

        return chunks


    def add_meeting_as_subtopic(self, meeting_id, title, meeting_date, audio_file, summary_content):
        """스크립트 전체를 소주제별 청크로 DB에 저장합니다."""

        
        # 1. 생성된 요약을 주제별로 파싱
        # "### "로 분리하되, 첫 번째 요소가 공백일 경우를 대비해 filter(None, ...) 사용
        summary_chunks = summary_content.split('\n### ')
        summary_chunks = [chunk.strip() for chunk in summary_chunks if chunk.strip()]
        
        # 첫 번째 청크에 "### "가 누락되었을 수 있으므로, 첫 번째 청크만 따로 처리
        # if summary_chunks and not summary_chunks[0].startswith('###'):
        #      # 첫번째 청크가 ###로 시작하지 않으면 ###를 붙여준다.
        #      if summary_chunks[0].count('\n') > 0:
        #          summary_chunks[0] = '### ' + summary_chunks[0]

        print("===============summary_chunks=================")
        print(summary_chunks)
        
        # 2. 각 요약 chunk를 Summary_Analysis_DB에 저장
        subtopic_vdb = self.vectorstores['subtopic']
        chunk_texts = []
        chunk_metadatas = []
        chunk_ids = []

        for i, chunk in enumerate(summary_chunks):
            # '### '가 없는 경우를 대비하여, 첫 줄을 main_topic으로 추출
            lines = chunk.split('\n')
            main_topic = lines[0].replace('### ', '').strip()
            
            # 실제 저장될 내용은 '### '를 포함한 전체 청크
            full_chunk_content = '### ' + chunk if not chunk.startswith('###') else chunk

            chunk_texts.append(full_chunk_content)
            chunk_metadatas.append({
                "meeting_id": meeting_id,
                "meeting_title": title,
                "meeting_date": meeting_date,
                "audio_file": audio_file,
                "main_topic": main_topic,
                "summary_index": i
            })
            chunk_ids.append(f"{meeting_id}_summary_{i}")

        if chunk_texts:
            subtopic_vdb.add_texts(texts=chunk_texts, metadatas=chunk_metadatas, ids=chunk_ids)
            print(f"📄 요약 결과 {len(chunk_texts)}개를 Summary_Analysis_DB에 저장했습니다.")
            return summary_chunks
        else:
            print("⚠️ 요약 결과에서 유효한 청크를 찾지 못했습니다.")



    
    
    def search(self,
             db_type: str,
             query: str,
             k: int = 5,
             retriever_type: str = "similarity",
             filter_criteria: dict = None,
             score_threshold: float = None,  # <-- [수정됨] 점수 임계값 추가
             mmr_fetch_k: int = 20,         # <-- [수정됨] MMR fetch_k 추가
             mmr_lambda_mult: float = 0.5   # <-- [수정됨] MMR lambda_mult 추가
             ) -> list:
        """
        지정된 DB에서 쿼리와 필터 조건을 사용하여 문서를 검색합니다.
        score_threshold가 지정되면 retriever_type은 'similarity_score_threshold'로 자동 변경됩니다.

        Args:
            db_type (str): 검색할 DB 타입 ('chunks', 'subtopic').
            query (str): 검색할 텍스트 쿼리.
            k (int, optional): 반환할 결과의 수. Defaults to 5.
            retriever_type (str, optional): 사용할 리트리버 타입 ('similarity', 'mmr', 'self_query', 'similarity_score_threshold'). Defaults to "similarity".
            filter_criteria (dict, optional): 메타데이터 필터링 조건 (예: {'meeting_id': '...', 'audio_file': '...'}). Defaults to None.
            score_threshold (float, optional): 유사도 점수 임계값 (0.0~1.0). Defaults to None.
            mmr_fetch_k (int, optional): MMR에서 초기 fetch할 문서 수. Defaults to 20.
            mmr_lambda_mult (float, optional): MMR의 다양성 파라미터 (0.0~1.0). Defaults to 0.5.

        Returns:
            list: LangChain Document 객체 리스트.
        """
        # 1. Validate inputs
        if db_type not in self.vectorstores:
            raise ValueError(f"Unknown db_type: {db_type}. Available types are {list(self.vectorstores.keys())}")

        # [수정됨] "similarity_score_threshold"를 유효한 타입으로 허용
        allowed_types = ["similarity", "mmr", "self_query", "similarity_score_threshold"]
        if retriever_type not in allowed_types:
            raise ValueError(f"Unsupported retriever_type: {retriever_type}. Choose from {allowed_types}.")

        # [수정됨] score_threshold가 제공되면, retriever_type을 강제로 변경
        current_retriever_type = retriever_type
        if score_threshold is not None and retriever_type == "similarity":
            current_retriever_type = "similarity_score_threshold"
            print(f"ℹ️ score_threshold provided. Changing retriever_type to 'similarity_score_threshold'.")

        vdb = self.vectorstores[db_type]
        results = []

        # 2. Handle 'similarity', 'mmr', 'similarity_score_threshold' retrievers
        if current_retriever_type in ["similarity", "mmr", "similarity_score_threshold"]:
            search_kwargs = {'k': k}
            if filter_criteria:
                search_kwargs['filter'] = filter_criteria

            # [수정됨] 타입에 따라 search_kwargs 동적 구성
            if current_retriever_type == "similarity_score_threshold":
                if score_threshold is None:
                    raise ValueError("score_threshold must be provided when retriever_type is 'similarity_score_threshold'")
                search_kwargs['score_threshold'] = score_threshold

            elif current_retriever_type == "mmr":
                search_kwargs['fetch_k'] = mmr_fetch_k
                search_kwargs['lambda_mult'] = mmr_lambda_mult

            retriever = vdb.as_retriever(
                search_type=current_retriever_type,
                search_kwargs=search_kwargs
            )
            results = retriever.invoke(query)

        # 3. Handle 'self_query' retriever
        elif current_retriever_type == "self_query":
            # (참고: SelfQueryRetriever는 기본적으로 내부에서 similarity_search를 사용합니다.)
            # (여기서 점수 기반 필터링을 하려면, SelfQueryRetriever를 커스텀해야 할 수도 있습니다.)
            metadata_info = self.metadata_field_infos[db_type]
            doc_description = self.document_content_descriptions[db_type]

            retriever = SelfQueryRetriever.from_llm(
                self.llm,
                vdb,
                doc_description,
                metadata_info,
                verbose=True,
                base_filter=filter_criteria,
                # [개선 아이디어] SelfQueryRetriever가 반환할 k의 개수를 설정할 수 있습니다.
                # 다만, invoke 시점이 아닌 생성 시점에 search_kwargs를 넘겨야 할 수 있습니다. (LangChain 버전에 따라 다름)
                # enable_limit=True를 사용하고 쿼리에 "top 3 results" 등을 포함시켜야 할 수도 있습니다.
            )
            results = retriever.invoke(query)

            # [수정됨] SelfQuery 이후에도 k개만 반환하도록 강제 (필요시)
            # SelfQueryRetriever는 k를 LLM이 추론하게 하므로, k가 무시될 수 있습니다.
            # 만약 결과가 너무 많다면, k만큼 잘라냅니다.
            if len(results) > k:
                 print(f"ℹ️ SelfQuery found {len(results)} results. Truncating to k={k}.")
                 results = results[:k]

        print(f"✅ Found {len(results)} documents from '{self.COLLECTION_NAMES[db_type]}' for query: '{query}'")
        return results

    
    def get_summary_by_meeting_id(self, meeting_id: str) -> str:
        """
        meeting_id로 문단 요약을 summary_index 순서대로 가져와서 하나의 문자열로 결합합니다.

        Args:
            meeting_id (str): 회의 ID

        Returns:
            str: summary_index 순서대로 결합된 전체 문단 요약 텍스트
                 (요약이 없으면 빈 문자열 반환)
        """
        try:
            # meeting_subtopic 컬렉션에서 해당 meeting_id의 모든 청크 조회
            collection = self.client.get_collection(name=self.COLLECTION_NAMES['subtopic'])

            # meeting_id로 필터링하여 모든 항목 가져오기
            results = collection.get(
                where={"meeting_id": meeting_id},
                include=["documents", "metadatas"]
            )

            if not results or not results.get('documents'):
                print(f"⚠️ meeting_id '{meeting_id}'에 대한 문단 요약을 찾을 수 없습니다.")
                return ""

            # documents와 metadatas를 summary_index 순서로 정렬
            documents = results['documents']
            metadatas = results['metadatas']

            # (summary_index, document) 튜플 리스트 생성 후 정렬
            indexed_docs = []
            for doc, meta in zip(documents, metadatas):
                summary_index = meta.get('summary_index', 0)
                indexed_docs.append((summary_index, doc))

            # summary_index 기준으로 정렬
            indexed_docs.sort(key=lambda x: x[0])

            # 문서들을 순서대로 결합 (각 문서 사이에 줄바꿈 2개 추가)
            full_summary = "\n\n".join([doc for _, doc in indexed_docs])

            print(f"✅ meeting_id '{meeting_id}'에 대한 {len(indexed_docs)}개의 문단 요약을 순서대로 가져왔습니다.")
            return full_summary

        except Exception as e:
            print(f"❌ 문단 요약 조회 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return ""

    def delete_from_collection(self, db_type, meeting_id=None, audio_file=None, title=None):
        """
        지정된 벡터 DB 컬렉션에서 항목을 삭제합니다.
        meeting_id, audio_file, title 중 하나 이상이 제공되면 해당 조건에 맞는 항목을 삭제합니다.
        아무것도 제공되지 않으면 해당 db_type의 전체 컬렉션을 삭제합니다.
        """
        if db_type not in self.vectorstores:
            raise ValueError(f"Unknown db_type: {db_type}. Must be one of {list(self.COLLECTION_NAMES.keys())}")

        collection = self.client.get_or_create_collection(name=self.COLLECTION_NAMES[db_type])

        filters = {}
        if meeting_id:
            filters["meeting_id"] = meeting_id
        if audio_file:
            filters["audio_file"] = audio_file
        if title:
            filters["title"] = title

        if filters:
            # 특정 필터가 있는 경우
            print(f"🗑️ Deleting from '{db_type}' collection with filters: {filters}")
            collection.delete(where=filters)
            print(f"✅ Deletion from '{db_type}' collection complete.")
        else:
            # 필터가 없는 경우, 전체 컬렉션 삭제
            print(f"⚠️ No specific filters provided. Deleting ALL items from '{db_type}' collection.")
            collection.delete(where={}) # deletes all items
            print(f"✅ All items deleted from '{db_type}' collection.")



# --- 싱글톤 인스턴스 생성 ---
# DB 파일은 minute_ai/database/vector_db 경로에 저장됩니다.
# vector_db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'vector_db')
vdb_manager = VectorDBManager()
