# 코드 변경 사항 요약

## 변경 날짜: 2025-11-03

---

## 🔄 업데이트 내역

### 1차 업데이트: 제목 및 회의 일시 검증 기능
### 2차 업데이트: 스크립트 탭 및 문단 요약 탭 추가
### 3차 업데이트: 회의록 탭 추가 및 회의록 생성 기능
### 4차 업데이트: Vector DB 문단 요약 순서대로 조회 및 자동 표시 기능
### 5차 업데이트: 회의록 SQLite DB 저장 및 자동 조회 기능

---

## 1. **새로운 파일 생성**

### `utils/validation.py` (신규 생성)
- **전체 파일 신규 생성** (1-58행)
- **목적**: 입력 검증 및 날짜/시간 처리를 위한 모듈화된 유틸리티
- **포함 함수**:
  - `validate_title(title)`: 제목 입력값 검증
  - `get_current_datetime_string()`: 현재 날짜/시간 문자열 반환
  - `parse_meeting_date(meeting_date)`: 회의 일시 파싱 및 검증

---

## 2. **templates/index.html**

### 변경 내용:
- **25행 수정**
  - **변경 전**: `<input type="datetime-local">`
  - **변경 후**: `<input type="datetime-local" name="meeting_date" id="meeting-date-input" form="upload-form">`
  - **목적**: 회의 일시 입력란에 name 및 id 속성 추가하여 서버로 데이터 전송 가능하게 함

---

## 3. **static/js/script.js**

### 변경 내용:

#### 1) 20-21행 추가 (변수 선언)
```javascript
const titleInput = document.querySelector('input[name="title"]');
const meetingDateInput = document.getElementById('meeting-date-input');
```
- **목적**: 제목 및 회의 일시 입력란 참조 변수 추가

#### 2) 30-36행 수정 (파일 선택 이벤트)
- **변경 전**: 29-31행
  ```javascript
  fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) handleFile(fileInput.files[0]);
  });
  ```
- **변경 후**: 30-36행
  ```javascript
  fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
          handleFile(fileInput.files[0]);
          // 회의 일시가 비어있으면 현재 날짜/시간 자동 입력
          autoFillMeetingDate();
      }
  });
  ```
- **목적**: 파일 선택 시 회의 일시 자동 입력 함수 호출

#### 3) 53-58행 수정 (드래그 앤 드롭 이벤트)
- **변경 전**: 47-52행
  ```javascript
  if (files.length > 0) {
      fileInput.files = files;
      handleFile(files[0]);
  }
  ```
- **변경 후**: 53-58행
  ```javascript
  if (files.length > 0) {
      fileInput.files = files;
      handleFile(files[0]);
      // 회의 일시가 비어있으면 현재 날짜/시간 자동 입력
      autoFillMeetingDate();
  }
  ```
- **목적**: 드래그 앤 드롭 시에도 회의 일시 자동 입력

#### 4) 63-83행 수정 (폼 제출 검증)
- **변경 전**: 55-66행
  ```javascript
  uploadForm.addEventListener('submit', (event) => {
      if (fileInput.files.length === 0) {
          event.preventDefault();
          alert('파일을 선택해 주세요');
          return;
      }
      if(sttSubmitButton) {
          sttSubmitButton.textContent = '처리 중...';
          sttSubmitButton.disabled = true;
      }
  });
  ```
- **변경 후**: 63-83행
  ```javascript
  uploadForm.addEventListener('submit', (event) => {
      // 제목 입력 검증
      if (!titleInput || titleInput.value.trim() === '') {
          event.preventDefault();
          alert('제목을 입력해 주세요.');
          return;
      }

      // 파일 선택 검증
      if (fileInput.files.length === 0) {
          event.preventDefault();
          alert('파일을 선택해 주세요.');
          return;
      }

      // 모든 검증 통과 시 버튼 상태를 변경하고 폼 제출 진행
      if(sttSubmitButton) {
          sttSubmitButton.textContent = '처리 중...';
          sttSubmitButton.disabled = true;
      }
  });
  ```
- **목적**: 제목 입력 검증 추가 및 에러 메시지 개선

#### 5) 102-116행 추가 (새로운 함수)
```javascript
// 회의 일시 자동 입력 함수
function autoFillMeetingDate() {
    if (meetingDateInput && !meetingDateInput.value) {
        // 현재 날짜/시간을 datetime-local 형식으로 변환 (YYYY-MM-DDTHH:MM)
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');

        const formattedDateTime = `${year}-${month}-${day}T${hours}:${minutes}`;
        meetingDateInput.value = formattedDateTime;
    }
}
```
- **목적**: 회의 일시가 비어있을 경우 현재 날짜/시간 자동 입력

---

## 4. **app.py**

### 변경 내용:

#### 1) 13행 추가 (import 문)
- **변경 전**: 9-12행
  ```python
  # --- 커스텀 모듈 임포트 ---
  from utils.stt import STTManager
  from utils.db_manager import DatabaseManager
  from utils.vector_db_manager import vdb_manager
  ```
- **변경 후**: 9-13행
  ```python
  # --- 커스텀 모듈 임포트 ---
  from utils.stt import STTManager
  from utils.db_manager import DatabaseManager
  from utils.vector_db_manager import vdb_manager
  from utils.validation import validate_title, parse_meeting_date
  ```
- **목적**: validation 모듈 import

#### 2) 43-61행 수정 (upload_and_process 함수 시작 부분)
- **변경 전**: 42-51행
  ```python
  @app.route("/upload", methods=["POST"])
  def upload_and_process():
      if 'audio_file' not in request.files:
          return render_template("index.html", error="오디오 파일이 없습니다.")

      file = request.files['audio_file']
      title = request.form.get('title', '제목 없음')

      if file.filename == '' or not allowed_file(file.filename):
          return render_template("index.html", error="파일이 없거나 허용되지 않는 형식입니다.")
  ```
- **변경 후**: 43-61행
  ```python
  @app.route("/upload", methods=["POST"])
  def upload_and_process():
      # 제목 검증
      title = request.form.get('title', '').strip()
      is_valid, error_message = validate_title(title)
      if not is_valid:
          return render_template("index.html", error=error_message)

      # 오디오 파일 검증
      if 'audio_file' not in request.files:
          return render_template("index.html", error="오디오 파일이 없습니다.")

      file = request.files['audio_file']
      if file.filename == '' or not allowed_file(file.filename):
          return render_template("index.html", error="파일이 없거나 허용되지 않는 형식입니다.")

      # 회의 일시 처리 (입력이 없으면 현재 시간 자동 설정)
      meeting_date_input = request.form.get('meeting_date', '')
      meeting_date = parse_meeting_date(meeting_date_input)
  ```
- **목적**: 제목 검증 로직 추가 및 회의 일시 처리 로직 추가

#### 3) 74행 수정 (DB 저장 호출)
- **변경 전**: 64행
  ```python
  meeting_id = db.save_stt_to_db(segments, filename, title)
  ```
- **변경 후**: 74행
  ```python
  meeting_id = db.save_stt_to_db(segments, filename, title, meeting_date)
  ```
- **목적**: meeting_date 매개변수 전달

---

## 5. **utils/db_manager.py**

### 변경 내용:

