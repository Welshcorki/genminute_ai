
document.addEventListener('DOMContentLoaded', () => {
    const retrieverForm = document.getElementById('retriever-form');
    const resultsArea = document.getElementById('results-area');

    if (retrieverForm) {
        retrieverForm.addEventListener('submit', async (event) => {
            event.preventDefault();

            const formData = new FormData(retrieverForm);
            const query = formData.get('query');
            const db_type = formData.get('db_type');
            const retriever_type = formData.get('retriever_type'); // Get the new retriever type
            const submitButton = retrieverForm.querySelector('button[type="submit"]');

            // 로딩 상태 표시
            resultsArea.innerHTML = '<p>검색 중...</p>';
            submitButton.disabled = true;
            submitButton.textContent = '검색 중...';

            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query, db_type, retriever_type }), // Include retriever_type
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    displayResults(data.results);
                } else {
                    throw new Error(data.error || '알 수 없는 오류가 발생했습니다.');
                }

            } catch (error) {
                resultsArea.innerHTML = `<p class="error-message">오류: ${error.message}</p>`;
            } finally {
                // 로딩 상태 해제
                submitButton.disabled = false;
                submitButton.textContent = '검색';
            }
        });
    }

    function displayResults(results) {
        resultsArea.innerHTML = ''; // 기존 결과 삭제

        if (!results || results.length === 0) {
            resultsArea.innerHTML = '<p>일치하는 검색 결과가 없습니다.</p>';
            return;
        }

        const resultHeader = document.createElement('h3');
        resultHeader.textContent = `✅ 검색 결과 (${results.length}개)`;
        resultsArea.appendChild(resultHeader);

        results.forEach(result => {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';

            const content = document.createElement('p');
            content.textContent = result.page_content;

            const metadata = document.createElement('pre');
            metadata.className = 'result-metadata';
            metadata.textContent = JSON.stringify(result.metadata, null, 2);

            resultItem.appendChild(content);
            resultItem.appendChild(metadata);
            resultsArea.appendChild(resultItem);
        });
    }
});
