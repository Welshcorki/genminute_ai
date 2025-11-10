document.addEventListener('DOMContentLoaded', () => {
    // === 업로드 중복 방지 (Phase 1) ===
    checkUploadStatus();

    // --- Chatbot Toggle 기능 ---
    const chatbotToggleTab = document.getElementById('chatbot-toggle-tab');
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

    // 챗봇 탭 클릭 이벤트
    if (chatbotToggleTab) {
        chatbotToggleTab.addEventListener('click', openChatbot);
    }

    // 챗봇 열기 함수
    function openChatbot() {
        chatbotSidebar.classList.add('open');
        chatbotToggleTab.classList.add('hidden');
        if (appContainer) {
            appContainer.classList.add('chatbot-open');
        }
        // 챗봇 열림 상태 저장
        sessionStorage.setItem(CHATBOT_STATE_KEY, 'open');
    }

    // 챗봇 닫기 함수
    function closeChatbot() {
        chatbotSidebar.classList.remove('open');
        chatbotToggleTab.classList.remove('hidden');
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

        // 명시적으로 닫힌 상태가 아니면 열린 상태로 시작 (기본값: 열림)
        if (savedState !== 'closed') {
            // transition 비활성화 (애니메이션 방지)
            chatbotSidebar.classList.add('no-transition');
            if (appContainer) {
                appContainer.classList.add('no-transition');
            }

            // 챗봇 열기
            chatbotSidebar.classList.add('open');
            chatbotToggleTab.classList.add('hidden');
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

            // 처음 로그인이면 'open' 상태 저장
            if (!savedState) {
                sessionStorage.setItem(CHATBOT_STATE_KEY, 'open');
                console.log('✅ 챗봇 기본 열림 상태로 시작');
            } else {
                console.log('✅ 챗봇 열림 상태 복원 (애니메이션 없음)');
            }
        } else {
            // 명시적으로 닫힌 상태인 경우에만 닫힌 상태 유지
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

    // 전송 중 상태 플래그
    let isSending = false;

    // 메시지 전송 함수
    async function sendChatMessage() {
        const message = chatbotInput.value.trim();
        if (!message) return;

        // 이미 전송 중이면 무시
        if (isSending) {
            console.log('⚠️ 이미 메시지를 전송 중입니다.');
            return;
        }

        // 전송 중 상태로 변경
        isSending = true;

        // 입력 필드와 버튼 비활성화
        chatbotInput.disabled = true;
        chatbotSendBtn.disabled = true;
        chatbotSendBtn.style.opacity = '0.5';
        chatbotSendBtn.style.cursor = 'not-allowed';

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

                // 출처 정보 표시 제거 (필요시 아래 주석 해제)
                // if (data.sources && data.sources.length > 0) {
                //     const sourcesText = formatSources(data.sources);
                //     addChatMessage('assistant', sourcesText, true); // 작은 글씨로 표시
                // }
            } else {
                addChatMessage('assistant', `오류: ${data.error || '알 수 없는 오류가 발생했습니다.'}`);
            }
        } catch (error) {
            console.error('챗봇 API 호출 오류:', error);
            loadingMsg.remove();
            addChatMessage('assistant', '죄송합니다. 서버와 통신 중 오류가 발생했습니다. 다시 시도해 주세요.');
        } finally {
            // 전송 완료 - UI 재활성화
            isSending = false;
            chatbotInput.disabled = false;
            chatbotSendBtn.disabled = false;
            chatbotSendBtn.style.opacity = '1';
            chatbotSendBtn.style.cursor = 'pointer';
            chatbotInput.focus(); // 입력 필드에 포커스
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

            // 최근 50개 메시지만 유지 (용량 절약)
            if (history.messages.length > 50) {
                history.messages = history.messages.slice(-50);
            }

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
        // 폼 제출 시 SSE로 실시간 상태 수신
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

            // === 중복 방지: 업로드 시작 ===
            sessionStorage.setItem('upload_in_progress', 'true');
            sessionStorage.setItem('upload_start_time', Date.now().toString());

            // 새로고침 경고 설정
            window.addEventListener('beforeunload', beforeUnloadHandler);

            // FormData 생성 (UI 비활성화 전에 먼저 생성!)
            const formData = new FormData(uploadForm);

            // UI 비활성화 (FormData 생성 후)
            disableUploadUI();

            // 진행 모달 표시
            const progressModal = document.getElementById('progress-modal');
            if (progressModal) {
                progressModal.classList.add('active');
            }

            // 업로드 단계 즉시 활성화 (SSE 메시지 없이도 표시)
            const stepUpload = document.getElementById('step-upload');
            if (stepUpload) {
                stepUpload.classList.add('active');
            }

            // SSE로 업로드 요청
            try {
                // 일반 fetch로 먼저 시작 (파일 업로드)
                const response = await fetch(uploadForm.action, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok || !response.headers.get('content-type')?.includes('text/event-stream')) {
                    throw new Error('서버에서 올바른 응답을 받지 못했습니다.');
                }

                // EventSource는 GET만 지원하므로, fetch의 ReadableStream 사용
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n\n');
                    buffer = lines.pop() || ''; // 마지막 불완전한 줄은 buffer에 유지

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = JSON.parse(line.substring(6));
                            handleSSEMessage(data);
                        }
                    }
                }

            } catch (error) {
                console.error('업로드 중 오류:', error);

                // 모달에 오류 표시 (handleSSEMessage의 error 케이스와 동일한 방식)
                handleSSEMessage({
                    step: 'error',
                    message: '서버와 통신 중 오류가 발생했습니다. 다시 시도해 주세요.'
                });
            }
        });

        // SSE 메시지 처리 함수
        function handleSSEMessage(data) {
            const progressStatus = document.getElementById('progress-status');
            const progressIcon = document.getElementById('progress-icon');
            const stepUpload = document.getElementById('step-upload');
            const stepSTT = document.getElementById('step-stt');
            const stepSummary = document.getElementById('step-summary');
            const stepMindmap = document.getElementById('step-mindmap');

            // 모든 단계의 active만 제거 (completed는 유지!)
            [stepUpload, stepSTT, stepSummary, stepMindmap].forEach(el => {
                if (el) el.classList.remove('active');
            });

            // 현재 단계 업데이트
            switch (data.step) {
                case 'upload':
                    if (progressIcon) progressIcon.textContent = data.icon || '📤';
                    if (progressStatus) progressStatus.textContent = data.message;
                    if (stepUpload) stepUpload.classList.add('active');
                    break;

                case 'stt':
                    if (progressIcon) progressIcon.textContent = data.icon || '🎤';
                    if (progressStatus) progressStatus.textContent = data.message;
                    // 이전 단계들 completed 설정
                    if (stepUpload) stepUpload.classList.add('completed');
                    if (stepSTT) stepSTT.classList.add('active');
                    break;

                case 'summary':
                    if (progressIcon) progressIcon.textContent = data.icon || '📝';
                    if (progressStatus) progressStatus.textContent = data.message;
                    // 이전 단계들 completed 설정
                    if (stepUpload) stepUpload.classList.add('completed');
                    if (stepSTT) stepSTT.classList.add('completed');
                    if (stepSummary) stepSummary.classList.add('active');
                    break;

                case 'mindmap':
                    if (progressIcon) progressIcon.textContent = data.icon || '🗺️';
                    if (progressStatus) progressStatus.textContent = data.message;
                    // 이전 단계들 completed 설정
                    if (stepUpload) stepUpload.classList.add('completed');
                    if (stepSTT) stepSTT.classList.add('completed');
                    if (stepSummary) stepSummary.classList.add('completed');
                    if (stepMindmap) stepMindmap.classList.add('active');
                    break;

                case 'complete':
                    if (progressIcon) progressIcon.textContent = data.icon || '✅';
                    if (progressStatus) progressStatus.textContent = data.message;
                    // 모든 단계 completed 설정
                    if (stepUpload) stepUpload.classList.add('completed');
                    if (stepSTT) stepSTT.classList.add('completed');
                    if (stepSummary) stepSummary.classList.add('completed');
                    if (stepMindmap) stepMindmap.classList.add('completed');

                    // === 중복 방지: 업로드 완료 ===
                    sessionStorage.removeItem('upload_in_progress');
                    sessionStorage.removeItem('upload_start_time');
                    window.removeEventListener('beforeunload', beforeUnloadHandler);

                    // 1초 후 페이지 이동
                    setTimeout(() => {
                        window.location.href = data.redirect;
                    }, 1000);
                    break;

                case 'error':
                    // 오류 메시지를 모달 안에 표시
                    if (progressIcon) progressIcon.textContent = '❌';
                    if (progressStatus) {
                        progressStatus.textContent = data.message || '업로드 중 오류가 발생했습니다.';
                        progressStatus.style.color = '#e74c3c';
                        progressStatus.style.fontWeight = 'bold';
                    }

                    // 스피너 숨기기
                    const spinner = document.querySelector('.spinner');
                    if (spinner) spinner.style.display = 'none';

                    // 단계 표시 숨기기
                    const stepIndicator = document.querySelector('.step-indicator');
                    if (stepIndicator) stepIndicator.style.display = 'none';

                    // 팁 메시지를 버튼으로 교체
                    const progressTip = document.querySelector('.progress-tip');
                    if (progressTip) {
                        progressTip.innerHTML = `
                            <div style="display: flex; gap: 1rem; justify-content: center; margin-top: 2rem;">
                                <button id="error-retry-btn" class="btn-primary" style="padding: 0.75rem 2rem; min-width: 120px;">다시 시도</button>
                                <button id="error-close-btn" class="btn-secondary" style="padding: 0.75rem 2rem; min-width: 120px;">닫기</button>
                            </div>
                        `;

                        // 닫기 버튼 이벤트
                        document.getElementById('error-close-btn').addEventListener('click', () => {
                            const progressModal = document.getElementById('progress-modal');
                            if (progressModal) {
                                progressModal.classList.remove('active');
                            }

                            // === 중복 방지: 업로드 실패 ===
                            sessionStorage.removeItem('upload_in_progress');
                            sessionStorage.removeItem('upload_start_time');
                            window.removeEventListener('beforeunload', beforeUnloadHandler);

                            enableUploadUI();

                            // 모달 초기화
                            resetProgressModal();
                        });

                        // 다시 시도 버튼 이벤트
                        document.getElementById('error-retry-btn').addEventListener('click', () => {
                            const progressModal = document.getElementById('progress-modal');
                            if (progressModal) {
                                progressModal.classList.remove('active');
                            }

                            // === 중복 방지: 업로드 실패 ===
                            sessionStorage.removeItem('upload_in_progress');
                            sessionStorage.removeItem('upload_start_time');
                            window.removeEventListener('beforeunload', beforeUnloadHandler);

                            enableUploadUI();

                            // 모달 초기화
                            resetProgressModal();

                            // 폼 자동 재제출
                            setTimeout(() => {
                                uploadForm.dispatchEvent(new Event('submit'));
                            }, 300);
                        });
                    }
                    break;
            }
        }

        // 모달 초기화 함수
        function resetProgressModal() {
            // 아이콘 초기화
            const progressIcon = document.getElementById('progress-icon');
            if (progressIcon) progressIcon.textContent = '📤';

            // 상태 메시지 초기화
            const progressStatus = document.getElementById('progress-status');
            if (progressStatus) {
                progressStatus.textContent = '파일을 업로드하고 있습니다...';
                progressStatus.style.color = '';
                progressStatus.style.fontWeight = '';
            }

            // 스피너 다시 표시
            const spinner = document.querySelector('.spinner');
            if (spinner) spinner.style.display = '';

            // 단계 표시 다시 표시
            const stepIndicator = document.querySelector('.step-indicator');
            if (stepIndicator) stepIndicator.style.display = '';

            // 팁 메시지 복원
            const progressTip = document.querySelector('.progress-tip');
            if (progressTip) {
                progressTip.innerHTML = '잠시만 기다려주세요';
                progressTip.style.color = '';
            }

            // 모든 단계 초기화
            const steps = document.querySelectorAll('.step');
            steps.forEach(step => {
                step.classList.remove('active', 'completed');
            });
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

            // === 중복 방지: 스크립트 처리 시작 ===
            sessionStorage.setItem('upload_in_progress', 'true');
            sessionStorage.setItem('upload_start_time', Date.now().toString());

            // 새로고침 경고 설정
            window.addEventListener('beforeunload', beforeUnloadHandler);

            // FormData 생성 (먼저 생성)
            const formData = new FormData(scriptForm);

            // 프로그레스바 시작
            startScriptProgressBar();

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

                    // === 중복 방지: 처리 완료 ===
                    sessionStorage.removeItem('upload_in_progress');
                    sessionStorage.removeItem('upload_start_time');
                    window.removeEventListener('beforeunload', beforeUnloadHandler);

                    // 1초 후 페이지 이동
                    setTimeout(() => {
                        window.location.href = result.redirect_url || `/view/${result.meeting_id}`;
                    }, 1000);
                } else {
                    const error = await response.json();

                    // === 중복 방지: 처리 실패 ===
                    sessionStorage.removeItem('upload_in_progress');
                    sessionStorage.removeItem('upload_start_time');
                    window.removeEventListener('beforeunload', beforeUnloadHandler);

                    hideScriptProgressBar();
                    alert(`오류 발생: ${error.error || '알 수 없는 오류'}`);
                }
            } catch (error) {
                console.error('스크립트 처리 중 오류:', error);

                // === 중복 방지: 처리 실패 ===
                sessionStorage.removeItem('upload_in_progress');
                sessionStorage.removeItem('upload_start_time');
                window.removeEventListener('beforeunload', beforeUnloadHandler);

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

    // ==================== 중복 업로드 방지 헬퍼 함수 ====================

    // 페이지 로드 시 업로드 상태 체크
    async function checkUploadStatus() {
        const uploadInProgress = sessionStorage.getItem('upload_in_progress');
        const uploadStartTime = sessionStorage.getItem('upload_start_time');

        if (!uploadInProgress) {
            return; // 진행 중인 업로드 없음
        }

        // 10분 이상 지난 경우 타임아웃 처리
        const startTime = parseInt(uploadStartTime || '0');
        const currentTime = Date.now();
        const TEN_MINUTES = 10 * 60 * 1000;

        if (currentTime - startTime > TEN_MINUTES) {
            console.log('⏰ 업로드 타임아웃 (10분 경과) - 플래그 제거');
            sessionStorage.removeItem('upload_in_progress');
            sessionStorage.removeItem('upload_start_time');
            return;
        }

        // 실제로 새 노트가 생성되었는지 확인 (최근 5분 이내)
        try {
            const fiveMinutesAgo = Date.now() - (5 * 60 * 1000);
            const response = await fetch('/notes_json');

            if (response.ok) {
                const data = await response.json();

                // 최근 생성된 노트가 있는지 확인
                if (data.meetings && data.meetings.length > 0) {
                    const latestMeeting = data.meetings[0];
                    const meetingTime = new Date(latestMeeting.meeting_date).getTime();

                    // upload_start_time 이후에 생성된 노트가 있으면 작업 완료된 것
                    if (meetingTime >= startTime) {
                        console.log('✅ 업로드 작업 완료 확인 - 플래그 제거');
                        sessionStorage.removeItem('upload_in_progress');
                        sessionStorage.removeItem('upload_start_time');

                        // 완료된 노트로 자동 이동
                        window.location.href = `/view/${latestMeeting.meeting_id}`;
                        return;
                    }
                }
            }
        } catch (error) {
            console.error('노트 확인 중 오류:', error);
        }

        // 업로드 진행 중 - UI 잠금
        console.log('⚠️ 업로드 진행 중 감지 - UI 잠금');
        showUploadInProgressWarning();
    }

    // 업로드 진행 중 경고 UI 표시
    function showUploadInProgressWarning() {
        const dropZone = document.getElementById('drop-zone');
        if (!dropZone) return;

        // 기존 UI 숨기기
        dropZone.style.display = 'none';

        // 경고 메시지 생성
        const warningDiv = document.createElement('div');
        warningDiv.id = 'upload-warning';
        warningDiv.style.cssText = `
            padding: 3rem;
            text-align: center;
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 12px;
            margin: 2rem auto;
            max-width: 600px;
        `;

        warningDiv.innerHTML = `
            <div style="font-size: 3rem; margin-bottom: 1rem;">⚠️</div>
            <h2 style="color: #856404; margin-bottom: 1rem;">이미 노트를 생성 중입니다</h2>
            <p style="color: #856404; margin-bottom: 2rem;">
                이전에 업로드한 파일이 처리 중입니다.<br>
                완료될 때까지 기다려주세요.
            </p>
            <div style="display: flex; gap: 1rem; justify-content: center;">
                <button id="force-cancel-btn" class="btn-secondary" style="padding: 0.75rem 2rem; font-size: 1rem;">
                    강제 취소 (다시 업로드)
                </button>
            </div>
        `;

        dropZone.parentElement.insertBefore(warningDiv, dropZone);

        // 강제 취소 버튼 이벤트
        document.getElementById('force-cancel-btn').addEventListener('click', () => {
            if (confirm('정말로 이전 작업을 취소하고 새로 시작하시겠습니까?\n서버에서 처리 중인 작업은 계속 진행될 수 있습니다.')) {
                sessionStorage.removeItem('upload_in_progress');
                sessionStorage.removeItem('upload_start_time');
                warningDiv.remove();
                dropZone.style.display = '';
                enableUploadUI();
            }
        });
    }

    // 새로고침/페이지 이탈 경고
    function beforeUnloadHandler(e) {
        e.preventDefault();
        e.returnValue = '노트를 생성 중입니다. 페이지를 나가면 작업이 취소될 수 있습니다.';
        return e.returnValue;
    }

    // UI 비활성화
    function disableUploadUI() {
        const dropZone = document.getElementById('drop-zone');
        const uploadButton = document.getElementById('upload-button');
        const fileInput = document.getElementById('audio-file-input');
        const submitButton = document.getElementById('submit-button');
        const titleInput = document.querySelector('input[name="title"]');

        if (dropZone) dropZone.style.pointerEvents = 'none';
        if (dropZone) dropZone.style.opacity = '0.5';
        if (uploadButton) uploadButton.disabled = true;
        if (fileInput) fileInput.disabled = true;
        if (submitButton) submitButton.disabled = true;
        if (titleInput) titleInput.disabled = true;
    }

    // UI 재활성화
    function enableUploadUI() {
        const dropZone = document.getElementById('drop-zone');
        const uploadButton = document.getElementById('upload-button');
        const fileInput = document.getElementById('audio-file-input');
        const submitButton = document.getElementById('submit-button');
        const titleInput = document.querySelector('input[name="title"]');

        if (dropZone) dropZone.style.pointerEvents = '';
        if (dropZone) dropZone.style.opacity = '';
        if (uploadButton) uploadButton.disabled = false;
        if (fileInput) fileInput.disabled = false;
        if (submitButton) submitButton.disabled = false;
        if (titleInput) titleInput.disabled = false;
    }
});