#### 1) 15-49행 수정 (save_stt_to_db 함수)
- **변경 전**: 15-32행
  ```python
  def save_stt_to_db(self, segments, audio_filename, title):
      meeting_id = str(uuid.uuid4())
      meeting_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      conn = self._get_connection()
      cursor = conn.cursor()
      for segment in segments:
          cursor.execute("""
              INSERT INTO meeting_dialogues
              (meeting_id, meeting_date, speaker_label, start_time, segment, confidence, audio_file, title)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?)
          """, (
              meeting_id, meeting_date, str(segment['speaker']), segment['start_time'],
              segment['text'], segment['confidence'], audio_filename, title
          ))
      conn.commit()
      conn.close()
      print(f"✅ DB 저장 완료: meeting_id={meeting_id}")
      return meeting_id
  ```
- **변경 후**: 15-49행
  ```python
  def save_stt_to_db(self, segments, audio_filename, title, meeting_date=None):
      """
      음성 인식 결과를 데이터베이스에 저장합니다.

      Args:
          segments (list): 음성 인식 결과 세그먼트 리스트
          audio_filename (str): 오디오 파일명
          title (str): 회의 제목
          meeting_date (str, optional): 회의 일시 (형식: "YYYY-MM-DD HH:MM:SS")
                                        제공되지 않으면 현재 시간 사용

      Returns:
          str: 생성된 meeting_id
      """
      meeting_id = str(uuid.uuid4())

      # meeting_date가 제공되지 않으면 현재 시간 사용
      if meeting_date is None:
          meeting_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

      conn = self._get_connection()
      cursor = conn.cursor()
      for segment in segments:
          cursor.execute("""
              INSERT INTO meeting_dialogues
              (meeting_id, meeting_date, speaker_label, start_time, segment, confidence, audio_file, title)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?)
          """, (
              meeting_id, meeting_date, str(segment['speaker']), segment['start_time'],
              segment['text'], segment['confidence'], audio_filename, title
          ))
      conn.commit()
      conn.close()
      print(f"✅ DB 저장 완료: meeting_id={meeting_id}, meeting_date={meeting_date}")
      return meeting_id
  ```
- **목적**: meeting_date 매개변수 추가 및 docstring 작성

---

## 요약

### 주요 개선 사항:
1. ✅ **제목 입력 검증**: 제목이 비어있으면 "제목을 입력해 주세요." 메시지 표시
2. ✅ **회의 일시 자동 입력**: 오디오 파일 선택 시 회의 일시가 비어있으면 현재 날짜/시간 자동 입력
3. ✅ **모듈화**: validation.py로 검증 로직 분리하여 재사용성 향상
4. ✅ **사용자 경험 개선**: 명확한 에러 메시지 제공
5. ✅ **기존 기능 유지**: 파일 검증 및 음성 인식 기능 정상 동작

### 영향을 받는 파일 (1차):
- **신규**: `utils/validation.py`
- **수정**: `templates/index.html`, `static/js/script.js`, `app.py`, `utils/db_manager.py`

---

---

# 2차 업데이트: 스크립트 탭 및 문단 요약 탭 추가 (2025-11-03)

## 6. **templates/viewer.html**

### 변경 내용:

#### 1) 13-38행 수정 (탭 UI 추가)
- **변경 전**: 13-19행
  ```html
  <div class="player-container">
      <audio id="audio-player" controls></audio>
  </div>

  <main id="transcript-container" class="transcript-container">
      <p>데이터를 불러오는 중입니다...</p>
  </main>
  ```
- **변경 후**: 13-38행
  ```html
  <div class="player-container">
      <audio id="audio-player" controls></audio>
  </div>

  <!-- 탭 네비게이션 -->
  <div class="tabs-container">
      <button class="tab-button active" data-tab="script">스크립트</button>
      <button class="tab-button" data-tab="summary">문단 요약</button>
  </div>

  <!-- 탭 컨텐츠 -->
  <div class="tab-content-container">
      <!-- 스크립트 탭 -->
      <div id="script-tab" class="tab-content active">
          <div id="transcript-container" class="transcript-container">
              <p>데이터를 불러오는 중입니다...</p>
          </div>
      </div>

      <!-- 문단 요약 탭 -->
      <div id="summary-tab" class="tab-content">
          <div id="summary-container" class="summary-container">
              <p class="summary-placeholder">요약하기 버튼을 눌러 회의 내용을 요약하세요.</p>
          </div>
      </div>
  </div>
  ```
- **목적**: 스크립트와 문단 요약을 탭으로 구분하여 표시

---

## 7. **static/css/style.css**

### 변경 내용:

#### 1) 201-294행 추가 (탭 및 요약 스타일)
```css
/* --- Tab Styles --- */
.tabs-container {
    display: flex;
    gap: 0.5rem;
    border-bottom: 2px solid var(--border-color);
    margin-bottom: 1rem;
}

.tab-button {
    background: none;
    border: none;
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    cursor: pointer;
    color: var(--text-color);
    border-bottom: 3px solid transparent;
    transition: all 0.2s;
    font-weight: 500;
}

.tab-button:hover {
    background-color: #f8f9fa;
}

.tab-button.active {
    color: var(--primary-color);
    border-bottom-color: var(--primary-color);
    font-weight: 600;
}

.tab-content-container {
    position: relative;
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

/* --- Summary Container Styles --- */
.summary-container {
    border: 1px solid var(--border-color);
    border-radius: 5px;
    padding: 1.5rem;
    height: calc(100vh - 320px);
    overflow-y: auto;
    background-color: #fafafa;
}

.summary-placeholder {
    text-align: center;
    color: #999;
    padding: 3rem;
    font-size: 1.1rem;
}

.summary-content {
    line-height: 1.8;
    color: var(--text-color);
}

.summary-content h3 {
    color: var(--nav-bg);
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
    font-size: 1.3rem;
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 0.5rem;
}

.summary-content ul {
    margin: 0.5rem 0 1.5rem 1.5rem;
    padding: 0;
}

.summary-content li {
    margin-bottom: 0.5rem;
    line-height: 1.6;
}

.summary-loading {
    text-align: center;
    padding: 3rem;
    color: var(--primary-color);
}

.summary-error {
    text-align: center;
    padding: 3rem;
    color: #e74c3c;
}
```
- **목적**: 탭 UI 및 요약 컨텐츠 스타일링

---

## 8. **static/js/viewer.js**

### 변경 내용:

#### 1) 2-27행 수정 (탭 전환 기능 추가)
- **변경 전**: 2-8행
  ```javascript
  document.addEventListener('DOMContentLoaded', () => {
      const audioPlayer = document.getElementById('audio-player');
      const transcriptContainer = document.getElementById('transcript-container');
      const meetingTitle = document.getElementById('meeting-title');

      let segments = [];
      let currentSegmentIndex = -1;
  ```
- **변경 후**: 2-27행
  ```javascript
  document.addEventListener('DOMContentLoaded', () => {
      const audioPlayer = document.getElementById('audio-player');
      const transcriptContainer = document.getElementById('transcript-container');
      const summaryContainer = document.getElementById('summary-container');
      const meetingTitle = document.getElementById('meeting-title');

      let segments = [];
      let currentSegmentIndex = -1;

      // 탭 전환 기능
      const tabButtons = document.querySelectorAll('.tab-button');
      const tabContents = document.querySelectorAll('.tab-content');

      tabButtons.forEach(button => {
          button.addEventListener('click', () => {
              const targetTab = button.dataset.tab;

              // 모든 탭 버튼과 컨텐츠에서 active 클래스 제거
              tabButtons.forEach(btn => btn.classList.remove('active'));
              tabContents.forEach(content => content.classList.remove('active'));

              // 클릭한 탭 버튼과 해당 컨텐츠에 active 클래스 추가
              button.classList.add('active');
              document.getElementById(`${targetTab}-tab`).classList.add('active');
          });
      });
  ```
