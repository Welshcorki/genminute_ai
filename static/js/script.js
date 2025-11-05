document.addEventListener('DOMContentLoaded', () => {
    // --- Chatbot Toggle 기능 ---
    const chatbotToggleBtn = document.getElementById('chatbot-toggle-btn');
    const chatbotSidebar = document.getElementById('chatbot-sidebar');
    const btnCloseChatbot = document.getElementById('btn-close-chatbot');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotSendBtn = document.getElementById('chatbot-send-btn');
    const chatbotMessages = document.getElementById('chatbot-messages');
    const appContainer = document.querySelector('.app-container');

    // --- 챗봇 대화 내역 및 상태 관리 (sessionStorage) ---
    const CHAT_HISTORY_KEY = 'chatbot_history';
    const CHATBOT_STATE_KEY = 'chatbot_state';

    // 페이지 로드 시 대화 내역 불러오기
    loadChatHistory();

    // 페이지 로드 시 챗봇 상태 복원
    restoreChatbotState();

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
        // 챗봇 열림 상태 저장
        sessionStorage.setItem(CHATBOT_STATE_KEY, 'open');
    }

    // 챗봇 닫기 함수
    function closeChatbot() {
        chatbotSidebar.classList.remove('open');
        chatbotToggleBtn.classList.remove('hidden');
        if (appContainer) {
            appContainer.classList.remove('chatbot-open');
        }
        // 챗봇 닫힘 상태 저장
        sessionStorage.setItem(CHATBOT_STATE_KEY, 'closed');
    }

    // 챗봇 닫기 버튼 이벤트
    if (btnCloseChatbot) {
        btnCloseChatbot.addEventListener('click', closeChatbot);
    }

    // 챗봇 상태 복원 함수
    function restoreChatbotState() {
        const savedState = sessionStorage.getItem(CHATBOT_STATE_KEY);
        if (savedState === 'open') {
            // transition 비활성화 (애니메이션 방지)
            chatbotSidebar.classList.add('no-transition');
            if (appContainer) {
                appContainer.classList.add('no-transition');
            }

            // 챗봇이 열려있던 상태였으면 다시 열기
            chatbotSidebar.classList.add('open');
            chatbotToggleBtn.classList.add('hidden');
            if (appContainer) {
                appContainer.classList.add('chatbot-open');
            }

            // 다음 프레임에서 transition 재활성화 (사용자 상호작용 시 애니메이션 작동)
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    chatbotSidebar.classList.remove('no-transition');
                    if (appContainer) {
                        appContainer.classList.remove('no-transition');
                    }
                });
            });

            console.log('✅ 챗봇 열림 상태 복원 (애니메이션 없음)');
        } else {
            // 명시적으로 닫힌 상태이거나 저장된 값이 없으면 닫힌 상태 유지
            console.log('ℹ️ 챗봇 닫힘 상태 유지');
        }
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
    async function sendChatMessage() {
        const message = chatbotInput.value.trim();
        if (!message) return;

        // 사용자 메시지 추가
        addChatMessage('user', message);
        chatbotInput.value = '';

        // 로딩 메시지 표시 (저장하지 않음)
        const loadingMsg = addChatMessage('assistant', '답변을 생성하고 있습니다...', false, false);
        loadingMsg.classList.add('loading');

        try {
            // API 호출
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: message,
                    // meeting_id: null  // 특정 회의로 제한하려면 여기에 meeting_id 전달
                })
            });

            const data = await response.json();

            // 로딩 메시지 제거
            loadingMsg.remove();

            if (data.success) {
                // 답변 표시
                addChatMessage('assistant', data.answer);

                // 출처 정보가 있으면 표시 (선택적)
                if (data.sources && data.sources.length > 0) {
                    const sourcesText = formatSources(data.sources);
                    addChatMessage('assistant', sourcesText, true); // 작은 글씨로 표시
                }
            } else {
                addChatMessage('assistant', `오류: ${data.error || '알 수 없는 오류가 발생했습니다.'}`);
            }
        } catch (error) {
            console.error('챗봇 API 호출 오류:', error);
            loadingMsg.remove();
            addChatMessage('assistant', '죄송합니다. 서버와 통신 중 오류가 발생했습니다. 다시 시도해 주세요.');
        }
    }

    // 출처 정보 포맷팅
    function formatSources(sources) {
        if (!sources || sources.length === 0) return '';

        const uniqueMeetings = new Set();
        sources.forEach(source => {
            if (source.title) {
                uniqueMeetings.add(`"${source.title}" (${source.meeting_date})`);
            }
        });

        if (uniqueMeetings.size === 0) return '';

        return `📌 출처: ${Array.from(uniqueMeetings).join(', ')}`;
    }

    // sessionStorage에서 대화 내역 불러오기
    function loadChatHistory() {
        try {
            const historyJson = sessionStorage.getItem(CHAT_HISTORY_KEY);
            if (!historyJson) return; // 저장된 내역이 없으면 종료

            const history = JSON.parse(historyJson);
            if (!history.messages || history.messages.length === 0) return;

            // 환영 메시지 제거
            const welcome = chatbotMessages.querySelector('.chatbot-welcome');
            if (welcome) {
                welcome.remove();
            }

            // 저장된 메시지들을 화면에 표시
            history.messages.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.className = `chat-message ${msg.role}`;

                const bubbleDiv = document.createElement('div');
                bubbleDiv.className = 'chat-bubble';

                // 출처 정보는 작은 글씨로
                if (msg.isSource) {
                    bubbleDiv.style.fontSize = '0.85rem';
                    bubbleDiv.style.opacity = '0.8';
                }

                bubbleDiv.textContent = msg.content;
                messageDiv.appendChild(bubbleDiv);
                chatbotMessages.appendChild(messageDiv);
            });

            // 스크롤을 최하단으로
            chatbotMessages.scrollTop = chatbotMessages.scrollHeight;

            console.log(`✅ 챗봇 대화 내역 ${history.messages.length}개 복원됨`);
        } catch (error) {
            console.error('챗봇 대화 내역 불러오기 오류:', error);
        }
    }

    // sessionStorage에 메시지 저장
    function saveChatMessage(role, content, isSource = false) {
        try {
            // 기존 내역 가져오기
            const historyJson = sessionStorage.getItem(CHAT_HISTORY_KEY);
            const history = historyJson ? JSON.parse(historyJson) : { messages: [] };

            // 새 메시지 추가
            history.messages.push({
                role: role,
                content: content,
                isSource: isSource,
                timestamp: new Date().toISOString()
            });

            // 저장
            sessionStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(history));
        } catch (error) {
            console.error('챗봇 메시지 저장 오류:', error);
        }
    }

    // 채팅 메시지 추가 함수
    function addChatMessage(role, text, isSource = false, saveToStorage = true) {
        // 환영 메시지 제거 (첫 메시지 시)
        const welcome = chatbotMessages.querySelector('.chatbot-welcome');
        if (welcome) {
            welcome.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}`;

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'chat-bubble';

        // 출처 정보는 작은 글씨로
        if (isSource) {
            bubbleDiv.style.fontSize = '0.85rem';
            bubbleDiv.style.opacity = '0.8';
        }

        bubbleDiv.textContent = text;

        messageDiv.appendChild(bubbleDiv);
        chatbotMessages.appendChild(messageDiv);

        // 스크롤을 최하단으로
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;

        // sessionStorage에 저장 (로딩 메시지는 저장 안 함)
        if (saveToStorage) {
            saveChatMessage(role, text, isSource);
        }

        return messageDiv;  // 로딩 메시지 제거를 위해 반환
    }

    // --- 업로드 페이지 기능 (오디오) ---
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        const dropZone = document.getElementById('drop-zone');
        const uploadButton = document.getElementById('upload-button');
        const fileInput = document.getElementById('audio-file-input');
        const fileNameDisplay = document.getElementById('file-name-display');
        const submitButton = document.getElementById('submit-button');
        const titleInput = document.querySelector('input[name="title"]');

        // 파일 대화상자 상태 추적
        let fileDialogOpen = false;

        // '파일 선택' 버튼 클릭
        if (uploadButton) {
            uploadButton.addEventListener('click', () => {
                fileDialogOpen = true;
                fileInput.click();
            });
        }

        // 파일이 직접 선택되었을 때
        if (fileInput) {
            fileInput.addEventListener('change', () => {
                fileDialogOpen = false;
                if (fileInput.files.length > 0) {
                    const file = fileInput.files[0];
                    handleFile(file);

                    // 파일이 선택되면 노트 생성 버튼 보이기
                    if (submitButton) {
                        submitButton.style.display = 'block';
                    }
                } else {
                    // 파일이 없으면 UI 초기화
                    fileNameDisplay.textContent = '';
                    if (submitButton) {
                        submitButton.style.display = 'none';
                    }
                }
            });
        }

        // 파일 대화상자가 닫힌 후 파일 선택 여부 확인
        window.addEventListener('focus', () => {
            if (fileDialogOpen) {
                fileDialogOpen = false;
                // 파일 대화상자가 닫힌 후 잠시 후 확인
                setTimeout(() => {
                    if (fileInput && fileInput.files.length === 0) {
                        // 파일이 선택되지 않은 경우 UI 초기화
                        fileNameDisplay.textContent = '';
                        if (submitButton) {
                            submitButton.style.display = 'none';
                        }
                    }
                }, 300);
            }
        }, true);

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
                    const file = files[0];
                    handleFile(file);

                    // 파일이 드롭되면 노트 생성 버튼 보이기
                    if (submitButton) {
                        submitButton.style.display = 'block';
                    }
                } else {
                    // 파일이 없으면 UI 초기화
                    fileNameDisplay.textContent = '';
                    if (submitButton) {
                        submitButton.style.display = 'none';
                    }
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
            const allowedExtensions = ['.wav', '.mp3', '.m4a', '.flac', '.mp4'];
            const fileName = file.name;
            const fileExtension = fileName.substring(fileName.lastIndexOf('.')).toLowerCase();

            if (allowedExtensions.includes(fileExtension)) {
                fileNameDisplay.textContent = `선택된 파일: ${fileName}`;
                fileNameDisplay.style.color = 'var(--text-color)';
            } else {
                fileNameDisplay.textContent = '지원하지 않는 파일 형식입니다.';
                fileNameDisplay.style.color = '#e74c3c';
                fileInput.value = '';
                // 유효하지 않은 파일인 경우 버튼 숨기기
                if (submitButton) {
                    submitButton.style.display = 'none';
                }
            }
        }
    }

    // --- 스크립트 입력 페이지 기능 ---
    const scriptForm = document.getElementById('script-form');
    if (scriptForm) {
        const scriptTextInput = document.getElementById('script-text-input');
        const scriptTitleInput = document.querySelector('input[name="title"][form="script-form"]');
        const scriptMeetingDateInput = document.getElementById('script-meeting-date');

        // 폼 제출 시 유효성 검사 및 프로그레스바 표시
        scriptForm.addEventListener('submit', async (event) => {
            event.preventDefault(); // 기본 폼 제출 막기

            // 제목 입력 검증
            if (!scriptTitleInput || scriptTitleInput.value.trim() === '') {
                alert('제목을 입력해 주세요.');
                return;
            }

            // 스크립트 내용 검증
            if (!scriptTextInput || scriptTextInput.value.trim() === '') {
                alert('스크립트 내용을 입력해 주세요.');
                return;
            }

            // 프로그레스바 시작
            startScriptProgressBar();

            // FormData 생성
            const formData = new FormData(scriptForm);

            try {
                // AJAX로 스크립트 처리
                const response = await fetch(scriptForm.action, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: formData
                });

                if (response.ok) {
                    const result = await response.json();

                    // 100% 완료 표시
                    completeScriptProgress();

                    // 1초 후 페이지 이동
                    setTimeout(() => {
                        window.location.href = result.redirect_url || `/view/${result.meeting_id}`;
                    }, 1000);
                } else {
                    const error = await response.json();
                    hideScriptProgressBar();
                    alert(`오류 발생: ${error.error || '알 수 없는 오류'}`);
                }
            } catch (error) {
                console.error('스크립트 처리 중 오류:', error);
                hideScriptProgressBar();
                alert('처리 중 오류가 발생했습니다. 다시 시도해 주세요.');
            }
        });

        // 프로그레스바 관련 변수 (스크립트용)
        let scriptProgressInterval = null;
        let scriptCurrentProgress = 0;

        // 프로그레스바 시작 함수 (스크립트용)
        function startScriptProgressBar() {
            const progressModal = document.getElementById('progress-modal');
            const progressBar = document.getElementById('progress-bar');
            const progressText = document.getElementById('progress-text');
            const progressStatus = document.getElementById('progress-status');
            const progressTitle = document.getElementById('progress-title');

            progressModal.classList.add('active');
            scriptCurrentProgress = 0;

            // 스크립트 처리는 오디오보다 빠르므로 60초로 설정
            const totalDuration = 60000; // 60초
            const targetProgress = 95;
            const interval = 100; // 100ms마다 업데이트
            const increment = (targetProgress / totalDuration) * interval;

            progressTitle.textContent = '스크립트 처리 중...';
            progressStatus.textContent = '스크립트를 분석하고 있습니다...';

            scriptProgressInterval = setInterval(() => {
                scriptCurrentProgress += increment;

                if (scriptCurrentProgress >= targetProgress) {
                    scriptCurrentProgress = targetProgress;
                    progressStatus.textContent = '처리를 완료하고 있습니다...';
                    clearInterval(scriptProgressInterval);
                }

                updateScriptProgressBar(scriptCurrentProgress);
            }, interval);
        }

        // 프로그레스바 업데이트 (스크립트용)
        function updateScriptProgressBar(percent) {
            const progressBar = document.getElementById('progress-bar');
            const progressText = document.getElementById('progress-text');

            const displayPercent = Math.min(Math.round(percent), 99);
            progressBar.style.width = displayPercent + '%';
            progressText.textContent = displayPercent + '%';
        }

        // 프로그레스바 완료 (스크립트용)
        function completeScriptProgress() {
            clearInterval(scriptProgressInterval);

            const progressBar = document.getElementById('progress-bar');
            const progressText = document.getElementById('progress-text');
            const progressStatus = document.getElementById('progress-status');

            scriptCurrentProgress = 100;
            progressBar.style.width = '100%';
            progressText.textContent = '100%';
            progressStatus.textContent = '완료! 페이지를 이동합니다...';
        }

        // 프로그레스바 숨기기 (스크립트용)
        function hideScriptProgressBar() {
            clearInterval(scriptProgressInterval);
            const progressModal = document.getElementById('progress-modal');
            progressModal.classList.remove('active');
            scriptCurrentProgress = 0;
        }
    }
});