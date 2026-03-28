/* auto-iros 공통 JS 유틸리티 */

/**
 * POST JSON 요청
 */
async function apiPost(url, data) {
    const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    return res.json();
}

/**
 * POST 파일 업로드
 */
async function apiUpload(url, file) {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(url, { method: 'POST', body: form });
    return res.json();
}

/**
 * 로딩 오버레이 표시/숨김
 */
function showLoading(message = 'API 요청 중...') {
    if (document.getElementById('loading-overlay')) return;
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.className = 'overlay';
    overlay.innerHTML = `
        <div class="overlay-content">
            <div class="spinner mb-3"></div>
            <p class="text-gray-600">${message}</p>
        </div>
    `;
    document.body.appendChild(overlay);
}

function hideLoading() {
    const el = document.getElementById('loading-overlay');
    if (el) el.remove();
}

/**
 * 알림 메시지 표시
 */
function showAlert(container, message, type = 'error') {
    const colors = {
        error: 'bg-red-50 text-red-700 border-red-200',
        success: 'bg-green-50 text-green-700 border-green-200',
        info: 'bg-blue-50 text-blue-700 border-blue-200',
    };
    container.innerHTML = `
        <div class="p-4 rounded border ${colors[type] || colors.info} mb-4">
            ${message}
        </div>
    `;
}

/**
 * 주소 목록 테이블 생성
 */
function renderAddressTable(addrList, options = {}) {
    const { onSelect, onQuery } = options;
    if (!addrList || addrList.length === 0) {
        return '<p class="text-gray-500">검색 결과가 없습니다.</p>';
    }

    let html = `
        <table class="w-full text-sm border-collapse">
            <thead>
                <tr class="bg-gray-50 border-b">
                    <th class="text-left p-2 w-10">#</th>
                    <th class="text-left p-2">주소</th>
                    <th class="text-left p-2 w-40">고유번호</th>
                    <th class="text-left p-2 w-24">부동산구분</th>
                    ${onSelect || onQuery ? '<th class="p-2 w-20"></th>' : ''}
                </tr>
            </thead>
            <tbody>
    `;

    addrList.forEach((addr, i) => {
        const address = addr.address || addr.resAddr || '';
        const uniqueNo = addr.uniqueNo || '';
        const realtyType = addr.realtyType || '';
        html += `
            <tr class="border-b hover:bg-gray-50">
                <td class="p-2 text-gray-400">${i + 1}</td>
                <td class="p-2">${address}</td>
                <td class="p-2 font-mono text-xs">${uniqueNo}</td>
                <td class="p-2">${realtyType}</td>
        `;
        if (onSelect) {
            html += `<td class="p-2"><button onclick="${onSelect}(${i})" class="text-blue-600 hover:underline text-xs">선택</button></td>`;
        } else if (onQuery) {
            html += `<td class="p-2"><a href="/single?unique_no=${encodeURIComponent(uniqueNo)}" class="text-blue-600 hover:underline text-xs">조회</a></td>`;
        }
        html += '</tr>';
    });

    html += '</tbody></table>';
    return html;
}
