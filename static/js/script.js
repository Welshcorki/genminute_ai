document.addEventListener('DOMContentLoaded', () => {
    // --- Chatbot Toggle 기능 ---
    const chatbotToggleBtn = document.getElementById('chatbot-toggle-btn');
    const chatbotSidebar = document.getElementById('chatbot-sidebar');
    const btnCloseChatbot = document.getElementById('btn-close-chatbot');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotSendBtn = document.getElementById('chatbot-send-btn');
    const chatbotMessages = document.getElementById('chatbot-messages');
    const appContainer = document.querySelector('.app-container');

    // 드래그 앤 드롭 관련 변수
    let isDragging = false;
    let dragStartX = 0;
    let dragStartY = 0;
    let currentX = 0;
    let currentY = 0;
    let hasMoved = false;

    // 저장된 위치 복원
    if (chatbotToggleBtn) {
        const savedTop = localStorage.getItem('chatbot-btn-top');
        if (savedTop) {
            chatbotToggleBtn.style.top = savedTop;
        }

        // 드래그 시작 함수
        function startDrag(clientX, clientY) {
            isDragging = true;
            hasMoved = false;
            dragStartX = clientX - chatbotToggleBtn.offsetLeft;
            dragStartY = clientY - chatbotToggleBtn.offsetTop;
            chatbotToggleBtn.classList.add('dragging');
        }

        // 마우스 다운 - 드래그 시작
        chatbotToggleBtn.addEventListener('mousedown', (e) => {
            startDrag(e.clientX, e.clientY);
            e.preventDefault(); // 기본 동작 방지
        });

        // 터치 시작 - 모바일 지원
        chatbotToggleBtn.addEventListener('touchstart', (e) => {
            const touch = e.touches[0];
            startDrag(touch.clientX, touch.clientY);
            e.preventDefault();
        }, { passive: false });

        // 드래그 중 함수
        function onDrag(clientX, clientY) {
            if (!isDragging) return;

            hasMoved = true;
            currentX = clientX - dragStartX;
            currentY = clientY - dragStartY;

            // 화면 경계 제한
            const maxY = window.innerHeight - chatbotToggleBtn.offsetHeight;
            currentY = Math.max(0, Math.min(currentY, maxY));

            chatbotToggleBtn.style.top = currentY + 'px';
            chatbotToggleBtn.style.right = 'auto'; // 드래그 중에는 right 해제
            chatbotToggleBtn.style.left = currentX + 'px';
        }

        // 마우스 무브 - 드래그 중
        document.addEventListener('mousemove', (e) => {
            onDrag(e.clientX, e.clientY);
        });

        // 터치 무브 - 모바일 지원
        document.addEventListener('touchmove', (e) => {
            if (isDragging) {
                const touch = e.touches[0];
                onDrag(touch.clientX, touch.clientY);
                e.preventDefault();
            }
        }, { passive: false });

        // 드래그 종료 함수
        function endDrag() {
            if (isDragging) {
                isDragging = false;

                if (hasMoved) {
                    // 드래그했으면 오른쪽 끝으로 이동 (애니메이션 효과)
                    // dragging 클래스를 제거한 후 위치 변경으로 transition 적용
                    chatbotToggleBtn.classList.remove('dragging');

                    // 약간의 지연 후 오른쪽으로 이동 (transition 적용)
                    setTimeout(() => {
                        chatbotToggleBtn.style.left = 'auto';
                        chatbotToggleBtn.style.right = '20px';
                    }, 10);

                    // top 위치 저장
                    localStorage.setItem('chatbot-btn-top', chatbotToggleBtn.style.top);
                } else {
                    // 드래그하지 않고 클릭만 했으면 챗봇 열기
                    chatbotToggleBtn.classList.remove('dragging');
                    openChatbot();
                }
            }
        }

        // 마우스 업 - 드래그 종료
        document.addEventListener('mouseup', endDrag);

        // 터치 엔드 - 모바일 지원
        document.addEventListener('touchend', endDrag);
    }

    // 챗봇 열기 함수
    function openChatbot() {
        chatbotSidebar.classList.add('open');
        chatbotToggleBtn.classList.add('hidden');
        if (appContainer) {
            appContainer.classList.add('chatbot-open');
        }
    }

    // 챗봇 닫기
    if (btnCloseChatbot) {
        btnCloseChatbot.addEventListener('click', () => {
            chatbotSidebar.classList.remove('open');
            chatbotToggleBtn.classList.remove('hidden');
            if (appContainer) {
                appContainer.classList.remove('chatbot-open');
            }
        });
    }

    // 메시지 전송 (Enter 키)
    if (chatbotInput) {
        chatbotInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    }

    // 메시지 전송 (버튼 클릭)
    if (chatbotSendBtn) {
        chatbotSendBtn.addEventListener('click', sendChatMessage);
    }

    // 메시지 전송 함수
    function sendChatMessage() {
        const message = chatbotInput.value.trim();
        if (!message) return;

        // 사용자 메시지 추가
        addChatMessage('user', message);
        chatbotInput.value = '';

        // TODO: 여기에 API 호출 로직 추가 예정
        // 임시로 응답 메시지 표시
        setTimeout(() => {
            addChatMessage('assistant', '챗봇 API 연동이 아직 구현되지 않았습니다. 곧 추가될 예정입니다.');
        }, 500);
    }

    // 채팅 메시지 추가 함수
    function addChatMessage(role, text) {
        // 환영 메시지 제거 (첫 메시지 시)
        const welcome = chatbotMessages.querySelector('.chatbot-welcome');
        if (welcome) {
            welcome.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}`;

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'chat-bubble';
        bubbleDiv.textContent = text;

        messageDiv.appendChild(bubbleDiv);
        chatbotMessages.appendChild(messageDiv);

        // 스크롤을 최하단으로
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
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
        
        // 폼 제출 시 유효성 검사 및 프로그레스바 표시
        uploadForm.addEventListener('submit', async (event) => {
            event.preventDefault(); // 기본 폼 제출 막기

            // 제목 입력 검증
            if (!titleInput || titleInput.value.trim() === '') {
                alert('제목을 입력해 주세요.');
                return;
            }

            // 파일 선택 검증
            if (fileInput.files.length === 0) {
                alert('파일을 선택해 주세요.');
                return;
            }

            // 프로그레스바 시작
            startProgressBar();

            // FormData 생성
            const formData = new FormData(uploadForm);

            try {
                // AJAX로 파일 업로드 및 STT 처리
                const response = await fetch(uploadForm.action, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: formData
                });

                if (response.ok) {
                    const result = await response.json();

                    // 100% 완료 표시
                    completeProgress();

                    // 1초 후 페이지 이동
                    setTimeout(() => {
                        window.location.href = result.redirect_url || `/view/${result.meeting_id}`;
                    }, 1000);
                } else {
                    const error = await response.json();
                    hideProgressBar();
                    alert(`오류 발생: ${error.error || '알 수 없는 오류'}`);
                }
            } catch (error) {
                console.error('업로드 중 오류:', error);
                hideProgressBar();
                alert('업로드 중 오류가 발생했습니다. 다시 시도해 주세요.');
            }
        });

        // 프로그레스바 관련 변수
        let progressInterval = null;
        let currentProgress = 0;
        let progressPhase = 1; // 1: 0-80% (2분), 2: 80-100% (단계별)

        // 프로그레스바 시작 함수
        function startProgressBar() {
            const progressModal = document.getElementById('progress-modal');
            const progressBar = document.getElementById('progress-bar');
            const progressText = document.getElementById('progress-text');
            const progressStatus = document.getElementById('progress-status');

            progressModal.classList.add('active');
            currentProgress = 0;
            progressPhase = 1;

            // Phase 1: 0-80% (120초 = 2분)
            const phase1Duration = 120000; // 120초 = 2분
            const phase1Target = 80;
            const phase1Interval = 100; // 100ms마다 업데이트
            const phase1Increment = (phase1Target / phase1Duration) * phase1Interval;

            progressStatus.textContent = '음성 파일을 분석하고 있습니다...';

            progressInterval = setInterval(() => {
                if (progressPhase === 1) {
                    currentProgress += phase1Increment;

                    if (currentProgress >= phase1Target) {
                        currentProgress = phase1Target;
                        progressPhase = 2;
                        progressStatus.textContent = '음성 인식을 완료하고 있습니다...';

                        // Phase 2로 전환: 80-100% (10단계, 각 2%)
                        clearInterval(progressInterval);
                        startPhase2();
                    }

                    updateProgressBar(currentProgress);
                }
            }, phase1Interval);
        }

        // Phase 2: 80-100% (10단계)
        function startPhase2() {
            let step = 0;
            const totalSteps = 10;
            const stepIncrement = 2; // 2%씩 증가
            const stepInterval = 500; // 0.5초마다

            const phase2Interval = setInterval(() => {
                if (step < totalSteps) {
                    currentProgress += stepIncrement;
                    updateProgressBar(currentProgress);
                    step++;
                } else {
                    clearInterval(phase2Interval);
                }
            }, stepInterval);

            progressInterval = phase2Interval;
        }

        // 프로그레스바 업데이트
        function updateProgressBar(percent) {
            const progressBar = document.getElementById('progress-bar');
            const progressText = document.getElementById('progress-text');

            const displayPercent = Math.min(Math.round(percent), 99); // 최대 99%까지만 표시
            progressBar.style.width = displayPercent + '%';
            progressText.textContent = displayPercent + '%';
        }

        // 프로그레스바 완료
        function completeProgress() {
            clearInterval(progressInterval);

            const progressBar = document.getElementById('progress-bar');
            const progressText = document.getElementById('progress-text');
            const progressStatus = document.getElementById('progress-status');

            currentProgress = 100;
            progressBar.style.width = '100%';
            progressText.textContent = '100%';
            progressStatus.textContent = '완료! 페이지를 이동합니다...';
        }

        // 프로그레스바 숨기기
        function hideProgressBar() {
            clearInterval(progressInterval);
            const progressModal = document.getElementById('progress-modal');
            progressModal.classList.remove('active');
            currentProgress = 0;
            progressPhase = 1;
        }

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