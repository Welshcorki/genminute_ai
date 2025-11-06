# GenMinute 설정 가이드

## 환경 변수 설정

### 1. `.env` 파일 생성

프로젝트 루트에 `.env` 파일을 생성하고 `.env.example`을 참고하여 작성하세요.

```bash
cp .env.example .env
```

### 2. Firebase 설정

#### Firebase Console에서 프로젝트 생성:
1. https://console.firebase.google.com/ 접속
2. "프로젝트 추가" 클릭
3. 프로젝트 이름 입력 (예: genminute)

#### Firebase Web App 등록:
1. 프로젝트 설정 → 일반 탭
2. "앱 추가" → 웹 선택
3. 앱 닉네임 입력
4. Firebase SDK 설정 정보 복사

#### `.env` 파일에 추가:
```bash
FIREBASE_API_KEY=your_api_key_here
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_project.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id
FIREBASE_MEASUREMENT_ID=your_measurement_id
```

#### Firebase Admin SDK 설정:
1. Firebase Console → 프로젝트 설정 → 서비스 계정
2. "새 비공개 키 생성" 클릭
3. 다운로드한 JSON 파일을 프로젝트 루트에 `firebase-adminsdk.json`으로 저장

#### Google 로그인 활성화:
1. Firebase Console → Authentication
2. "Sign-in method" 탭
3. Google 제공업체 활성화

#### Authorized Domains 설정:
1. Firebase Console → Authentication → Settings
2. "Authorized domains"에 추가:
   - `localhost` (개발용)
   - 배포 도메인 (프로덕션용)
   - ngrok 도메인 (외부 테스트용)

### 3. 기타 필수 환경 변수

```bash
# Flask
FLASK_SECRET_KEY=generate_with_python_secrets_token_hex_32
ADMIN_EMAILS=your_admin_email@gmail.com

# Google API (STT, Gemini 등)
GOOGLE_API_KEY=your_google_api_key
```

#### Flask Secret Key 생성:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 보안 주의사항

### ⚠️ 절대 GitHub에 올리지 말 것:
- `.env` 파일
- `firebase-adminsdk.json` 파일
- API 키가 포함된 모든 파일

### ✅ `.gitignore` 확인:
다음 항목이 포함되어 있는지 확인:
```
.env
firebase-adminsdk.json
```

### 🔒 Firebase Web API Key에 대하여:

**중요:** Firebase의 Web API Key는 브라우저에서 사용되므로 완전히 숨길 수 없습니다.

**실제 보안은 다음으로 관리됩니다:**
- Firebase Console의 **Authorized Domains** 설정
- Firestore/Storage의 **Security Rules**
- Firebase Authentication 설정

**그럼에도 GitHub에 올리지 않는 이유:**
- 봇 스크래핑 방지
- API 사용량 악용 방지
- 보안 모범 사례 준수

---

## 데이터베이스 마이그레이션

```bash
python migrate_db.py
```

---

## 서버 실행

```bash
python app.py
```

기본 포트: `http://localhost:5050`

---

## 외부 접속 (ngrok)

### 1. ngrok 설치 및 설정
```bash
# ngrok 다운로드: https://ngrok.com/download
# Authtoken 설정
ngrok config add-authtoken YOUR_AUTHTOKEN
```

### 2. 터널 실행
```bash
# 터미널 1: Flask 서버
python app.py

# 터미널 2: ngrok
ngrok http 5050
```

### 3. Firebase Authorized Domains에 ngrok URL 추가
- Firebase Console → Authentication → Settings
- "Authorized domains"에 ngrok 도메인 추가 (예: `abc123.ngrok-free.app`)

---

## 문제 해결

### Firebase 로그인 오류: "auth/unauthorized-domain"
→ Firebase Console → Authentication → Settings → Authorized domains에 도메인 추가

### "no such table: users" 오류
→ `python migrate_db.py` 실행

### Flask Secret Key 오류
→ `.env` 파일에 `FLASK_SECRET_KEY` 추가

---

## 라이선스

MIT License
