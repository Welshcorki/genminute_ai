# genminute

AI 기반 회의록 자동 생성 시스템

회의 음성/영상을 업로드하면 자동으로 음성인식(STT), 회의록 생성, 마인드맵 생성, RAG 기반 챗봇을 제공하는 웹 애플리케이션입니다.

## 주요 기능

### 1. 음성/영상 파일 업로드 및 전사
- **지원 포맷**: WAV, MP3, M4A, FLAC, MP4 (최대 500MB)
- **자동 화자 분리**: Gemini 2.5 Pro를 활용한 화자 구분 (SPEAKER_00, SPEAKER_01...)
- **타임스탬프**: 각 발언에 정확한 시간 정보 (MM:SS:mmm)
- **신뢰도 점수**: 각 세그먼트별 전사 정확도 (0.0 ~ 1.0)
- **영상 변환**: ffmpeg를 통한 자동 오디오 추출

### 2. AI 기반 회의록 자동 생성
- **단락 요약**: 주제별로 그룹화된 요약문 (마크다운 ### 헤더 형식)
- **정식 회의록**:
  - 회의 정보 (제목, 날짜, 참석자)
  - 전체 요약
  - 주요 논의 사항
  - 액션 아이템 (담당자, 기한)
  - 향후 계획
- **인용 표시**: `[cite: 1, 2]` 형식으로 출처 추적

### 3. 마인드맵 시각화
- 회의 내용의 핵심 키워드를 계층적 마인드맵으로 자동 생성
- Markmap 라이브러리를 활용한 인터랙티브 시각화
- 확대/축소, 드래그 가능한 SVG 렌더링

### 4. AI 챗봇 (RAG 기반)
- **Retrieval-Augmented Generation (RAG)** 아키텍처
- ChromaDB 벡터 데이터베이스를 활용한 의미 기반 검색
- 회의록 청크 및 주제별 요약에서 관련 정보 추출
- Gemini 2.5 Flash를 통한 실시간 답변 생성
- 출처 인용 (회의 정보, 타임스탬프)

### 5. 회의록 관리
- **제목/날짜 수정**: 인라인 편집 기능 (소유자 전용)
- **공유 기능**: 이메일 기반 회의록 공유
- **접근 제어**: 소유자/공유 사용자/관리자 역할 기반 권한
- **화자 비중 분석**: 발언 분량 시각화 (Chart.js)
- **오디오/비디오 재생**: 타임스탬프 동기화 재생

### 6. 사용자 인증
- **Google 계정 로그인**: Firebase Authentication
- **세션 관리**: Flask 세션 기반
- **관리자 모드**: 디버그 도구 및 고급 기능 접근

---

## 기술 스택

### Backend
- **프레임워크**: Flask 3.1.2
- **AI/ML**:
  - Google Gemini 2.5 Pro (STT, 요약, 회의록)
  - Google Gemini 2.5 Flash (마인드맵, 챗봇)
- **벡터 데이터베이스**: ChromaDB 1.3.0 + LangChain 1.0.5
- **데이터베이스**: SQLite (관계형 데이터), ChromaDB (벡터 임베딩)
- **인증**: Firebase Admin SDK 7.1.0
- **임베딩**: OpenAI Embeddings (text-embedding-ada-002)
- **오디오 처리**: ffmpeg

### Frontend
- **템플릿 엔진**: Jinja2
- **스타일링**: 커스텀 CSS (Tailwind 스타일 유틸리티 클래스)
- **JavaScript**: Vanilla JS + Fetch API
- **차트**: Chart.js (화자 비중 시각화)
- **마인드맵**: Markmap (SVG 기반 인터랙티브 렌더링)

---

## 프로젝트 구조

```
seoulloc/
├── app.py                          # Flask 애플리케이션 진입점
├── config.py                       # 중앙 집중식 설정 관리
├── init_db.py                      # 데이터베이스 초기화 스크립트
│
├── routes/                         # HTTP 라우트 핸들러 (Blueprint)
│   ├── __init__.py
│   ├── admin.py                    # 관리자 전용 디버그 기능
│   ├── auth.py                     # 인증 및 사용자 관리
│   ├── chat.py                     # AI 챗봇 Q&A
│   ├── meetings.py                 # 회의록 CRUD 작업
│   └── summary.py                  # 요약 및 회의록 생성
│
├── services/                       # 비즈니스 로직 레이어
│   ├── __init__.py
│   └── upload_service.py           # 파일 업로드 및 처리 로직
│
├── utils/                          # 인프라 및 유틸리티
│   ├── analysis.py                 # 화자 비중 분석
│   ├── chat_manager.py             # RAG 기반 챗봇 매니저
│   ├── db_manager.py               # SQLite 데이터베이스 작업
│   ├── decorators.py               # Flask 라우트 데코레이터
│   ├── firebase_auth.py            # Firebase 인증
│   ├── stt.py                      # Gemini STT 및 AI 처리
│   ├── user_manager.py             # 사용자 및 권한 관리
│   ├── validation.py               # 입력 검증 유틸리티
│   └── vector_db_manager.py        # ChromaDB 벡터 데이터베이스
│
├── templates/                      # Jinja2 HTML 템플릿
│   ├── layout.html                 # 기본 레이아웃 (네비게이션, 챗봇)
│   ├── index.html                  # 업로드 페이지
│   ├── viewer.html                 # 회의록 뷰어
│   ├── shared-notes.html           # 공유된 회의록 목록
│   └── ...                         # 기타 테스트 페이지
│
├── static/                         # 정적 파일
│   ├── css/
│   │   └── style.css               # 메인 스타일시트
│   └── js/
│       ├── script.js               # 챗봇 UI 로직
│       └── viewer.js               # 뷰어 페이지 로직
│
├── database/                       # 데이터베이스 저장소
│   ├── minute_ai.db                # SQLite 데이터베이스
│   └── chroma_db/                  # ChromaDB 영구 저장소
│
├── uploads/                        # 업로드된 오디오/비디오 파일
├── requirements.txt                # Python 패키지 종속성
├── .env                            # 환경 변수 (비공개)
└── README.md                       # 프로젝트 문서 (본 파일)
```

---

## 데이터베이스 스키마

### SQLite (minute_ai.db)

#### meeting_dialogues
회의 전사 세그먼트 저장
```sql
- segment_id: INTEGER PRIMARY KEY AUTOINCREMENT
- meeting_id: TEXT (UUID, 세그먼트 그룹화)
- meeting_date: TEXT (YYYY-MM-DD HH:MM:SS)
- speaker_label: TEXT (예: "1", "2", "3")
- start_time: REAL (시작 시간, 초)
- segment: TEXT (전사 텍스트)
- confidence: REAL (0.0 ~ 1.0)
- audio_file: TEXT (파일명)
- title: TEXT (회의 제목)
- owner_id: INTEGER (users 외래키)
```

#### meeting_minutes
생성된 회의록 저장
```sql
- id: INTEGER PRIMARY KEY AUTOINCREMENT
- meeting_id: TEXT UNIQUE (meeting_dialogues 연결)
- minutes_content: TEXT (마크다운 형식)
- created_at: DATETIME
- owner_id: INTEGER
```

#### meeting_mindmap
마인드맵 데이터 저장
```sql
- id: INTEGER PRIMARY KEY AUTOINCREMENT
- meeting_id: TEXT UNIQUE
- mindmap_content: TEXT (마크다운 형식)
- created_at: DATETIME
```

#### users
사용자 계정 및 인증
```sql
- id: INTEGER PRIMARY KEY AUTOINCREMENT
- google_id: TEXT UNIQUE (Firebase UID)
- email: TEXT UNIQUE
- name: TEXT
- profile_picture: TEXT (URL)
- role: TEXT ('user' 또는 'admin')
- created_at: DATETIME
```

#### meeting_shares
회의록 접근 제어
```sql
- id: INTEGER PRIMARY KEY AUTOINCREMENT
- meeting_id: TEXT (공유되는 회의)
- owner_id: INTEGER (소유자)
- shared_with_user_id: INTEGER (접근 권한을 받은 사용자)
- permission: TEXT ('read')
- created_at: DATETIME
```

### ChromaDB (벡터 데이터베이스)

#### meeting_chunks
스마트 청킹된 회의 전사본 + 임베딩
```python
Metadata:
- meeting_id: UUID
- dialogue_id: meeting_id_chunk_N
- chunk_index: 정수 (순서)
- title: 회의 제목
- meeting_date: YYYY-MM-DD HH:MM:SS
- audio_file: 파일명
- start_time: 시작 시간 (초)
- end_time: 종료 시간 (초)
- speaker_count: 화자 수

Content: 정제된 전사 텍스트 (화자 라벨 및 타임스탬프 제거)
```

#### meeting_subtopic
주제별 단락 요약
```python
Metadata:
- meeting_id: UUID
- meeting_title: 회의 제목
- meeting_date: YYYY-MM-DD HH:MM:SS
- audio_file: 파일명
- main_topic: ### 헤더에서 추출
- summary_index: 정수 (순서)

Content: "### 주제\n* 포인트 1\n* 포인트 2..." 형식
```

---

## API 엔드포인트

### 인증 (auth.py)

| 엔드포인트 | 메서드 | 인증 | 설명 |
|----------|--------|------|------|
| `/login` | GET | 불필요 | 로그인 페이지 표시 |
| `/api/login` | POST | 불필요 | Firebase ID 토큰 검증 및 세션 생성 |
| `/api/logout` | POST | 불필요 | 세션 종료 |
| `/api/me` | GET | 필수 | 현재 사용자 정보 조회 |

### 회의록 관리 (meetings.py)

| 엔드포인트 | 메서드 | 인증 | 설명 |
|----------|--------|------|------|
| `/` | GET | 필수 | 업로드 페이지 |
| `/notes` | GET | 필수 | 내 회의록 목록 |
| `/shared-notes` | GET | 필수 | 공유받은 회의록 목록 |
| `/view/<meeting_id>` | GET | 필수 | 회의록 뷰어 페이지 |
| `/api/meeting/<meeting_id>` | GET | 필수 | 회의록 데이터 조회 |
| `/upload` | POST | 필수 | 오디오/비디오 파일 업로드 (SSE 스트리밍) |
| `/api/delete_meeting/<meeting_id>` | POST | 필수 | 회의록 삭제 (소유자 전용) |
| `/api/update_title/<meeting_id>` | POST | 필수 | 제목 수정 (소유자 전용) |
| `/api/update_date/<meeting_id>` | POST | 필수 | 날짜 수정 (소유자 전용) |
| `/api/share/<meeting_id>` | POST | 필수 | 이메일로 회의록 공유 (소유자 전용) |
| `/api/shared_users/<meeting_id>` | GET | 필수 | 공유된 사용자 목록 조회 |
| `/api/unshare/<meeting_id>/<user_id>` | POST | 필수 | 공유 해제 (소유자 전용) |
| `/api/mindmap/<meeting_id>` | GET | 필수 | 마인드맵 데이터 조회 |

### 요약 및 회의록 (summary.py)

| 엔드포인트 | 메서드 | 인증 | 설명 |
|----------|--------|------|------|
| `/api/summarize/<meeting_id>` | POST | 필수 | 단락 요약 생성 |
| `/api/check_summary/<meeting_id>` | GET | 필수 | 요약 존재 여부 확인 |
| `/api/generate_minutes/<meeting_id>` | POST | 필수 | 정식 회의록 생성 |
| `/api/get_minutes/<meeting_id>` | GET | 필수 | 기존 회의록 조회 |

### 챗봇 (chat.py)

| 엔드포인트 | 메서드 | 인증 | 설명 |
|----------|--------|------|------|
| `/api/chat` | POST | 필수 | AI 챗봇 Q&A |

**요청 예시:**
```json
{
  "query": "예산에 대해 무엇을 논의했나요?",
  "meeting_id": "선택적-특정-회의-ID"
}
```

**응답 예시:**
```json
{
  "success": true,
  "answer": "회의 내용 기반 AI 생성 답변",
  "sources": [
    {
      "type": "chunk",
      "meeting_id": "...",
      "title": "...",
      "meeting_date": "...",
      "start_time": 0,
      "end_time": 120
    }
  ]
}
```

---

## 설치 및 실행

### 1. 사전 요구사항
- Python 3.10 이상
- ffmpeg (영상 변환용)
- SQLite 3.x

### 2. 환경 설정

#### 2.1 가상환경 생성
```bash
conda env create -f environment_crossplatform.yml
conda activate genminute
```

#### 2.2 환경 변수 설정
`.env` 파일 생성 (프로젝트 루트):
```env
# Flask 설정
FLASK_SECRET_KEY=<256비트 랜덤 hex>
FLASK_DEBUG=False
FLASK_PORT=5050

# Firebase 설정 (Firebase Console에서 확인)
FIREBASE_API_KEY=<your-api-key>
FIREBASE_AUTH_DOMAIN=<your-app>.firebaseapp.com
FIREBASE_PROJECT_ID=<your-project-id>
FIREBASE_STORAGE_BUCKET=<your-app>.appspot.com
FIREBASE_MESSAGING_SENDER_ID=<sender-id>
FIREBASE_APP_ID=<app-id>
FIREBASE_MEASUREMENT_ID=<measurement-id>

# API 키
GOOGLE_API_KEY=<Google Cloud API 키>
OPENAI_API_KEY=<OpenAI API 키>

# 관리자 이메일 (쉼표로 구분)
ADMIN_EMAILS=admin1@example.com,admin2@example.com
```

#### 2.3 Firebase 서비스 계정 키
프로젝트 루트에 `firebase-adminsdk.json` 파일 배치:
1. Firebase Console → Project Settings → Service Accounts
2. "Generate New Private Key" 클릭
3. 다운로드한 JSON 파일을 `firebase-adminsdk.json`로 저장

### 3. 애플리케이션 실행
```bash
python app.py
```

브라우저에서 `http://localhost:5050` 접속

**참고:** 데이터베이스 테이블은 `app.py` 실행 시 자동으로 생성됩니다. 별도의 초기화 스크립트 실행이 필요 없습니다.

**선택사항 - 수동 DB 초기화:**
```bash
# DB를 완전히 재생성하거나 초기화하고 싶을 때만 실행
python init_db.py
```

---

## 주요 워크플로우

### 1. 회의록 생성 워크플로우
```
1. 사용자가 오디오/비디오 파일 업로드
   ↓
2. 파일 저장 (/uploads/<uuid>_<filename>)
   ↓
3. (영상인 경우) ffmpeg로 오디오 추출
   ↓
4. Gemini 2.5 Pro STT 처리
   → 화자 분리 + 타임스탬프 + 신뢰도
   ↓
5. SQLite에 세그먼트 저장 (meeting_dialogues)
   ↓
6. 스마트 청킹 + 임베딩 → ChromaDB (meeting_chunks)
   ↓
7. Gemini로 단락 요약 생성
   ↓
8. 주제별 요약 임베딩 → ChromaDB (meeting_subtopic)
   ↓
9. Gemini로 마인드맵 키워드 추출
   ↓
10. SQLite에 마인드맵 저장 (meeting_mindmap)
```

### 2. 챗봇 쿼리 워크플로우
```
1. 사용자가 질문 입력
   ↓
2. 접근 가능한 회의록 ID 조회
   → 소유 + 공유받은 회의록
   ↓
3. 벡터 검색 (meeting_chunks + meeting_subtopic)
   → 각각 상위 3개 문서
   ↓
4. 컨텍스트 포맷팅 (메타데이터 포함)
   ↓
5. Gemini 2.5 Flash로 답변 생성
   → 컨텍스트 기반만 사용
   ↓
6. 출처 정보 추출
   → 회의 ID, 제목, 날짜, 타임스탬프
   ↓
7. JSON 응답 반환 (답변 + 출처)
```

---

## 핵심 알고리즘

### 스마트 청킹
```python
def _create_smart_chunks(segments, max_chunk_size=1000, time_gap_threshold=60):
    """
    청크 분할 조건:
    1. 청크 크기가 max_chunk_size 초과
    2. 시간 간격 > time_gap_threshold (주제 변경 감지)
    3. 화자 변경 AND 청크 크기 > 500자

    → 의미적 일관성 유지 + 검색 품질 향상
    """
```

### RAG 파이프라인
```python
def process_query(query, meeting_id, accessible_meeting_ids):
    # 1. 벡터 검색 (청크 + 요약)
    chunks = search_meeting_chunks(query, accessible_meeting_ids, k=3)
    subtopics = search_meeting_subtopic(query, accessible_meeting_ids, k=3)

    # 2. 컨텍스트 생성
    context = format_context(chunks + subtopics)

    # 3. AI 답변 생성
    answer = gemini_generate(query, context)

    # 4. 출처 추출
    sources = extract_sources(chunks + subtopics)

    return answer, sources
```

---

## 보안 고려사항

### 인증
- Firebase ID 토큰 검증 (모든 요청)
- Flask 세션 기반 상태 관리
- 256비트 랜덤 시크릿 키

### 권한 제어
- 라우트 레벨 데코레이터 (`@login_required`, `@admin_required`)
- 데이터베이스 레벨 권한 체크 (`can_access_meeting`, `can_edit_meeting`)
- 쿼리 필터링 (accessible_meeting_ids)

### 입력 검증
- 파일 타입 화이트리스트 (wav, mp3, m4a, flac, mp4)
- 파일 크기 제한 (500MB)
- 제목 길이 검증 (100자)
- 날짜 형식 검증

### SQL 인젝션 방지
- 전체 코드에 파라미터화된 쿼리 사용
- SQL 문자열 연결 없음

### 파일 업로드 보안
- `werkzeug.secure_filename()` 사용
- UUID 접두사로 이름 충돌 방지
- 별도 업로드 디렉토리
- MIME 타입 검증

---

## 성능 최적화

### 데이터베이스
- 자주 쿼리되는 컬럼에 인덱스 (meeting_id, owner_id)
- SQLite Row factory로 딕셔너리 접근
- DatabaseManager 싱글톤 패턴

### 벡터 데이터베이스
- 스마트 청킹으로 문서 수 감소
- ChromaDB의 효율적인 임베딩 저장
- 필터링된 검색으로 연산 감소

### 캐싱
- Firebase SDK 초기화 전역 캐싱
- 싱글톤 매니저 (STT, Chat, Vector DB)

### 비동기 처리
- SSE 스트리밍으로 긴 작업 처리
- 요약 생성 백그라운드 처리
- 비블로킹 오디오 변환 (subprocess)

---

## 배포 고려사항

### 환경 변수
`.env` 파일에 필수 항목:
```
FLASK_SECRET_KEY=<256비트 랜덤 hex>
FLASK_DEBUG=False
FLASK_PORT=5050

FIREBASE_API_KEY=<Firebase 설정>
... (모든 Firebase 클라이언트 설정)

GOOGLE_API_KEY=<Google Cloud API 키>
OPENAI_API_KEY=<OpenAI API 키>

ADMIN_EMAILS=admin1@example.com,admin2@example.com
```

### 시스템 종속성
- Python 3.10+
- ffmpeg (영상 변환용)
- SQLite 3.x

### 프로덕션 권장사항
- Gunicorn 또는 uWSGI 사용 (Flask 개발 서버 대신)
- 리버스 프록시 설정 (Nginx)
- HTTPS 활성화
- 데이터베이스 백업 설정 (SQLite → 클라우드 스토리지)
- API 사용량 모니터링 (Gemini, OpenAI 할당량)
- 로깅 집계 설정 (예: Sentry)

---

## 문제 해결

### 1. ffmpeg 오류
```bash
# ffmpeg가 설치되어 있는지 확인
which ffmpeg  # Mac/Linux
where ffmpeg  # Windows

# 없으면 설치 필요
# Mac: brew install ffmpeg
# Ubuntu: sudo apt-get install ffmpeg
# Windows: https://ffmpeg.org/download.html
```

### 2. SQLite DB 오류
```bash
# 증상: "no such table: meeting_dialogues" 에러
# 해결: DB 초기화
python init_db.py

# 또는 완전 재생성
rm database/minute_ai.db
python init_db.py
```

### 3. ChromaDB 오류
```bash
# ChromaDB 데이터베이스 초기화
rm -rf database/chroma_db
python app.py  # 자동으로 재생성됨
```

### 4. Firebase 인증 오류
```bash
# Firebase credentials 파일 경로 확인
ls -la firebase-adminsdk.json

# 없으면 Firebase Console에서 다운로드 후 프로젝트 루트에 저장
```

---

## 향후 개선 사항

### 기술 개선
- 실시간 협업 (WebSocket)
- 백그라운드 작업 큐 (Celery)
- Redis 세션 관리
- PostgreSQL 마이그레이션 (프로덕션)
- CDN 정적 자산 제공
- 다국어 UI (i18n)

### 기능 추가
- PDF/DOCX 내보내기
- 캘린더 통합 (Google Calendar, Outlook)
- 공유 이메일 알림
- 편집 버전 히스토리
- 고급 검색 필터 (날짜 범위, 화자, 키워드)
- 감정 분석
- 주제 모델링
- 회의 템플릿

### AI 개선
- 도메인별 파인튜닝 모델
- 화자 식별 웨이크워드 감지
- 실시간 전사 (스트리밍 STT)
- 멀티모달 분석 (비디오 + 오디오)

---

## 라이선스

이 프로젝트는 교육 및 연구 목적으로 개발되었습니다.

---

## 감사의 말

이 프로젝트는 다음 오픈소스 프로젝트들을 사용합니다:
- [Google Gemini](https://deepmind.google/technologies/gemini/)
- [LangChain](https://github.com/langchain-ai/langchain)
- [ChromaDB](https://github.com/chroma-core/chroma)
- [Flask](https://flask.palletsprojects.com/)
- [Firebase](https://firebase.google.com/)