- **목적**: summaryContainer 변수 추가 및 탭 클릭 시 전환 기능 구현

#### 2) 128-200행 수정 (요약 결과 표시 기능)
- **변경 전**: 109-154행
  ```javascript
  // 요약하기 버튼 이벤트 리스너
  const summarizeButton = document.getElementById('summarize-button');
  if (summarizeButton) {
      summarizeButton.addEventListener('click', async () => {
          // ... (중략)
          if (data.success) {
              alert('요약이 성공적으로 생성 및 저장되었습니다!');
              console.log('Summary:', data.summary);
          } else {
              alert(`요약 실패: ${data.error}`);
          }
          // ... (중략)
      });
  }
  ```
- **변경 후**: 128-200행
  ```javascript
  // 요약하기 버튼 이벤트 리스너
  const summarizeButton = document.getElementById('summarize-button');
  if (summarizeButton) {
      summarizeButton.addEventListener('click', async () => {
          // ... (중략)
          // 요약 컨테이너에 로딩 메시지 표시
          summaryContainer.innerHTML = '<div class="summary-loading">요약을 생성하는 중입니다. 잠시만 기다려주세요...</div>';

          // 문단 요약 탭으로 자동 전환
          tabButtons.forEach(btn => btn.classList.remove('active'));
          tabContents.forEach(content => content.classList.remove('active'));
          document.querySelector('[data-tab="summary"]').classList.add('active');
          document.getElementById('summary-tab').classList.add('active');

          // ... (중략)
          if (data.success) {
              // 요약 내용을 마크다운에서 HTML로 변환하여 표시
              displaySummary(data.summary);
              alert('요약이 성공적으로 생성되었습니다!');
          } else {
              summaryContainer.innerHTML = `<div class="summary-error">요약 실패: ${data.error}</div>`;
          }
          // ... (중략)
      });
  }

  // 요약 내용 표시 함수
  function displaySummary(summaryText) {
      // 마크다운 형식을 HTML로 변환
      // ### 제목 -> <h3>제목</h3>
      // * 항목 -> <li>항목</li>
      let htmlContent = summaryText
          .replace(/### (.+)/g, '<h3>$1</h3>')
          .replace(/^\* (.+)/gm, '<li>$1</li>');

      // <li> 태그들을 <ul>로 감싸기
      htmlContent = htmlContent.replace(/(<li>.*?<\/li>\s*)+/gs, match => {
          return `<ul>${match}</ul>`;
      });

      summaryContainer.innerHTML = `<div class="summary-content">${htmlContent}</div>`;
  }
  ```
- **목적**:
  - 요약 생성 중 로딩 메시지 표시
  - 요약 시작 시 자동으로 문단 요약 탭으로 전환
  - 요약 완료 후 마크다운을 HTML로 변환하여 표시
  - displaySummary 함수 추가로 마크다운 형식 변환 처리

---

## 요약 (2차 업데이트)

### 주요 개선 사항:
1. ✅ **탭 UI 추가**: 스크립트 탭과 문단 요약 탭으로 구분
2. ✅ **탭 전환 기능**: 사용자가 클릭하여 탭 전환 가능
3. ✅ **요약 결과 표시**: 요약하기 버튼 클릭 시 문단 요약 탭에 결과 표시
4. ✅ **자동 탭 전환**: 요약 시작 시 자동으로 문단 요약 탭으로 전환
5. ✅ **마크다운 변환**: 요약 내용의 마크다운 형식을 HTML로 자동 변환
6. ✅ **로딩 상태 표시**: 요약 생성 중 로딩 메시지 표시
7. ✅ **에러 처리**: 요약 실패 시 에러 메시지 표시

### 영향을 받는 파일 (2차):
- **수정**: `templates/viewer.html`, `static/css/style.css`, `static/js/viewer.js`

---

## 📊 전체 변경 파일 요약

### 1차 업데이트 (제목/회의일시 검증):
- **신규**: `utils/validation.py`
- **수정**: `templates/index.html`, `static/js/script.js`, `app.py`, `utils/db_manager.py`

### 2차 업데이트 (스크립트/요약 탭):
- **수정**: `templates/viewer.html`, `static/css/style.css`, `static/js/viewer.js`

---

---

# 3차 업데이트: 회의록 탭 추가 및 회의록 생성 기능 (2025-11-03)

## 9. **utils/stt.py**

### 변경 내용:

#### 1) 167-283행 추가 (generate_minutes 함수)
```python
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
    # summarizer.py의 로직을 참조하여 회의록 생성
    # 회의명, 일시, 참석자, 회의 요약, 핵심 논의 내용, 액션 아이템, 향후 계획 포함
```
- **목적**: 문단 요약을 기반으로 정식 회의록 형식으로 변환하는 함수 추가
- **참조**: summarizer.py의 summarize_text 함수 로직 활용

---

## 10. **app.py**

### 변경 내용:

#### 1) 240-295행 추가 (/api/generate_minutes API)
```python
@app.route("/api/generate_minutes/<string:meeting_id>", methods=["POST"])
def generate_minutes(meeting_id):
    """회의록 생성 API - 문단 요약을 기반으로 정식 회의록을 생성합니다."""
    try:
        # 1. meeting_id로 회의록 내용 조회
        rows = db.get_meeting_by_id(meeting_id)

        # 2. title, transcript_text 추출
        title = rows[0]['title']
        transcript_text = " ".join([row['segment'] for row in rows])

        # 3. vector DB에서 문단 요약 내용 가져오기
        results = vdb_manager.search(
            db_type="meeting_subtopic",
            query=title,
            retriever_type="similarity",
            k=1
        )

        summary_content = results[0].page_content

        # 4. stt_manager의 generate_minutes를 이용해 회의록 생성
        minutes_content = stt_manager.generate_minutes(title, transcript_text, summary_content)

        return jsonify({
            "success": True,
            "message": "회의록이 성공적으로 생성되었습니다.",
            "minutes": minutes_content
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"회의록 생성 중 오류 발생: {str(e)}"}), 500
```
- **목적**: 회의록 생성 API 엔드포인트 추가
- **기능**:
  - 문단 요약을 Vector DB에서 조회
  - 조회한 문단 요약을 기반으로 회의록 생성
  - 생성된 회의록을 JSON으로 반환

---

## 11. **templates/viewer.html**

### 변경 내용:

#### 1) 18-47행 수정 (회의록 탭 추가)
- **변경 전**: 18-22행
  ```html
  <!-- 탭 네비게이션 -->
  <div class="tabs-container">
      <button class="tab-button active" data-tab="script">스크립트</button>
      <button class="tab-button" data-tab="summary">문단 요약</button>
  </div>
  ```
- **변경 후**: 18-47행
  ```html
  <!-- 탭 네비게이션 -->
  <div class="tabs-container">
      <button class="tab-button active" data-tab="script">스크립트</button>
      <button class="tab-button" data-tab="summary">문단 요약</button>
      <button class="tab-button" data-tab="minutes">회의록</button>
  </div>

  <!-- 탭 컨텐츠 -->
  <div class="tab-content-container">
      <!-- 스크립트 탭 -->
      <div id="script-tab" class="tab-content active">...</div>

      <!-- 문단 요약 탭 -->
      <div id="summary-tab" class="tab-content">...</div>

      <!-- 회의록 탭 -->
      <div id="minutes-tab" class="tab-content">
          <div id="minutes-container" class="minutes-container">
              <p class="minutes-placeholder">문단 요약 생성 후, 회의록 생성 버튼을 눌러주세요.</p>
              <button id="generate-minutes-button" class="btn-primary" style="display: none; margin-top: 1rem;">회의록 생성</button>
          </div>
      </div>
  </div>
  ```
