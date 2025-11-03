
document.addEventListener('DOMContentLoaded', () => {
    const audioPlayer = document.getElementById('audio-player');
    const transcriptContainer = document.getElementById('transcript-container');
    const summaryContainer = document.getElementById('summary-container');
    const minutesContainer = document.getElementById('minutes-container');
    const meetingTitle = document.getElementById('meeting-title');

    let segments = [];
    let currentSegmentIndex = -1;
    let summaryGenerated = false; // 요약 생성 여부 추적
    let minutesGenerated = false; // 회의록 생성 여부 추적

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

            // 회의록 탭을 클릭했을 때 회의록 조회
            if (targetTab === 'minutes' && !minutesGenerated) {
                checkAndDisplayMinutes();
            }
        });
    });

    // 데이터 가져오기 및 뷰어 설정
    async function initializeViewer() {
        if (typeof MEETING_ID === 'undefined' || !MEETING_ID) {
            showError('회의 ID를 찾을 수 없습니다.');
            return;
        }

        try {
            const response = await fetch(`/api/meeting/${MEETING_ID}`);
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || '데이터를 불러오는 데 실패했습니다.');
            }

            // 데이터로 뷰어 설정
            segments = data.transcript;
            meetingTitle.textContent = data.title;
            audioPlayer.src = data.audio_url;

            renderTranscript(segments);

            // 문단 요약 존재 여부 확인 및 표시
            await checkAndDisplaySummary();

            // 회의록 존재 여부 확인 및 표시
            await checkAndDisplayMinutes();

        } catch (error) {
            showError(error.message);
        }
    }

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

    // 회의록 존재 여부 확인 및 자동 표시
    async function checkAndDisplayMinutes() {
        try {
            const response = await fetch(`/api/get_minutes/${MEETING_ID}`);
            const data = await response.json();

            if (data.success && data.has_minutes) {
                // 회의록이 이미 존재하면 자동으로 표시
                displayMinutes(data.minutes);
                minutesGenerated = true;

                // 회의록 컨테이너를 업데이트 (버튼 숨기기)
                console.log('✅ 기존 회의록을 불러왔습니다.');
            } else {
                console.log('ℹ️ 회의록이 아직 생성되지 않았습니다.');
            }
        } catch (error) {
            console.error('회의록 조회 중 오류:', error);
            // 오류가 발생해도 계속 진행 (필수 기능 아님)
        }
    }

    // 회의록 렌더링
    function renderTranscript(segments) {
        transcriptContainer.innerHTML = '';
        segments.forEach((segment, index) => {
            const segDiv = document.createElement('div');
            segDiv.className = 'segment-block';
            segDiv.dataset.startTime = segment.start_time;
            segDiv.dataset.index = index;

            const time = new Date(segment.start_time * 1000).toISOString().substr(14, 5);

            segDiv.innerHTML = `
                <div class="segment-block-header">
                    <span class="segment-speaker">Speaker ${segment.speaker_label}</span>
                    <span class="segment-time">${time}</span>
                </div>
                <p class="segment-block-text">${segment.segment}</p>
            `;

            // 클릭 시 해당 시간으로 이동 및 재생
            segDiv.addEventListener('click', () => {
                audioPlayer.currentTime = segment.start_time;
                audioPlayer.play();
            });

            transcriptContainer.appendChild(segDiv);
        });
    }

    // 오디오 재생에 맞춰 하이라이트
    audioPlayer.addEventListener('timeupdate', () => {
        const currentTime = audioPlayer.currentTime;
        let newSegmentIndex = -1;

        for (let i = 0; i < segments.length; i++) {
            const segment = segments[i];
            const nextSegment = segments[i + 1];
            const startTime = segment.start_time;
            const endTime = nextSegment ? nextSegment.start_time : audioPlayer.duration;

            if (currentTime >= startTime && currentTime < endTime) {
                newSegmentIndex = i;
                break;
            }
        }

        if (newSegmentIndex !== currentSegmentIndex) {
            currentSegmentIndex = newSegmentIndex;
            highlightSegment(currentSegmentIndex);
        }
    });

    // 세그먼트 하이라이트 함수
    function highlightSegment(index) {
        const segmentBlocks = document.querySelectorAll('.segment-block');
        segmentBlocks.forEach((block, i) => {
            if (i === index) {
                block.classList.add('current');
                block.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } else {
                block.classList.remove('current');
            }
        });
    }

    // 오류 메시지 표시
    function showError(message) {
        transcriptContainer.innerHTML = `<p class="error-message">오류: ${message}</p>`;
    }

    initializeViewer();

    // 요약하기 버튼 이벤트 리스너
    const summarizeButton = document.getElementById('summarize-button');
    if (summarizeButton) {
        summarizeButton.addEventListener('click', async () => {
            if (typeof MEETING_ID === 'undefined' || !MEETING_ID) {
                alert('회의 ID를 찾을 수 없습니다.');
                return;
            }

            if (!confirm('회의 내용을 요약하시겠습니까? 요약에는 시간이 소요될 수 있습니다.')) {
                return;
            }

            try {
                // 버튼 비활성화 및 로딩 표시
                summarizeButton.disabled = true;
                summarizeButton.textContent = '요약 중...';

                // 요약 컨테이너에 로딩 메시지 표시
                summaryContainer.innerHTML = '<div class="summary-loading">요약을 생성하는 중입니다. 잠시만 기다려주세요...</div>';

                // 문단 요약 탭으로 자동 전환
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                document.querySelector('[data-tab="summary"]').classList.add('active');
                document.getElementById('summary-tab').classList.add('active');

                const response = await fetch(`/api/summarize/${MEETING_ID}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });

                const data = await response.json();

                if (data.success) {
                    // 요약 내용을 마크다운에서 HTML로 변환하여 표시
                    displaySummary(data.summary);
                    summaryGenerated = true; // 요약 생성 완료 표시

                    // 회의록 탭에서 회의록 생성 버튼 활성화
                    updateMinutesTab();

                    alert('요약이 성공적으로 생성되었습니다!');
                } else {
                    summaryContainer.innerHTML = `<div class="summary-error">요약 실패: ${data.error}</div>`;
                    alert(`요약 실패: ${data.error}`);
                }
            } catch (error) {
                console.error('요약 요청 중 오류 발생:', error);
                summaryContainer.innerHTML = '<div class="summary-error">요약 요청 중 오류가 발생했습니다.</div>';
                alert('요약 요청 중 오류가 발생했습니다.');
            } finally {
                // 버튼 다시 활성화
                summarizeButton.disabled = false;
                summarizeButton.textContent = '요약하기';
            }
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

    // 회의록 탭 업데이트 함수
    function updateMinutesTab() {
        const generateMinutesButton = document.getElementById('generate-minutes-button');

        if (summaryGenerated) {
            // 요약이 생성되었으면 회의록 생성 버튼 표시
            minutesContainer.innerHTML = `
                <p class="minutes-placeholder">회의록 생성 버튼을 눌러 정식 회의록을 작성하세요.</p>
                <button id="generate-minutes-button" class="btn-primary" style="margin-top: 1rem;">회의록 생성</button>
            `;

            // 버튼 이벤트 리스너 다시 추가
            attachMinutesButtonListener();
        }
    }

    // 회의록 생성 버튼 이벤트 리스너
    function attachMinutesButtonListener() {
        const generateMinutesButton = document.getElementById('generate-minutes-button');

        if (generateMinutesButton) {
            generateMinutesButton.addEventListener('click', async () => {
                if (typeof MEETING_ID === 'undefined' || !MEETING_ID) {
                    alert('회의 ID를 찾을 수 없습니다.');
                    return;
                }

                if (!summaryGenerated) {
                    alert('먼저 "요약하기" 버튼을 눌러 문단 요약을 생성해주세요.');
                    return;
                }

                if (!confirm('회의록을 생성하시겠습니까? 생성에는 시간이 소요될 수 있습니다.')) {
                    return;
                }

                try {
                    // 버튼 비활성화 및 로딩 표시
                    generateMinutesButton.disabled = true;
                    generateMinutesButton.textContent = '회의록 생성 중...';

                    // 회의록 컨테이너에 로딩 메시지 표시
                    minutesContainer.innerHTML = '<div class="minutes-loading">회의록을 생성하는 중입니다. 잠시만 기다려주세요...</div>';

                    const response = await fetch(`/api/generate_minutes/${MEETING_ID}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                    });

                    const data = await response.json();

                    if (data.success) {
                        // 회의록 내용을 마크다운에서 HTML로 변환하여 표시
                        displayMinutes(data.minutes);
                        minutesGenerated = true; // 회의록 생성 완료 표시
                        alert('회의록이 성공적으로 생성 및 저장되었습니다!');
                    } else {
                        minutesContainer.innerHTML = `<div class="minutes-error">회의록 생성 실패: ${data.error}</div>`;
                        // 버튼 다시 표시
                        updateMinutesTab();
                        alert(`회의록 생성 실패: ${data.error}`);
                    }
                } catch (error) {
                    console.error('회의록 생성 중 오류 발생:', error);
                    minutesContainer.innerHTML = '<div class="minutes-error">회의록 생성 중 오류가 발생했습니다.</div>';
                    // 버튼 다시 표시
                    updateMinutesTab();
                    alert('회의록 생성 중 오류가 발생했습니다.');
                }
            });
        }
    }

    // 회의록 내용 표시 함수
    function displayMinutes(minutesText) {
        // 마크다운 형식을 HTML로 변환
        let htmlContent = minutesText
            // # 제목 -> <h1>제목</h1>
            .replace(/^# (.+)$/gm, '<h1>$1</h1>')
            // ## 제목 -> <h2>제목</h2>
            .replace(/^## (.+)$/gm, '<h2>$1</h2>')
            // ### 제목 -> <h3>제목</h3>
            .replace(/^### (.+)$/gm, '<h3>$1</h3>')
            // **굵게** -> <strong>굵게</strong>
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            // 일반 텍스트를 <p>로 감싸기 (태그가 없는 줄)
            .replace(/^(?!<[h123]|<strong|<hr|$)(.+)$/gm, '<p>$1</p>')
            // --- -> <hr>
            .replace(/^---$/gm, '<hr>');

        minutesContainer.innerHTML = `<div class="minutes-content">${htmlContent}</div>`;
    }
});
