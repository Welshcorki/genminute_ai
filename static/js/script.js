document.addEventListener('DOMContentLoaded', () => {
    // --- 공통 레이아웃 기능 ---
    const toggleButton = document.getElementById('toggle-ai-sidebar');
    const appContainer = document.querySelector('.app-container');

    if (toggleButton && appContainer) {
        toggleButton.addEventListener('click', () => {
            appContainer.classList.toggle('sidebar-collapsed');
        });
    }

    // --- 업로드 페이지 기능 ---
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        const dropZone = document.getElementById('drop-zone');
        const uploadButton = document.getElementById('upload-button');
        const fileInput = document.getElementById('audio-file-input');
        const fileNameDisplay = document.getElementById('file-name-display');
        const sttSubmitButton = document.querySelector('button[type="submit"]');
        const titleInput = document.querySelector('input[name="title"]');
        const meetingDateInput = document.getElementById('meeting-date-input');

        // '파일 선택' 버튼 클릭
        if (uploadButton) {
            uploadButton.addEventListener('click', () => fileInput.click());
        }

        // 파일이 직접 선택되었을 때
        if (fileInput) {
            fileInput.addEventListener('change', () => {
                if (fileInput.files.length > 0) {
                    handleFile(fileInput.files[0]);
                    // 회의 일시가 비어있으면 현재 날짜/시간 자동 입력
                    autoFillMeetingDate();
                }
            });
        }

        // 드래그 앤 드롭
        if (dropZone) {
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('drag-over');
            });
            dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                dropZone.classList.remove('drag-over');
            });
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('drag-over');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    fileInput.files = files;
                    handleFile(files[0]);
                    // 회의 일시가 비어있으면 현재 날짜/시간 자동 입력
                    autoFillMeetingDate();
                }
            });
        }
        
        // 폼 제출 시 유효성 검사 및 로딩 상태 표시
        uploadForm.addEventListener('submit', (event) => {
            // 제목 입력 검증
            if (!titleInput || titleInput.value.trim() === '') {
                event.preventDefault(); // 폼 제출을 막고 경고창을 띄움
                alert('제목을 입력해 주세요.');
                return;
            }

            // 파일 선택 검증
            if (fileInput.files.length === 0) {
                event.preventDefault(); // 폼 제출을 막고 경고창을 띄움
                alert('파일을 선택해 주세요.');
                return;
            }

            // 모든 검증 통과 시 버튼 상태를 변경하고 폼 제출 진행
            if(sttSubmitButton) {
                sttSubmitButton.textContent = '처리 중...';
                sttSubmitButton.disabled = true;
            }
        });

        // 파일 처리 및 유효성 검사 함수
        function handleFile(file) {
            if (!file) return;
            const allowedExtensions = ['.wav', '.mp3', '.m4a', '.flac'];
            const fileName = file.name;
            const fileExtension = fileName.substring(fileName.lastIndexOf('.')).toLowerCase();

            if (allowedExtensions.includes(fileExtension)) {
                fileNameDisplay.textContent = `선택된 파일: ${fileName}`;
                fileNameDisplay.style.color = 'var(--text-color)';
            } else {
                fileNameDisplay.textContent = '지원하지 않는 파일 형식입니다.';
                fileNameDisplay.style.color = '#e74c3c';
                fileInput.value = '';
            }
        }

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
    }
});