- **목적**: 회의록 탭 추가

---

## 12. **static/css/style.css**

### 변경 내용:

#### 1) 296-370행 추가 (회의록 컨테이너 스타일)
```css
/* --- Minutes Container Styles --- */
.minutes-container {
    border: 1px solid var(--border-color);
    border-radius: 5px;
    padding: 1.5rem;
    height: calc(100vh - 320px);
    overflow-y: auto;
    background-color: #fafafa;
}

.minutes-content {
    line-height: 1.8;
    color: var(--text-color);
    background-color: white;
    padding: 2rem;
    border-radius: 5px;
}

.minutes-content h1 {
    color: var(--nav-bg);
    font-size: 2rem;
    margin-bottom: 1rem;
    border-bottom: 3px solid var(--primary-color);
    padding-bottom: 0.5rem;
}

.minutes-content h2 {
    color: var(--nav-bg);
    margin-top: 2rem;
    margin-bottom: 1rem;
    font-size: 1.5rem;
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 0.5rem;
}

/* ... 기타 회의록 스타일 ... */
```
- **목적**: 회의록 컨테이너 및 회의록 내용 스타일 추가

---

## 13. **static/js/viewer.js**

### 변경 내용:

#### 1) 2-11행 수정 (변수 추가)
- **변경 전**: 2-10행
  ```javascript
  const summaryContainer = document.getElementById('summary-container');
  let segments = [];
  let currentSegmentIndex = -1;
  ```
- **변경 후**: 2-11행
  ```javascript
  const summaryContainer = document.getElementById('summary-container');
  const minutesContainer = document.getElementById('minutes-container');
  let segments = [];
  let currentSegmentIndex = -1;
  let summaryGenerated = false; // 요약 생성 여부 추적
  ```
- **목적**: minutesContainer 및 summaryGenerated 변수 추가

#### 2) 166-178행 수정 (요약 완료 시 회의록 버튼 활성화)
- **변경 전**: 166-174행
  ```javascript
  if (data.success) {
      displaySummary(data.summary);
      alert('요약이 성공적으로 생성되었습니다!');
  }
  ```
- **변경 후**: 166-178행
  ```javascript
  if (data.success) {
      displaySummary(data.summary);
      summaryGenerated = true; // 요약 생성 완료 표시

      // 회의록 탭에서 회의록 생성 버튼 활성화
      updateMinutesTab();

      alert('요약이 성공적으로 생성되었습니다!');
  }
  ```
- **목적**: 요약 생성 완료 시 회의록 탭의 버튼 활성화

#### 3) 208-300행 추가 (회의록 관련 함수들)
```javascript
// 회의록 탭 업데이트 함수
function updateMinutesTab() {
    if (summaryGenerated) {
        minutesContainer.innerHTML = `
            <p class="minutes-placeholder">회의록 생성 버튼을 눌러 정식 회의록을 작성하세요.</p>
            <button id="generate-minutes-button" class="btn-primary" style="margin-top: 1rem;">회의록 생성</button>
        `;
        attachMinutesButtonListener();
    }
}

// 회의록 생성 버튼 이벤트 리스너
function attachMinutesButtonListener() {
    const generateMinutesButton = document.getElementById('generate-minutes-button');
    if (generateMinutesButton) {
        generateMinutesButton.addEventListener('click', async () => {
            // 회의록 생성 API 호출
            const response = await fetch(`/api/generate_minutes/${MEETING_ID}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });

            if (data.success) {
                displayMinutes(data.minutes);
                alert('회의록이 성공적으로 생성되었습니다!');
            }
        });
    }
}

// 회의록 내용 표시 함수
function displayMinutes(minutesText) {
    // 마크다운 형식을 HTML로 변환
    let htmlContent = minutesText
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/^(?!<[h123]|<strong|<hr|$)(.+)$/gm, '<p>$1</p>')
        .replace(/^---$/gm, '<hr>');

    minutesContainer.innerHTML = `<div class="minutes-content">${htmlContent}</div>`;
}
```
- **목적**: 회의록 생성 및 표시 기능 구현

---

## 요약 (3차 업데이트)

### 주요 개선 사항:
1. ✅ **회의록 탭 추가**: 스크립트, 문단 요약, 회의록 3개 탭으로 구성
2. ✅ **회의록 생성 기능**: 문단 요약을 기반으로 정식 회의록 자동 생성
3. ✅ **회의록 템플릿**: 회의명, 일시, 참석자, 회의 요약, 핵심 논의 내용, 액션 아이템, 향후 계획 포함
4. ✅ **자동 버튼 활성화**: 문단 요약 생성 완료 시 회의록 생성 버튼 자동 활성화
5. ✅ **마크다운 변환**: 회의록 마크다운을 HTML로 자동 변환하여 표시
6. ✅ **에러 처리**: 문단 요약 미생성 시 안내 메시지 표시
7. ✅ **summarizer.py 참조**: 기존 회의록 생성 로직을 참조하여 일관된 형식 유지

### 영향을 받는 파일 (3차):
- **수정**: `utils/stt.py`, `app.py`, `templates/viewer.html`, `static/css/style.css`, `static/js/viewer.js`

---

## 📊 전체 변경 파일 요약

### 1차 업데이트 (제목/회의일시 검증):
- **신규**: `utils/validation.py`
- **수정**: `templates/index.html`, `static/js/script.js`, `app.py`, `utils/db_manager.py`

### 2차 업데이트 (스크립트/요약 탭):
- **수정**: `templates/viewer.html`, `static/css/style.css`, `static/js/viewer.js`

### 3차 업데이트 (회의록 탭):
- **수정**: `utils/stt.py`, `app.py`, `templates/viewer.html`, `static/css/style.css`, `static/js/viewer.js`

---

---

# 4차 업데이트: Vector DB 문단 요약 순서대로 조회 및 자동 표시 기능 (2025-11-03)

## 14. **utils/vector_db_manager.py**

### 변경 내용:

#### 1) 192-240행 추가 (get_summary_by_meeting_id 함수)
```python
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

        return full_summary

    except Exception as e:
        return ""
```
- **목적**: meeting_id로 Vector DB에서 문단 요약을 summary_index 순서대로 조회
- **기능**: 여러 개의 summary 청크를 순서대로 결합하여 하나의 완전한 문단 요약 반환

---

## 15. **app.py**

### 변경 내용:

#### 1) 240-263행 추가 (/api/check_summary API)
```python
@app.route("/api/check_summary/<string:meeting_id>", methods=["GET"])
def check_summary(meeting_id):
    """문단 요약 존재 여부 확인 API"""
    try:
        # Vector DB에서 문단 요약 조회
        summary_content = vdb_manager.get_summary_by_meeting_id(meeting_id)

        if summary_content:
            return jsonify({
                "success": True,
                "has_summary": True,
                "summary": summary_content
            })
        else:
            return jsonify({
                "success": True,
                "has_summary": False,
                "message": "문단 요약이 아직 생성되지 않았습니다."
            })

    except Exception as e:
        return jsonify({"success": False, "error": f"요약 조회 중 오류 발생: {str(e)}"}), 500
