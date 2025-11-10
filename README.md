# 🎙️ Minute AI

AI 기반 회의록 자동 생성 시스템

회의 음성/영상을 업로드하면 자동으로 음성인식(STT), 회의록 생성, 마인드맵 생성, RAG 기반 챗봇을 제공하는 웹 애플리케이션입니다.

---

## ✨ 주요 기능

### 📝 자동 회의록 생성
- **음성인식(STT)**: OpenAI Whisper API로 화자 분리 및 타임스탬프 포함 음성 텍스트 변환
- **스마트 요약**: Google Gemini로 회의 내용을 문단별 구조화 요약
- **마인드맵 생성**: 회의 키워드를 시각화한 마인드맵 자동 생성

### 💬 RAG 챗봇
- **문맥 기반 질의응답**: ChromaDB 벡터 검색 + LangChain으로 회의 내용 기반 Q&A
- **메타데이터 필터링**: 화자, 시간대별 검색 가능
- **스마트 청킹**: 화자와 타임스탬프를 고려한 지능형 텍스트 분할

### 🎥 미디어 통합
- **스티키 플레이어**: 스크롤 중에도 항상 보이는 비디오/오디오 플레이어
- **타임스탬프 연동**: 스크립트 클릭 시 해당 시점으로 자동 이동
- **실시간 진행 상황**: SSE 기반 업로드/처리 상태 실시간 표시

### 🔐 인증 & 공유
- **Firebase 인증**: Google 로그인 지원
- **권한 관리**: 회의록 소유자/공유자 권한 분리
- **공유 기능**: 다른 사용자에게 회의록 공유 가능

---

## 🛠️ 기술 스택

### Backend
- **Framework**: Flask 3.1.2
- **STT**: OpenAI Whisper API
- **LLM**: Google Gemini 1.5 Flash, GPT-4o-mini
- **Vector DB**: ChromaDB 1.3.0
- **RAG**: LangChain 1.0.5
- **Database**: SQLite

### Frontend
- **Vanilla JavaScript** (SSE, Fetch API)
- **HTML5/CSS3**
- **Responsive Design**

### Infrastructure
- **Local**: Conda/Pip 환경
- **Cloud**: GCP Cloud Run (Docker)
- **Storage**: Firebase Storage (업로드 파일)
- **Auth**: Firebase Authentication

---

