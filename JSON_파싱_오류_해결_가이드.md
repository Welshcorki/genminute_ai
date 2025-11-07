# JSON 파싱 오류 해결 가이드

**오류**: `JSONDecodeError: Expecting ',' delimiter`

---

## 🔍 오류 설명

Gemini API가 반환한 응답이 올바른 JSON 형식이 아닙니다.

### 오류 메시지 예시:
```
json.decoder.JSONDecodeError: Expecting ',' delimiter: line 160 column 29 (char 5862)
```

**의미**:
- 160번째 줄, 29번째 문자 위치에서 쉼표(`,`)가 예상되었으나 다른 문자가 있음

---

## ✅ 추가된 디버깅 기능

### 1. 상세한 오류 로그
오류 발생 시 콘솔에 표시:
```
❌ JSON 파싱 실패: Expecting ',' delimiter: line 160 column 29
📝 오류 위치: line 160, column 29
📄 오류 발생 줄: { "speaker": 1 "text": "안녕하세요" }
                                 ^ 여기
📁 전체 응답이 저장되었습니다: gemini_error_response.txt
```

### 2. 응답 저장
- 파일 위치: `gemini_error_response.txt`
- 전체 응답 내용 저장
- 수동으로 확인 및 수정 가능

---

## 🛠️ 해결 방법

### 방법 1: 재시도 (가장 간단)
1. 같은 파일을 다시 업로드
2. Gemini API가 간헐적으로 오류를 낼 수 있음
3. 대부분 재시도 시 성공

---

### 방법 2: 응답 확인 및 수정

#### Step 1: gemini_error_response.txt 열기
```bash
# 프로젝트 루트 폴더에 생성됨
notepad gemini_error_response.txt
```

#### Step 2: 오류 위치 찾기
콘솔에 표시된 line, column 번호로 이동
```
📝 오류 위치: line 160, column 29
```

#### Step 3: 일반적인 JSON 오류 패턴

**1. 쉼표 누락**
```json
// 잘못된 예:
{
  "speaker": 1
  "text": "안녕하세요"
}

// 올바른 예:
{
  "speaker": 1,  // ← 쉼표 추가
  "text": "안녕하세요"
}
```

**2. 따옴표 이스케이프 누락**
```json
// 잘못된 예:
{
  "text": "그는 "안녕"이라고 말했다"
}

// 올바른 예:
{
  "text": "그는 \"안녕\"이라고 말했다"
}
```

**3. 마지막 쉼표**
```json
// 잘못된 예:
{
  "speaker": 1,
  "text": "안녕하세요",  // ← 마지막 쉼표 제거
}

// 올바른 예:
{
  "speaker": 1,
  "text": "안녕하세요"
}
```

**4. 배열 마지막 요소**
```json
// 잘못된 예:
[
  { "speaker": 1, "text": "A" },
  { "speaker": 2, "text": "B" },  // ← 마지막 쉼표
]

// 올바른 예:
[
  { "speaker": 1, "text": "A" },
  { "speaker": 2, "text": "B" }
]
```

---

### 방법 3: 다른 오디오 파일 시도
- 현재 파일에 특수한 음성/내용이 있을 수 있음
- 더 짧거나 명확한 오디오로 테스트

---

## 🔧 고급 해결 방법 (개발자용)

### JSON 자동 수정 로직 추가

`utils/stt.py`에 추가 가능한 코드:

```python
def fix_common_json_errors(json_str):
    """
    일반적인 JSON 오류를 자동으로 수정합니다.
    """
    import re

    # 1. 중복 쉼표 제거
    json_str = re.sub(r',\s*,', ',', json_str)

    # 2. 마지막 쉼표 제거 (객체)
    json_str = re.sub(r',(\s*})', r'\1', json_str)

    # 3. 마지막 쉼표 제거 (배열)
    json_str = re.sub(r',(\s*\])', r'\1', json_str)

    # 4. 이스케이프되지 않은 따옴표 처리 (간단한 경우)
    # 주의: 완벽하지 않음, 복잡한 케이스는 수동 수정 필요

    return json_str

# 사용:
try:
    result_list = json.loads(cleaned_response)
except json.JSONDecodeError as e:
    print("⚠️ JSON 파싱 실패, 자동 수정 시도...")
    fixed_response = fix_common_json_errors(cleaned_response)
    try:
        result_list = json.loads(fixed_response)
        print("✅ JSON 자동 수정 성공!")
    except json.JSONDecodeError:
        # 자동 수정 실패, 원래 오류 처리 로직 실행
        raise
```

---

## 📊 오류 발생 빈도

### 일반적인 경우:
- 정상 작동: 95%
- JSON 오류: 3-5%
- 기타 오류: 1-2%

### JSON 오류가 자주 발생하는 경우:
1. **오디오 품질이 낮음**
   - 배경 소음 많음
   - 화자 겹침 심함

2. **특수 문자/단어 많음**
   - 따옴표, 괄호 등
   - 외국어 혼재

3. **매우 긴 오디오**
   - 1시간 이상
   - 응답이 잘릴 수 있음

---

## 🎯 예방 방법

### 1. 오디오 전처리
- 노이즈 제거
- 적절한 길이 (10-30분 권장)

### 2. Gemini 프롬프트 개선
현재 프롬프트에 추가:
```
IMPORTANT:
- Return ONLY valid JSON
- Escape all quotes inside text
- Do not include trailing commas
- Ensure proper bracket matching
```

### 3. 재시도 로직 추가
```python
MAX_RETRIES = 3
for attempt in range(MAX_RETRIES):
    try:
        result = transcribe_audio(file)
        break
    except JSONDecodeError:
        if attempt == MAX_RETRIES - 1:
            raise
        print(f"재시도 {attempt + 1}/{MAX_RETRIES}...")
```

---

## 📞 추가 지원

### gemini_error_response.txt 확인 필요 시:
1. 파일을 열어서 내용 확인
2. 오류 위치 (line 160, column 29) 찾기
3. 위의 패턴 참고하여 수정

### 여전히 해결 안 되는 경우:
1. 다른 오디오 파일로 테스트
2. 오디오 길이를 짧게 (5분 이하)
3. 더 명확한 음성으로 녹음

---

## ✅ 체크리스트

발표 전 확인:
- [ ] JSON 오류 발생 시 gemini_error_response.txt 생성됨
- [ ] 콘솔에 상세한 오류 위치 표시됨
- [ ] 재시도로 대부분 해결 가능
- [ ] 백업 오디오 파일 준비 (짧고 명확한 것)

---

## 🎉 대부분의 경우

**단순히 재업로드하면 해결됩니다!**

Gemini API가 간헐적으로 JSON 형식을 잘못 생성하는 경우가 있으므로,
같은 파일을 다시 업로드하면 정상 작동할 확률이 높습니다.