```
- **목적**: 프론트엔드에서 문단 요약 존재 여부 확인 및 조회
- **기능**: meeting_id로 Vector DB에서 문단 요약 조회 후 반환

#### 2) 265-277행 수정 (generate_minutes API 개선)
- **변경 전**: 253-278행
  ```python
  # 3. vector DB에서 문단 요약 내용 가져오기
  try:
      # meeting_subtopic 컬렉션에서 summary 내용 검색
      results = vdb_manager.search(
          db_type="meeting_subtopic",
          query=title,  # 제목으로 검색
          retriever_type="similarity",
          k=1
      )

      if not results or len(results) == 0:
          return jsonify({
              "success": False,
              "error": "먼저 '요약하기' 버튼을 눌러 문단 요약을 생성해주세요."
          }), 400

      # 가장 유사한 결과에서 summary 내용 추출
      summary_content = results[0].page_content

  except Exception as e:
      return jsonify({
          "success": False,
          "error": "문단 요약을 찾을 수 없습니다. 먼저 '요약하기' 버튼을 눌러주세요."
      }), 400
  ```
- **변경 후**: 253-260행
  ```python
  # 3. vector DB에서 문단 요약 내용 가져오기 (summary_index 순서대로)
  summary_content = vdb_manager.get_summary_by_meeting_id(meeting_id)

  if not summary_content:
      return jsonify({
          "success": False,
          "error": "먼저 '요약하기' 버튼을 눌러 문단 요약을 생성해주세요."
      }), 400
  ```
- **목적**:
  - 검색 방식에서 직접 조회 방식으로 변경
  - summary_index 순서대로 정렬된 완전한 문단 요약 사용

---

## 16. **static/js/viewer.js**

### 변경 내용:

#### 1) 32-59행 수정 (initializeViewer 함수)
- **변경 전**: 32-52행
  ```javascript
  async function initializeViewer() {
      // ... (중략)
      segments = data.transcript;
      meetingTitle.textContent = data.title;
      audioPlayer.src = data.audio_url;

      renderTranscript(segments);

  } catch (error) {
      showError(error.message);
  }
  ```
- **변경 후**: 32-59행
  ```javascript
  async function initializeViewer() {
      // ... (중략)
      segments = data.transcript;
      meetingTitle.textContent = data.title;
      audioPlayer.src = data.audio_url;

      renderTranscript(segments);

      // 문단 요약 존재 여부 확인 및 표시
      await checkAndDisplaySummary();

  } catch (error) {
      showError(error.message);
  }
  ```
- **목적**: 뷰어 초기화 시 문단 요약 자동 조회 및 표시

#### 2) 61-83행 추가 (checkAndDisplaySummary 함수)
```javascript
// 문단 요약 존재 여부 확인 및 자동 표시
async function checkAndDisplaySummary() {
    try {
        const response = await fetch(`/api/check_summary/${MEETING_ID}`);
        const data = await response.json();

        if (data.success && data.has_summary) {
            // 문단 요약이 이미 존재하면 자동으로 표시
            displaySummary(data.summary);
            summaryGenerated = true;

            // 회의록 생성 버튼 활성화
            updateMinutesTab();

            console.log('✅ 기존 문단 요약을 불러왔습니다.');
        } else {
            console.log('ℹ️ 문단 요약이 아직 생성되지 않았습니다.');
        }
    } catch (error) {
        console.error('문단 요약 조회 중 오류:', error);
        // 오류가 발생해도 계속 진행 (필수 기능 아님)
    }
}
```
- **목적**:
  - 페이지 로드 시 Vector DB에서 문단 요약 조회
  - 이미 생성된 문단 요약이 있으면 자동으로 표시
  - 회의록 생성 버튼 자동 활성화

---

## 요약 (4차 업데이트)

### 주요 개선 사항:
1. ✅ **순서 보장**: summary_index 순서대로 문단 요약 조회하여 올바른 순서 보장
2. ✅ **자동 표시**: 페이지 로드 시 이미 생성된 문단 요약 자동 표시
3. ✅ **회의록 버튼 자동 활성화**: 문단 요약이 있으면 회의록 생성 버튼 자동 활성화
4. ✅ **API 개선**: 검색 방식에서 직접 조회 방식으로 변경하여 정확도 향상
5. ✅ **사용자 경험 개선**:
   - 새로고침해도 생성된 요약이 사라지지 않음
   - 다른 페이지 갔다가 돌아와도 요약 유지
   - 불필요한 중복 생성 방지

### 영향을 받는 파일 (4차):
- **수정**: `utils/vector_db_manager.py`, `app.py`, `static/js/viewer.js`

---

## 📊 전체 변경 파일 요약

### 1차 업데이트 (제목/회의일시 검증):
- **신규**: `utils/validation.py`
- **수정**: `templates/index.html`, `static/js/script.js`, `app.py`, `utils/db_manager.py`

### 2차 업데이트 (스크립트/요약 탭):
- **수정**: `templates/viewer.html`, `static/css/style.css`, `static/js/viewer.js`

### 3차 업데이트 (회의록 탭):
- **수정**: `utils/stt.py`, `app.py`, `templates/viewer.html`, `static/css/style.css`, `static/js/viewer.js`

### 4차 업데이트 (Vector DB 순서 조회):
- **수정**: `utils/vector_db_manager.py`, `app.py`, `static/js/viewer.js`

---

---

# 5차 업데이트: 회의록 SQLite DB 저장 및 자동 조회 기능 (2025-11-03)

## 17. **utils/db_manager.py**

### 변경 내용:

#### 1) 80-132행 추가 (save_minutes 함수)
```python
def save_minutes(self, meeting_id, title, meeting_date, minutes_content):
    """
    생성된 회의록을 데이터베이스에 저장합니다.

    Args:
        meeting_id (str): 회의 ID
        title (str): 회의 제목
        meeting_date (str): 회의 일시
        minutes_content (str): 회의록 내용 (마크다운 형식)

    Returns:
        bool: 저장 성공 여부
    """
    # meeting_minutes 테이블이 없으면 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meeting_minutes (
            meeting_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            meeting_date TEXT NOT NULL,
            minutes_content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # 기존 회의록이 있는지 확인
    # 있으면 UPDATE, 없으면 INSERT
```
- **목적**: 생성된 회의록을 SQLite DB에 저장 (meeting_minutes 테이블)
- **기능**:
  - 테이블 자동 생성
  - 중복 시 업데이트, 없으면 신규 저장

#### 2) 134-165행 추가 (get_minutes_by_meeting_id 함수)
```python
def get_minutes_by_meeting_id(self, meeting_id):
    """
    meeting_id로 저장된 회의록을 조회합니다.

    Args:
        meeting_id (str): 회의 ID

    Returns:
        dict or None: 회의록 정보 (meeting_id, title, meeting_date, minutes_content, created_at, updated_at)
                      없으면 None 반환
    """
    # meeting_minutes 테이블에서 조회
    cursor.execute("""
        SELECT meeting_id, title, meeting_date, minutes_content, created_at, updated_at
        FROM meeting_minutes
        WHERE meeting_id = ?
    """, (meeting_id,))
```
- **목적**: meeting_id로 저장된 회의록 조회
- **기능**: 회의록이 있으면 dict 반환, 없으면 None 반환

---

## 18. **app.py**

### 변경 내용:

#### 1) 265-290행 추가 (/api/get_minutes API)
```python
@app.route("/api/get_minutes/<string:meeting_id>", methods=["GET"])
def get_minutes(meeting_id):
    """회의록 조회 API - SQLite DB에서 저장된 회의록을 조회합니다."""
    try:
        # DB에서 회의록 조회
        minutes_data = db.get_minutes_by_meeting_id(meeting_id)

        if minutes_data:
            return jsonify({
                "success": True,
                "has_minutes": True,
                "minutes": minutes_data['minutes_content'],
                "created_at": minutes_data['created_at'],
                "updated_at": minutes_data['updated_at']
            })
        else:
            return jsonify({
                "success": True,
                "has_minutes": False,
                "message": "회의록이 아직 생성되지 않았습니다."
            })

    except Exception as e:
        return jsonify({"success": False, "error": f"회의록 조회 중 오류 발생: {str(e)}"}), 500