## 📋 목차
- [빠른 시작](#빠른-시작)
- [상세 설치 가이드](#상세-설치-가이드)
  - [로컬 개발 환경 (Windows/Mac/Linux)](#로컬-개발-환경)
  - [GCP 배포 환경](#gcp-배포-환경)
- [사용 방법](#사용-방법)
- [문제 해결](#문제-해결)
- [개발 정보](#개발-정보)

---

## 🚀 빠른 시작

```bash
# 1. 저장소 클론
git clone <repository-url>
cd minute_ai

# 2. Conda 환경 생성 및 활성화
conda env create -f environment_crossplatform.yml
conda activate genminute

# 3. 환경 변수 설정
cp .env.example .env
# .env 파일에 API 키 입력:
# - GOOGLE_GENAI_API_KEY
# - OPENAI_API_KEY

# 4. 데이터베이스 초기화
python init_db.py

# 5. 앱 실행
python app.py

# 🎉 브라우저에서 http://localhost:5000 접속
```

---

## 📚 상세 설치 가이드

### 🖥️ 로컬 개발 환경

#### 방법 1: Conda 사용 (추천)

```bash
# 1. Conda 환경 생성
conda env create -f environment_crossplatform.yml

# 2. 환경 활성화
conda activate genminute

# 3. .env 파일 설정
cp .env.example .env
# .env 파일에 다음 API 키 입력:
# GOOGLE_GENAI_API_KEY=your_gemini_api_key
# OPENAI_API_KEY=your_openai_api_key
# SECRET_KEY=your_flask_secret_key (랜덤 문자열)
# ADMIN_EMAILS=your@email.com (선택)

# 4. 데이터베이스 초기화 (처음 한 번만)
python init_db.py

# 5. 앱 실행
python app.py
```

#### 방법 2: pip 사용

```bash
# 1. Python 3.11.13 가상환경 생성 (정확한 버전 사용 권장)
python3.11 -m venv venv

# 2. 가상환경 활성화
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. 패키지 설치
pip install -r requirements_crossplatform.txt

# 4. Graphviz 시스템 설치 (마인드맵 기능용)
# Mac:
brew install graphviz
# Ubuntu/Debian:
sudo apt-get install graphviz
# Windows:
# https://graphviz.org/download/ 에서 다운로드 및 설치

# 5. .env 파일 설정
cp .env.example .env
# .env 파일에 API 키 입력

# 6. 데이터베이스 초기화 (처음 한 번만)
python init_db.py

# 7. 앱 실행
python app.py
```

---

### ☁️ GCP 배포 환경

#### 필수 환경 변수

```bash
# .env 파일 또는 Cloud Run 환경 변수로 설정
GOOGLE_GENAI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
FIREBASE_CREDENTIALS_PATH=path/to/firebase/credentials.json
SECRET_KEY=your_flask_secret_key
ADMIN_UID=your_firebase_admin_uid
```

#### Cloud Run 배포

```bash
# 1. Dockerfile 빌드
docker build -t gcr.io/[PROJECT-ID]/minute-ai:latest .

# 2. GCP Container Registry에 푸시
docker push gcr.io/[PROJECT-ID]/minute-ai:latest

# 3. Cloud Run 배포
gcloud run deploy minute-ai \
  --image gcr.io/[PROJECT-ID]/minute-ai:latest \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_GENAI_API_KEY=xxx,OPENAI_API_KEY=xxx
```

---

## 📖 사용 방법

### 1. 회의록 생성

1. **업로드**: 홈 화면에서 회의 음성/영상 파일 업로드 (mp3, mp4, wav, m4a 등)
2. **자동 처리**:
   - 🎤 음성인식 (STT)
   - 📝 문단별 요약 생성
   - 🗺️ 마인드맵 생성
3. **결과 확인**: 자동으로 회의록 뷰어로 이동

### 2. 회의록 열람

- **노트 탭**: 구조화된 회의록 확인 및 PDF 다운로드
- **스크립트 탭**: 화자별 타임스탬프 포함 전체 대화 내용
- **챗봇 탭**: RAG 기반으로 회의 내용 질의응답

### 3. 챗봇 사용

```
💬 질문 예시:
- "이번 회의의 주요 안건은 뭐였어?"
- "김철수 팀장이 말한 내용 요약해줘"
- "다음 회의 날짜가 언제야?"
- "프로젝트 마감일이 언제로 결정됐어?"
```

---

## 🔧 문제 해결

### 1. pydot 설치 오류
```bash
# Graphviz가 시스템에 설치되어 있는지 확인
which dot  # Mac/Linux
where dot  # Windows

# 없으면 시스템 레벨에서 설치 필요
# Mac: brew install graphviz
# Ubuntu: sudo apt-get install graphviz
# Windows: https://graphviz.org/download/
```

### 2. SQLite DB 오류
```bash
# 증상: "no such table: meeting_dialogues" 에러
# 원인: DB 파일은 있지만 테이블이 없음

# 해결: DB 초기화
python init_db.py

# 또는 완전 재생성
rm database/minute_ai.db
python init_db.py
```

### 3. ChromaDB 오류
```bash
# ChromaDB 데이터베이스 초기화
rm -rf database/vector_db
python app.py  # 자동으로 재생성됨
```

### 4. Firebase 인증 오류
```bash
# Firebase credentials 파일 경로 확인
ls -la firebase/  # credentials.json 파일이 있는지 확인

# 없으면 Firebase Console에서 다운로드 후 firebase/ 폴더에 저장
```

### 5. Windows에서 pywin32 오류
**해결책**: `requirements_crossplatform.txt`를 사용하세요. pywin32가 제거되어 있습니다.

Windows에서 필요한 경우:
```bash
pip install pywin32  # 선택적으로 설치
```

### 6. LangChain 버전 호환성
**권장**: 모든 LangChain 패키지를 1.0.x로 통일!

**해결책**: 최신 1.0.x 버전 사용 (2025년 11월 기준)

```bash
# ✅ 올바른 조합 (1.0.x 패밀리 - 최신!)
langchain==1.0.5
langchain-core==1.0.4
langchain-chroma==1.0.0
langchain-classic==1.0.0
langchain-community==0.4.1  # 아직 1.0 stable 없음
langchain-openai==1.0.2
langchain-text-splitters==1.0.0

# ⚠️ 구버전 조합 (작동하지만 비추천)
langchain==0.3.27
langchain-core==0.3.79
# ... 보안 패치, 버그 수정, 새 기능 놓침!

# ❌ 잘못된 조합 (버전 미스매치!)
langchain==0.3.27
langchain-core==1.0.2  # 충돌!
```

**1.0.x 사용의 장점:**
- 🔒 최신 보안 패치
- 🐛 버그 수정
- 🚀 성능 개선
- ✨ 새 기능 (create_agent 등)
- 📚 장기 지원 (LTS)

---

## 🔄 개발 정보

### 패키지 버전 업데이트

현재 환경의 패키지를 최신 호환 버전으로 업데이트:

```bash
# Conda
conda env update -f environment_crossplatform.yml --prune

# Pip
pip install -r requirements_crossplatform.txt --upgrade
```

### 환경 테스트

새로운 환경이 제대로 설정되었는지 확인:

```bash
# 기본 패키지 import 테스트
python test_environment.py

# LangChain 1.0 호환성 테스트 (OpenAI API 키 필요)
python test_langchain_1_0.py
```

### 기존 environment.yml과의 차이점

#### ✅ 개선 사항
1. **크로스 플랫폼 지원**: Windows/Mac/Linux 모두 동작
2. **최신 버전 업그레이드**: LangChain 0.3.x → 1.0.x
3. **불필요한 패키지 제거**: 개발 도구(Jupyter 등) 제거
4. **빌드 해시 제거**: 플랫폼 간 충돌 방지
5. **누락 패키지 추가**: pydot, graphviz 추가 (마인드맵 기능용)
6. **명확한 버전 관리**: 핵심 패키지만 버전 고정
7. **보안 강화**: 최신 보안 패치 적용
8. **재현성 보장**: Python 3.11.13으로 정확히 고정 (팀 협업/배포 일관성)

#### ❌ 제거된 패키지
- `pywin32` (Windows 전용)
- `ipykernel`, `jupyter_*` (개발 도구)
- 플랫폼 특정 빌드 해시

#### 🆙 업그레이드된 패키지
- `langchain`: 0.3.27 → **1.0.5** ⬆️
- `langchain-core`: 1.0.2 (충돌) → **1.0.4** ✅
- `langchain-chroma`: 1.0.0 (충돌) → **1.0.0** (올바른 버전)
- `langchain-openai`: 1.0.1 (충돌) → **1.0.2** ✅
- `langchain-community`: 0.3.31 → **0.4.1** ⬆️

### 프로젝트 구조

```
minute_ai/
├── app.py                           # Flask 메인 애플리케이션
├── init_db.py                       # 데이터베이스 초기화 스크립트
├── environment_crossplatform.yml    # Conda 환경 설정 (크로스 플랫폼)
├── requirements_crossplatform.txt   # Pip 패키지 목록 (크로스 플랫폼)
├── database/
│   ├── minute_ai.db                 # SQLite 데이터베이스
│   └── vector_db/                   # ChromaDB 벡터 데이터베이스
├── utils/
│   ├── db_manager.py                # SQLite 관리
│   ├── vector_db_manager.py         # ChromaDB + RAG 관리
│   ├── stt.py                       # OpenAI Whisper STT
│   └── chatbot_manager.py           # 챗봇 관리
├── static/
│   ├── css/style.css                # 스타일시트
│   └── js/
│       ├── script.js                # 메인 페이지 로직
│       └── viewer.js                # 회의록 뷰어 로직
├── templates/
│   ├── index.html                   # 홈 페이지
│   ├── viewer.html                  # 회의록 뷰어
│   └── ...
├── uploads/                         # 업로드 파일 임시 저장
├── firebase/
│   └── credentials.json             # Firebase 서비스 계정 키
└── markdown_folder/                 # 문서 폴더
```

---

## 📞 지원 및 기여

### 이슈 리포트
설치 중 문제가 발생하거나 버그를 발견하시면 이슈를 등록해주세요!

### 기여 방법
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 라이선스

[라이선스 정보 추가 필요]

---

## 🙏 감사의 말

이 프로젝트는 다음 오픈소스 프로젝트들을 사용합니다:
- [LangChain](https://github.com/langchain-ai/langchain)
- [ChromaDB](https://github.com/chroma-core/chroma)
- [OpenAI Whisper](https://openai.com/research/whisper)
- [Google Gemini](https://deepmind.google/technologies/gemini/)
- [Flask](https://flask.palletsprojects.com/)