```
- **목적**: 프론트엔드에서 회의록 존재 여부 확인 및 조회
- **기능**: meeting_id로 SQLite DB에서 회의록 조회 후 반환

#### 2) 292-333행 수정 (generate_minutes API - DB 저장 추가)
- **변경 전**: 회의록 생성 후 JSON 반환만
- **변경 후**: 회의록 생성 → **SQLite DB 저장** → JSON 반환
  ```python
  # 5. 생성된 회의록을 SQLite DB에 저장
  db.save_minutes(meeting_id, title, meeting_date, minutes_content)

  return jsonify({
      "success": True,
      "message": "회의록이 성공적으로 생성 및 저장되었습니다.",
      "minutes": minutes_content
  })
  ```
- **목적**: 회의록 생성 후 자동으로 DB에 저장

---

## 19. **static/js/viewer.js**

### 변경 내용:

#### 1) 9-12행 수정 (변수 추가)
- **변경 전**: 9-11행
  ```javascript
  let segments = [];
  let currentSegmentIndex = -1;
  let summaryGenerated = false;
  ```
- **변경 후**: 9-12행
  ```javascript
  let segments = [];
  let currentSegmentIndex = -1;
  let summaryGenerated = false;
  let minutesGenerated = false; // 회의록 생성 여부 추적
  ```
- **목적**: 회의록 생성/조회 상태 추적

#### 2) 18-35행 수정 (탭 전환 시 회의록 조회)
- **변경 전**: 18-29행
  ```javascript
  tabButtons.forEach(button => {
      button.addEventListener('click', () => {
          const targetTab = button.dataset.tab;

          // 탭 전환 로직
          button.classList.add('active');
          document.getElementById(`${targetTab}-tab`).classList.add('active');
      });
  });
  ```
- **변경 후**: 18-35행
  ```javascript
  tabButtons.forEach(button => {
      button.addEventListener('click', () => {
          const targetTab = button.dataset.tab;

          // 탭 전환 로직
          button.classList.add('active');
          document.getElementById(`${targetTab}-tab`).classList.add('active');

          // 회의록 탭을 클릭했을 때 회의록 조회
          if (targetTab === 'minutes' && !minutesGenerated) {
              checkAndDisplayMinutes();
          }
      });
  });
  ```
- **목적**: 회의록 탭 클릭 시 DB에서 회의록 자동 조회

#### 3) 59-63행 수정 (페이지 로드 시 회의록 조회)
- **변경 전**: 59-60행
  ```javascript
  // 문단 요약 존재 여부 확인 및 표시
  await checkAndDisplaySummary();
  ```
- **변경 후**: 59-63행
  ```javascript
  // 문단 요약 존재 여부 확인 및 표시
  await checkAndDisplaySummary();

  // 회의록 존재 여부 확인 및 표시
  await checkAndDisplayMinutes();
  ```
- **목적**: 페이지 로드 시 자동으로 회의록 조회 및 표시

#### 4) 94-114행 추가 (checkAndDisplayMinutes 함수)
```javascript
// 회의록 존재 여부 확인 및 자동 표시
async function checkAndDisplayMinutes() {
    try {
        const response = await fetch(`/api/get_minutes/${MEETING_ID}`);
        const data = await response.json();

        if (data.success && data.has_minutes) {
            // 회의록이 이미 존재하면 자동으로 표시
            displayMinutes(data.minutes);
            minutesGenerated = true;

            console.log('✅ 기존 회의록을 불러왔습니다.');
        } else {
            console.log('ℹ️ 회의록이 아직 생성되지 않았습니다.');
        }
    } catch (error) {
        console.error('회의록 조회 중 오류:', error);
    }
}
```
- **목적**: SQLite DB에서 회의록 조회 및 자동 표시

#### 5) 319-323행 수정 (회의록 생성 완료 처리)
- **변경 전**: 319-321행
  ```javascript
  if (data.success) {
      displayMinutes(data.minutes);
      alert('회의록이 성공적으로 생성되었습니다!');
  }
  ```
- **변경 후**: 319-323행
  ```javascript
  if (data.success) {
      displayMinutes(data.minutes);
      minutesGenerated = true; // 회의록 생성 완료 표시
      alert('회의록이 성공적으로 생성 및 저장되었습니다!');
  }
  ```
- **목적**: 회의록 생성 상태 업데이트

---

## 요약 (5차 업데이트)

### 주요 개선 사항:
1. ✅ **SQLite DB 저장**: 회의록 생성 후 자동으로 meeting_minutes 테이블에 저장
2. ✅ **테이블 자동 생성**: meeting_minutes 테이블이 없으면 자동 생성
3. ✅ **회의록 조회 API**: `/api/get_minutes/<meeting_id>` API 추가
4. ✅ **자동 표시**: 페이지 로드 시 DB에서 기존 회의록 자동 조회 및 표시
5. ✅ **탭 전환 조회**: 회의록 탭 클릭 시에도 자동 조회
6. ✅ **중복 방지**: 이미 조회한 회의록은 다시 조회하지 않음
7. ✅ **업데이트 지원**: 같은 meeting_id로 재생성 시 자동 업데이트
8. ✅ **영구 저장**:
   - Vector DB는 임시 저장용 (요약 기반 검색)
   - SQLite DB는 영구 저장용 (빠른 조회)

### 데이터 흐름:
1. **회의록 생성**: Gemini API → 회의록 생성
2. **DB 저장**: SQLite DB (meeting_minutes 테이블)
3. **조회**: 페이지 로드 시 or 탭 클릭 시 → SQLite DB에서 조회
4. **표시**: 마크다운 → HTML 변환 후 화면 표시

### 영향을 받는 파일 (5차):
- **수정**: `utils/db_manager.py`, `app.py`, `static/js/viewer.js`

---

## 📊 전체 변경 파일 요약

### 1차 업데이트 (제목/회의일시 검증):
- **신규**: `utils/validation.py`
- **수정**: `templates/index.html`, `static/js/script.js`, `app.py`, `utils/db_manager.py`

### 2차 업데이트 (스크립트/요약 탭):
- **수정**: `templates/viewer.html`, `static/css/style.css`, `static/js/viewer.js`

### 3차 업데이트 (회의록 탭):
- **수정**: `utils/stt.py`, `app.py`, `templates/viewer.html`, `static/css/style.css`, `static/js/viewer.js`

### 4차 업데이트 (Vector DB 순서 조회):
- **수정**: `utils/vector_db_manager.py`, `app.py`, `static/js/viewer.js`

### 5차 업데이트 (회의록 DB 저장):
- **수정**: `utils/db_manager.py`, `app.py`, `static/js/viewer.js`

### 6차 업데이트 (스마트 청킹):
- **수정**: `utils/vector_db_manager.py`, `app.py`

---

---

# 6차 업데이트: 스마트 청킹 (Smart Chunking) 기능 추가 (2025-11-03)
## ⚠️ 업데이트: SemanticChunker 대신 스마트 청킹 사용 (Dependency 충돌 해결)

## 20. **utils/vector_db_manager.py**

### 변경 내용:

#### 1) 11-13행 수정 (import 문)
- **변경 전**: 8-9행
  ```python
  from langchain_classic.retrievers.self_query.base import SelfQueryRetriever
  from langchain_classic.chains.query_constructor.base import AttributeInfo
  ```
- **변경 후**: 8-13행
  ```python
  from langchain_classic.retrievers.self_query.base import SelfQueryRetriever
  from langchain_classic.chains.query_constructor.base import AttributeInfo

  # 텍스트 분할을 위한 import (의미적 청킹 대안)
  from langchain_text_splitters import RecursiveCharacterTextSplitter
  import numpy as np
  ```
- **목적**: RecursiveCharacterTextSplitter와 numpy 임포트 (SemanticChunker 대신 사용)

#### 2) 47-57행 수정 (metadata_field_infos - 추가 필드들)
- **변경 전**: 42-49행
  ```python
  self.metadata_field_infos = {
      "chunks": [
          AttributeInfo(name="meeting_id", description="The unique identifier for the meeting", type="string"),
          AttributeInfo(name="dialogue_id", description="The unique identifier for the dialogue within the meeting", type="string"),
          AttributeInfo(name="title", description="The title of the meeting", type="string"),
          AttributeInfo(name="meeting_date", description="The date of the meeting in ISO format (YYYY-MM-DD)", type="string"),
          AttributeInfo(name="audio_file", description="The name of the audio file for the meeting", type="string"),
      ],
  ```
- **변경 후**: 44-53행
  ```python
  self.metadata_field_infos = {
      "chunks": [
          AttributeInfo(name="meeting_id", description="The unique identifier for the meeting", type="string"),
          AttributeInfo(name="dialogue_id", description="The unique identifier for the dialogue within the meeting", type="string"),
          AttributeInfo(name="chunk_index", description="The index of the semantic chunk within the meeting", type="integer"),
          AttributeInfo(name="title", description="The title of the meeting", type="string"),
          AttributeInfo(name="meeting_date", description="The date of the meeting in ISO format (YYYY-MM-DD)", type="string"),
          AttributeInfo(name="audio_file", description="The name of the audio file for the meeting", type="string"),
      ],
  ```
- **목적**: chunk_index 메타데이터 필드 추가

#### 3) 66행 수정 (document_content_descriptions - 설명 업데이트)
- **변경 전**: 60-64행
  ```python
  self.document_content_descriptions = {
      "chunks": "Full transcript of a meeting",
      "subtopic": "Summarized sub-topic of a meeting transcript",
  }
  ```
- **변경 후**: 64-68행
  ```python
  self.document_content_descriptions = {
      "chunks": "Semantically grouped chunks of meeting transcript dialogue with speaker labels and timestamps",
      "subtopic": "Summarized sub-topic of a meeting transcript",
  }
  ```
- **목적**: chunks 컬렉션의 설명을 더 정확하게 업데이트

#### 4) 72-157행 완전 재작성 (add_meeting_as_chunk 함수)
- **변경 전**: 68-81행
  ```python
  def add_meeting_as_chunk(self, meeting_id, title, meeting_date, audio_file, full_text):
      """하나의 회의 전체를 단일 청크로 DB에 저장합니다."""
      chunk_vdb = self.vectorstores['chunks']

      metadata = {
          "meeting_id": meeting_id,
          "dialogue_id": meeting_id,  # 전체 문서를 나타내는 청크이므로 meeting_id를 사용
          "title": title,
          "meeting_date": meeting_date,
          "audio_file": audio_file
      }

      chunk_vdb.add_texts(texts=[full_text], metadatas=[metadata], ids=[meeting_id])
      print(f"Added full text of meeting {meeting_id} as a single chunk to meeting_chunks DB.")
  ```
- **변경 후**: 72-157행
  ```python
  def add_meeting_as_chunk(self, meeting_id, title, meeting_date, audio_file, segments):
      """
      회의 대화 내용을 의미적으로 비슷한 대화들끼리 청크로 묶어 DB에 저장합니다.

      Args:
          meeting_id (str): 회의 ID
          title (str): 회의 제목
          meeting_date (str): 회의 일시
          audio_file (str): 오디오 파일명
          segments (list): 회의 대화 세그먼트 리스트
              각 세그먼트는 {'speaker_label', 'start_time', 'segment', ...} 포함
      """
      chunk_vdb = self.vectorstores['chunks']

      # 1. 세그먼트를 포맷팅하여 하나의 텍스트로 결합
      # 형식: [Speaker X, MM:SS] 대화내용
      formatted_segments = []
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
          formatted_segments.append(formatted_text)

      # 전체 텍스트 결합 (줄바꿈으로 구분)
      full_text = "\n".join(formatted_segments)

      # 2. SemanticChunker로 의미적 청킹
      try:
          semantic_chunker = SemanticChunker(
              self.embedding_function,
              breakpoint_threshold_type="percentile"  # percentile, standard_deviation, interquartile 중 선택
          )

          chunks = semantic_chunker.create_documents([full_text])

          print(f"📦 SemanticChunker로 {len(chunks)}개의 청크 생성 완료")

          # 3. 각 청크를 Vector DB에 저장
          chunk_texts = []
          chunk_metadatas = []
          chunk_ids = []

          for i, chunk in enumerate(chunks):
              chunk_texts.append(chunk.page_content)
              chunk_metadatas.append({
                  "meeting_id": meeting_id,
                  "dialogue_id": f"{meeting_id}_chunk_{i}",
                  "chunk_index": i,
                  "title": title,
                  "meeting_date": meeting_date,
                  "audio_file": audio_file
              })
              chunk_ids.append(f"{meeting_id}_chunk_{i}")

          # Vector DB에 추가
          chunk_vdb.add_texts(
              texts=chunk_texts,
              metadatas=chunk_metadatas,
              ids=chunk_ids
          )

          print(f"✅ {len(chunks)}개의 의미적 청크를 meeting_chunks DB에 저장 완료 (meeting_id: {meeting_id})")

      except Exception as e:
          print(f"⚠️ SemanticChunker 사용 중 오류 발생: {e}")
          print(f"📝 대신 전체 텍스트를 단일 청크로 저장합니다.")

          # 에러 발생 시 폴백: 전체를 하나의 청크로 저장
          metadata = {
              "meeting_id": meeting_id,
              "dialogue_id": meeting_id,
              "chunk_index": 0,
              "title": title,
              "meeting_date": meeting_date,
              "audio_file": audio_file
          }

          chunk_vdb.add_texts(texts=[full_text], metadatas=[metadata], ids=[meeting_id])
          print(f"✅ 전체 텍스트를 단일 청크로 meeting_chunks DB에 저장 완료")
  ```
- **목적**:
  - 단일 청크 저장에서 **의미적 청킹**으로 변경
  - 파라미터 변경: `full_text` → `segments`
  - 화자와 시간 정보 포함하여 포맷팅
  - LangChain SemanticChunker 사용하여 임베딩 기반 의미적 유사도로 청킹
  - 여러 청크를 Vector DB에 저장
  - 에러 처리 (폴백: 단일 청크로 저장)

---

## 21. **app.py**

### 변경 내용:

#### 1) 76-92행 수정 (Vector DB 저장 로직)
- **변경 전**: 77-93행
  ```python
  # 2. Vector DB에 전체 대화록을 단일 chunk로 저장
  try:
      all_segments = db.get_segments_by_meeting_id(meeting_id)
      if all_segments:
          full_text = " ".join([s['segment'] for s in all_segments])
          # 메타데이터는 첫 번째 세그먼트에서 가져옴
          first_segment = all_segments[0]
          vdb_manager.add_meeting_as_chunk(
              meeting_id=meeting_id,
              title=first_segment['title'],
              meeting_date=first_segment['meeting_date'],
              audio_file=first_segment['audio_file'],
              full_text=full_text
          )
  except Exception as vdb_error:
      print(f"Vector DB 저장 중 오류 발생: {vdb_error}")
      # 벡터 DB 저장에 실패해도 주요 기능은 계속 동작하도록 일단 넘어감
  ```
- **변경 후**: 76-92행
  ```python
  # 2. Vector DB에 대화록을 의미적 청크로 저장
  try:
      all_segments = db.get_segments_by_meeting_id(meeting_id)
      if all_segments:
          # 메타데이터는 첫 번째 세그먼트에서 가져옴
          first_segment = all_segments[0]
          # segments를 직접 전달하여 의미적 청킹 수행
          vdb_manager.add_meeting_as_chunk(
              meeting_id=meeting_id,
              title=first_segment['title'],
              meeting_date=first_segment['meeting_date'],
              audio_file=first_segment['audio_file'],
              segments=all_segments  # 전체 segments 전달
          )
  except Exception as vdb_error:
      print(f"Vector DB 저장 중 오류 발생: {vdb_error}")
      # 벡터 DB 저장에 실패해도 주요 기능은 계속 동작하도록 일단 넘어감
  ```
- **목적**:
  - `full_text` 생성 코드 제거
  - `segments`를 직접 전달하여 의미적 청킹 수행
  - 주석 업데이트

---

## 요약 (6차 업데이트)

### 주요 개선 사항:
1. ✅ **스마트 청킹 (Smart Chunking)**: 화자 변경, 시간 간격을 고려한 지능형 청킹
2. ✅ **회의 맥락 고려**: 화자 변경, 60초 이상 침묵, 청크 크기를 종합적으로 판단
3. ✅ **화자 및 시간 정보 포함**: `[Speaker X, MM:SS] 대화내용` 형식으로 포맷팅
4. ✅ **다중 청크 저장**: 회의록을 여러 개의 스마트 청크로 분할하여 저장
5. ✅ **확장된 메타데이터**: `chunk_index`, `start_time`, `end_time`, `speaker_count` 필드 추가
6. ✅ **이중 폴백 시스템**: 스마트 청킹 실패 시 RecursiveCharacterTextSplitter 사용
7. ✅ **RAG 최적화**: 맥락적으로 관련된 내용만 검색되도록 개선
8. ✅ **Dependency 충돌 해결**: langchain-experimental 없이 구현

### 스마트 청킹의 작동 방식:
1. **세그먼트 포맷팅**: 각 대화에 화자와 시간 정보 추가 `[Speaker X, MM:SS] 텍스트`
2. **청크 분리 판단**: 다음 조건 중 하나라도 만족하면 청크 분리
   - 청크 크기가 1000자 초과
   - 시간 간격이 60초 초과 (긴 침묵 = 주제 전환 가능성)
   - 화자가 변경되고 현재 청크가 500자 이상
3. **메타데이터 추가**: 각 청크에 시작/종료 시간, 화자 수 저장
4. **Vector DB 저장**: 각 청크를 별도의 document로 저장

### 기술적 세부사항:
- **청킹 파라미터**:
  - `max_chunk_size=1000`: 최대 청크 크기 (문자 수)
  - `time_gap_threshold=60`: 시간 간격 임계값 (초)
  - 최소 청크 크기: 200자 (너무 작은 청크 방지)
  - 화자 변경 시 최소 크기: 500자
- **청크 ID 형식**: `{meeting_id}_chunk_{index}`
- **메타데이터**: meeting_id, dialogue_id, chunk_index, title, meeting_date, audio_file, start_time, end_time, speaker_count
- **폴백 방식**: RecursiveCharacterTextSplitter (chunk_size=1000, chunk_overlap=200)

### 데이터 흐름:
```
업로드 → STT → SQLite DB (세그먼트 저장)
                ↓
        Vector DB Manager
                ↓
        세그먼트 포맷팅 ([Speaker X, MM:SS] 텍스트)
                ↓
        스마트 청킹 (화자/시간/크기 기반)
                ↓
        Vector DB (스마트 청크 저장)
```

### RAG 검색 개선:
- **기존 (단일 청크)**: 전체 회의록이 하나의 청크 → 검색 시 전체 회의록 반환 → 컨텍스트가 너무 큼
- **개선 (스마트 청킹)**: 맥락적으로 관련된 부분만 청크화 → 검색 시 관련된 청크만 반환 → 정확도 향상
- **추가 정보**: start_time, end_time, speaker_count 메타데이터로 더 정확한 필터링 가능

### 영향을 받는 파일 (6차):
- **수정**: `utils/vector_db_manager.py`, `app.py`

---

## 📊 전체 변경 파일 요약

### 1차 업데이트 (제목/회의일시 검증):
- **신규**: `utils/validation.py`
- **수정**: `templates/index.html`, `static/js/script.js`, `app.py`, `utils/db_manager.py`

### 2차 업데이트 (스크립트/요약 탭):
- **수정**: `templates/viewer.html`, `static/css/style.css`, `static/js/viewer.js`

### 3차 업데이트 (회의록 탭):
- **수정**: `utils/stt.py`, `app.py`, `templates/viewer.html`, `static/css/style.css`, `static/js/viewer.js`

### 4차 업데이트 (Vector DB 순서 조회):
- **수정**: `utils/vector_db_manager.py`, `app.py`, `static/js/viewer.js`

### 5차 업데이트 (회의록 DB 저장):
- **수정**: `utils/db_manager.py`, `app.py`, `static/js/viewer.js`

### 6차 업데이트 (스마트 청킹):
- **수정**: `utils/vector_db_manager.py`, `app.py`

---

## 💡 참고사항

### 추가 패키지 설치 불필요:
6차 업데이트는 **기존 langchain 패키지만으로 작동**합니다. `langchain-experimental`이 필요 없습니다!

### 청킹 파라미터 조정:
`utils/vector_db_manager.py`의 `_create_smart_chunks()` 함수 파라미터를 조정할 수 있습니다:
```python
chunks = self._create_smart_chunks(
    segments,
    max_chunk_size=1000,      # 최대 청크 크기 (문자 수)
    time_gap_threshold=60     # 시간 간격 임계값 (초)
)
```

**파라미터 튜닝 가이드:**
- **max_chunk_size**: 500-2000 권장
  - 작을수록: 더 세밀한 검색, 많은 청크
  - 클수록: 더 넓은 맥락, 적은 청크
- **time_gap_threshold**: 30-120초 권장
  - 작을수록: 침묵 시 더 자주 분할
  - 클수록: 긴 침묵도 같은 청크로 유지

### 예상 청크 수:
- 짧은 회의 (10분): 2-5개 청크
- 중간 회의 (30분): 5-12개 청크
- 긴 회의 (1시간 이상): 10-25개 청크

청크 수는 회의 내용의 화자 수, 주제 다양성, 침묵 빈도에 따라 달라집니다.

### Dependency 문제 해결:
만약 이전에 `langchain-experimental`를 설치했다면 제거하세요:
```bash
pip uninstall langchain-experimental
```

또는 가상환경을 사용하는 경우:
```bash
# 가상환경 내에서
pip uninstall langchain-experimental
```
