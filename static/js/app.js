// 전역 변수
let currentPage = 1;
let currentMonth = '';
let currentSearch = '';
let currentPassGubn = '';
let currentProcStage = '';
let currentSortBy = 'proposal_date';
let currentOrder = 'desc';
let totalPages = 1;
let searchTimeout = null;

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 앱 초기화
async function initializeApp() {
    try {
        // 통계 정보 로드
        await loadStats();
        
        // 월별 필터 옵션 로드
        await loadMonthOptions();
        
        // 처리구분 필터 옵션 로드
        await loadPassGubnOptions();
        
        // 진행단계 필터 옵션 로드
        await loadProcStageOptions();
        
        // 의안 목록 로드
        await loadBills();
        
        // 이벤트 리스너 설정
        setupEventListeners();
    } catch (error) {
        console.error('초기화 오류:', error);
        showError('데이터를 불러오는 중 오류가 발생했습니다.');
    }
}

// 통계 정보 로드
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // 통계 카드 업데이트
        const totalBills = data.total_bills;
        const pendingBills = data.pending_bills || 0;
        const processedBills = data.processed_bills || 0;
        const processedWithVotes = data.processed_with_votes || 0;
        const processedNoVotes = data.processed_no_votes || 0;
        
        document.getElementById('totalBills').textContent = formatNumber(totalBills);
        document.getElementById('pendingBills').textContent = formatNumber(pendingBills);
        document.getElementById('processedBills').textContent = formatNumber(processedBills);
        document.getElementById('processedWithVotes').textContent = formatNumber(processedWithVotes);
        document.getElementById('processedNoVotes').textContent = formatNumber(processedNoVotes);
        
        // 퍼센트 계산 및 표시
        const pendingPercent = totalBills > 0 ? ((pendingBills / totalBills) * 100).toFixed(1) : 0;
        const processedPercent = totalBills > 0 ? ((processedBills / totalBills) * 100).toFixed(1) : 0;
        const processedWithVotesPercent = processedBills > 0 ? ((processedWithVotes / processedBills) * 100).toFixed(1) : 0;
        const processedNoVotesPercent = processedBills > 0 ? ((processedNoVotes / processedBills) * 100).toFixed(1) : 0;
        
        document.getElementById('pendingBillsPercent').textContent = `${pendingPercent}%`;
        document.getElementById('processedBillsPercent').textContent = `${processedPercent}%`;
        document.getElementById('processedWithVotesPercent').textContent = `${processedWithVotesPercent}%`;
        document.getElementById('processedNoVotesPercent').textContent = `${processedNoVotesPercent}%`;
        
        // 진행단계별 통계 표시
        if (data.proc_stage_stats) {
            displayProcStageStats(data.proc_stage_stats, totalBills);
        }
    } catch (error) {
        console.error('통계 로드 오류:', error);
    }
}


// 월별 필터 옵션 로드
async function loadMonthOptions() {
    try {
        const response = await fetch('/api/months');
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        const monthFilter = document.getElementById('monthFilter');
        data.months.forEach(month => {
            const option = document.createElement('option');
            option.value = month.month;
            option.textContent = `${month.month_label} (${formatNumber(month.bill_count)}건)`;
            monthFilter.appendChild(option);
        });
    } catch (error) {
        console.error('월 목록 로드 오류:', error);
    }
}

// 처리구분 필터 옵션 로드
async function loadPassGubnOptions() {
    try {
        const response = await fetch('/api/pass_gubn_options');
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        const passGubnFilter = document.getElementById('passGubnFilter');
        data.options.forEach(option => {
            const opt = document.createElement('option');
            opt.value = option.pass_gubn;
            opt.textContent = `${option.pass_gubn} (${formatNumber(option.bill_count || option.count || 0)}건)`;
            passGubnFilter.appendChild(opt);
        });
    } catch (error) {
        console.error('처리구분 필터 옵션 로드 오류:', error);
    }
}

// 진행단계 필터 옵션 로드
async function loadProcStageOptions() {
    try {
        const response = await fetch('/api/proc_stage_options');
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        const procStageFilter = document.getElementById('procStageFilter');
        
        // 주요 진행단계 순서 정의
        const mainStages = ['접수', '소관위접수', '소관위심사', '본회의의결', '공포', '정부이송', '대안반영폐기', '철회'];
        
        // 주요 단계 먼저 추가
        mainStages.forEach(stage => {
            const option = data.options.find(opt => opt.proc_stage_cd === stage);
            if (option) {
                const opt = document.createElement('option');
                opt.value = option.proc_stage_cd;
                opt.textContent = `${option.proc_stage_cd} (${formatNumber(option.bill_count || option.count || 0)}건)`;
                procStageFilter.appendChild(opt);
            }
        });
        
        // 나머지 단계 추가
        data.options.forEach(option => {
            if (!mainStages.includes(option.proc_stage_cd)) {
                const opt = document.createElement('option');
                opt.value = option.proc_stage_cd;
                opt.textContent = `${option.proc_stage_cd} (${formatNumber(option.bill_count || option.count || 0)}건)`;
                procStageFilter.appendChild(opt);
            }
        });
    } catch (error) {
        console.error('진행단계 필터 옵션 로드 오류:', error);
    }
}

// 의안 목록 로드
async function loadBills(page = 1) {
    showLoading(true);
    
    try {
        const params = new URLSearchParams({
            page: page,
            per_page: 20,
            sort_by: currentSortBy,
            order: currentOrder
        });
        
        if (currentMonth) {
            params.append('month', currentMonth);
        }
        
        if (currentSearch) {
            params.append('search', currentSearch);
        }
        
        if (currentPassGubn) {
            params.append('pass_gubn', currentPassGubn);
        }
        
        if (currentProcStage) {
            params.append('proc_stage', currentProcStage);
        }
        
        const response = await fetch(`/api/bills?${params.toString()}`);
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        currentPage = data.pagination.page;
        totalPages = data.pagination.pages;
        
        // 의안 카드 표시
        displayBills(data.bills);
        
        // 페이지네이션 표시
        displayPagination(data.pagination);
        
        // 활성 필터 표시 업데이트
        updateActiveFilters();
        
    } catch (error) {
        console.error('의안 목록 로드 오류:', error);
        showError('의안 목록을 불러오는 중 오류가 발생했습니다.');
    } finally {
        showLoading(false);
    }
}

// 의안 카드 표시
function displayBills(bills) {
    const container = document.getElementById('billsContainer');
    container.innerHTML = '';
    
    if (bills.length === 0) {
        let message = '표시할 의안이 없습니다.';
        if (currentSearch) {
            message = `"${escapeHtml(currentSearch)}"에 대한 검색 결과가 없습니다.`;
        }
        container.innerHTML = `<div style="text-align: center; padding: 40px; color: #7f8c8d;">${message}</div>`;
        return;
    }
    
    bills.forEach(bill => {
        const card = createBillCard(bill);
        container.appendChild(card);
    });
}

// 의안 카드 생성
function createBillCard(bill) {
    const card = document.createElement('div');
    card.className = `bill-card ${bill.vote_count > 0 ? 'has-votes' : 'no-votes'}`;
    card.onclick = () => showBillDetail(bill.bill_id);
    
    const proposalDate = bill.proposal_date ? formatDate(bill.proposal_date) : '미상';
    const procDate = bill.proc_date ? formatDate(bill.proc_date) : null;
    
    // 처리구분 및 진행단계 표시
    let statusBadge = '';
    if (bill.pass_gubn === '처리의안') {
        statusBadge = '<span class="bill-status processed">처리완료</span>';
    } else if (bill.pass_gubn === '계류의안') {
        statusBadge = '<span class="bill-status pending">계류중</span>';
    }
    
    // 진행단계 표시
    if (bill.proc_stage_cd) {
        statusBadge += ` <span class="bill-status" style="background: #f8f9fa; color: #6c757d; border: 1px solid #dee2e6; margin-left: 5px;">${escapeHtml(bill.proc_stage_cd)}</span>`;
    }
    
    let voteSection = '';
    if (bill.vote_count > 0) {
        const total = bill.vote_for + bill.vote_against + bill.vote_abstain + bill.vote_absent;
        const forPercent = total > 0 ? (bill.vote_for / total * 100).toFixed(1) : 0;
        const againstPercent = total > 0 ? (bill.vote_against / total * 100).toFixed(1) : 0;
        const abstainPercent = total > 0 ? (bill.vote_abstain / total * 100).toFixed(1) : 0;
        const absentPercent = total > 0 ? (bill.vote_absent / total * 100).toFixed(1) : 0;
        
        voteSection = `
            <div class="bill-votes">
                <div class="bill-votes-title">표결 결과 (${formatNumber(bill.member_count)}명 참여)</div>
                <div class="vote-bar">
                    ${bill.vote_for > 0 ? `<div class="vote-segment for" style="width: ${forPercent}%">${forPercent}%</div>` : ''}
                    ${bill.vote_against > 0 ? `<div class="vote-segment against" style="width: ${againstPercent}%">${againstPercent}%</div>` : ''}
                    ${bill.vote_abstain > 0 ? `<div class="vote-segment abstain" style="width: ${abstainPercent}%">${abstainPercent}%</div>` : ''}
                    ${bill.vote_absent > 0 ? `<div class="vote-segment absent" style="width: ${absentPercent}%">${absentPercent}%</div>` : ''}
                </div>
                <div class="vote-summary">
                    <span>찬성: ${formatNumber(bill.vote_for)}</span>
                    <span>반대: ${formatNumber(bill.vote_against)}</span>
                    <span>기권: ${formatNumber(bill.vote_abstain)}</span>
                    <span>불참: ${formatNumber(bill.vote_absent)}</span>
                </div>
            </div>
        `;
    } else {
        voteSection = '<div class="bill-votes"><div style="color: #95a5a6; text-align: center; padding: 20px;">표결 진행 전</div></div>';
    }
    
    card.innerHTML = `
        <div class="bill-header">
            <div class="bill-title">${escapeHtml(bill.title)}</div>
            <div class="bill-meta">
                <span class="bill-meta-item">📅 ${proposalDate}</span>
                ${bill.proposer_name ? `<span class="bill-meta-item">👤 ${escapeHtml(bill.proposer_name)}${bill.proposer_kind === '의원' ? ' 의원' : ''}</span>` : (bill.proposer_kind ? `<span class="bill-meta-item">👤 ${bill.proposer_kind}</span>` : '')}
                ${statusBadge}
            </div>
        </div>
        ${voteSection}
    `;
    
    return card;
}

// 의안 상세 정보 표시
async function showBillDetail(billId) {
    showLoading(true);
    
    try {
        const response = await fetch(`/api/bills/${billId}`);
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        displayBillModal(data);
    } catch (error) {
        console.error('의안 상세 조회 오류:', error);
        showError('의안 상세 정보를 불러오는 중 오류가 발생했습니다.');
    } finally {
        showLoading(false);
    }
}

// 의안 상세 모달 표시
function displayBillModal(bill) {
    const modal = document.getElementById('billModal');
    const modalBody = document.getElementById('modalBody');
    
    const proposalDate = bill.proposal_date ? formatDate(bill.proposal_date) : '미상';
    const procDate = bill.proc_date ? formatDate(bill.proc_date) : '미상';
    
    let voteSection = '';
    if (bill.vote_count > 0) {
        const total = bill.vote_for + bill.vote_against + bill.vote_abstain + bill.vote_absent;
        const forPercent = total > 0 ? (bill.vote_for / total * 100).toFixed(1) : 0;
        const againstPercent = total > 0 ? (bill.vote_against / total * 100).toFixed(1) : 0;
        const abstainPercent = total > 0 ? (bill.vote_abstain / total * 100).toFixed(1) : 0;
        const absentPercent = total > 0 ? (bill.vote_absent / total * 100).toFixed(1) : 0;
        
        voteSection = `
            <div class="modal-section">
                <h3>표결 결과 상세</h3>
                <div class="vote-bar" style="height: 40px; margin-bottom: 15px;">
                    ${bill.vote_for > 0 ? `<div class="vote-segment for" style="width: ${forPercent}%">찬성 ${forPercent}%</div>` : ''}
                    ${bill.vote_against > 0 ? `<div class="vote-segment against" style="width: ${againstPercent}%">반대 ${againstPercent}%</div>` : ''}
                    ${bill.vote_abstain > 0 ? `<div class="vote-segment abstain" style="width: ${abstainPercent}%">기권 ${abstainPercent}%</div>` : ''}
                    ${bill.vote_absent > 0 ? `<div class="vote-segment absent" style="width: ${absentPercent}%">불참 ${absentPercent}%</div>` : ''}
                </div>
                <div class="modal-info-grid">
                    <div class="modal-info-item">
                        <div class="modal-info-label">찬성</div>
                        <div class="modal-info-value">${formatNumber(bill.vote_for)}건</div>
                    </div>
                    <div class="modal-info-item">
                        <div class="modal-info-label">반대</div>
                        <div class="modal-info-value">${formatNumber(bill.vote_against)}건</div>
                    </div>
                    <div class="modal-info-item">
                        <div class="modal-info-label">기권</div>
                        <div class="modal-info-value">${formatNumber(bill.vote_abstain)}건</div>
                    </div>
                    <div class="modal-info-item">
                        <div class="modal-info-label">불참</div>
                        <div class="modal-info-value">${formatNumber(bill.vote_absent)}건</div>
                    </div>
                    <div class="modal-info-item">
                        <div class="modal-info-label">참여 의원</div>
                        <div class="modal-info-value">${formatNumber(bill.member_count)}명</div>
                    </div>
                    <div class="modal-info-item">
                        <div class="modal-info-label">총 표결 수</div>
                        <div class="modal-info-value">${formatNumber(bill.vote_count)}건</div>
                    </div>
                </div>
            </div>
        `;
        
        if (bill.party_votes && bill.party_votes.length > 0) {
            let partyTable = '<div class="modal-section"><h3>정당별 표결 결과</h3><table style="width: 100%; border-collapse: collapse; margin-top: 15px;"><thead><tr style="background: #f8f9fa;"><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e0e0e0;">정당</th><th style="padding: 10px; text-align: center; border-bottom: 2px solid #e0e0e0;">찬성</th><th style="padding: 10px; text-align: center; border-bottom: 2px solid #e0e0e0;">반대</th><th style="padding: 10px; text-align: center; border-bottom: 2px solid #e0e0e0;">기권</th><th style="padding: 10px; text-align: center; border-bottom: 2px solid #e0e0e0;">불참</th></tr></thead><tbody>';
            bill.party_votes.forEach(party => {
                partyTable += `<tr style="border-bottom: 1px solid #e0e0e0;"><td style="padding: 10px; font-weight: 600;">${escapeHtml(party.party_name || '무소속')}</td><td style="padding: 10px; text-align: center; color: #27ae60;">${formatNumber(party.vote_for)}</td><td style="padding: 10px; text-align: center; color: #e74c3c;">${formatNumber(party.vote_against)}</td><td style="padding: 10px; text-align: center; color: #f39c12;">${formatNumber(party.vote_abstain)}</td><td style="padding: 10px; text-align: center; color: #95a5a6;">${formatNumber(party.vote_absent)}</td></tr>`;
            });
            partyTable += '</tbody></table></div>';
            voteSection += partyTable;
        }
        
        // 의원별 표결 결과 표시
        if (bill.member_votes_by_result) {
            let memberSection = '<div class="modal-section"><h3>의원별 표결 결과</h3>';
            
            const resultLabels = {
                '찬성': { label: '찬성', color: '#27ae60', icon: '✅', class: 'vote-for' },
                '반대': { label: '반대', color: '#e74c3c', icon: '❌', class: 'vote-against' },
                '기권': { label: '기권', color: '#f39c12', icon: '⏸️', class: 'vote-abstain' },
                '불참': { label: '불참', color: '#95a5a6', icon: '🚫', class: 'vote-absent' }
            };
            
            for (const [result, config] of Object.entries(resultLabels)) {
                const members = bill.member_votes_by_result[result] || [];
                if (members.length > 0) {
                    memberSection += `<div style="margin-top: 20px;"><h4 style="color: ${config.color}; margin-bottom: 10px; font-size: 1.1em;">${config.icon} ${config.label} (${members.length}명)</h4>`;
                    memberSection += '<div class="member-list">';
                    
                    members.forEach(member => {
                        const memberName = escapeHtml(member.member_name || '미상');
                        const partyName = escapeHtml(member.party_name || '무소속');
                        const districtName = escapeHtml(member.district_name || '');
                        const photoUrl = member.photo_url || '';
                        
                        memberSection += `<div class="member-item ${config.class}">`;
                        if (photoUrl) {
                            memberSection += `<img src="${escapeHtml(photoUrl)}" alt="${memberName}" class="member-photo" onerror="this.style.display='none'">`;
                        }
                        memberSection += `<div class="member-name">${memberName}</div>`;
                        memberSection += `<div class="member-info">${partyName}${districtName ? ' · ' + districtName : ''}</div>`;
                        memberSection += '</div>';
                    });
                    
                    memberSection += '</div></div>';
                }
            }
            
            memberSection += '</div>';
            voteSection += memberSection;
        }
    } else {
        voteSection = '<div class="modal-section"><h3>표결 결과</h3><p style="color: #95a5a6;">표결이 진행되지 않았습니다.</p></div>';
    }
    
    modalBody.innerHTML = `
        <div class="modal-title">${escapeHtml(bill.title)}</div>
        <div class="modal-section">
            <h3>의안 정보</h3>
            <div class="modal-info-grid">
                <div class="modal-info-item">
                    <div class="modal-info-label">의안번호</div>
                    <div class="modal-info-value">${bill.bill_no || '미상'}</div>
                </div>
                <div class="modal-info-item">
                    <div class="modal-info-label">제안일</div>
                    <div class="modal-info-value">${proposalDate}</div>
                </div>
                <div class="modal-info-item">
                    <div class="modal-info-label">제안자</div>
                    <div class="modal-info-value">${bill.proposer_name ? escapeHtml(bill.proposer_name) + (bill.proposer_kind === '의원' ? ' 의원' : '') : (bill.proposer_kind || '미상')}</div>
                </div>
                <div class="modal-info-item">
                    <div class="modal-info-label">처리구분</div>
                    <div class="modal-info-value">${bill.pass_gubn || '미상'}</div>
                </div>
                <div class="modal-info-item">
                    <div class="modal-info-label">진행단계</div>
                    <div class="modal-info-value">${bill.proc_stage_cd || '미상'}</div>
                </div>
                <div class="modal-info-item">
                    <div class="modal-info-label">처리일</div>
                    <div class="modal-info-value">${procDate}</div>
                </div>
            </div>
            ${bill.link_url ? `
            <div style="margin-top: 20px; padding: 15px; background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%); border-radius: 10px; text-align: center; box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);">
                <a href="${bill.link_url}" target="_blank" style="color: white; text-decoration: none; font-weight: 600; font-size: 1.1em; display: inline-flex; align-items: center; gap: 8px;">
                    <span>📄 의안 원문 보기</span>
                    <span style="font-size: 1.2em;">→</span>
                </a>
                <p style="color: rgba(255, 255, 255, 0.9); font-size: 0.85em; margin-top: 8px; margin-bottom: 0;">국회 홈페이지에서 의안 상세 정보를 확인하실 수 있습니다</p>
            </div>
            ` : ''}
        </div>
        ${voteSection}
    `;
    
    modal.style.display = 'block';
}

// 페이지네이션 표시
function displayPagination(pagination) {
    const container = document.getElementById('pagination');
    container.innerHTML = '';
    
    if (pagination.pages <= 1) {
        return;
    }
    
    const pageInfo = document.createElement('div');
    pageInfo.className = 'pagination-info';
    pageInfo.textContent = `${pagination.page} / ${pagination.pages} 페이지`;
    container.appendChild(pageInfo);
    
    // 이전 페이지 버튼
    const prevButton = document.createElement('button');
    prevButton.textContent = '이전';
    prevButton.disabled = pagination.page <= 1;
    prevButton.onclick = () => loadBills(pagination.page - 1);
    container.appendChild(prevButton);
    
    // 페이지 번호 버튼들
    const startPage = Math.max(1, pagination.page - 2);
    const endPage = Math.min(pagination.pages, pagination.page + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        const pageButton = document.createElement('button');
        pageButton.textContent = i;
        pageButton.className = i === pagination.page ? 'active' : '';
        pageButton.onclick = () => loadBills(i);
        container.appendChild(pageButton);
    }
    
    // 다음 페이지 버튼
    const nextButton = document.createElement('button');
    nextButton.textContent = '다음';
    nextButton.disabled = pagination.page >= pagination.pages;
    nextButton.onclick = () => loadBills(pagination.page + 1);
    container.appendChild(nextButton);
}

// 활성 필터 표시 업데이트
function updateActiveFilters() {
    const container = document.getElementById('activeFilters');
    const filtersContainer = container.querySelector('div');
    filtersContainer.innerHTML = '<span style="font-weight: 600; color: #6c757d; font-size: 0.9rem;">적용된 필터:</span>';
    
    const activeFilters = [];
    
    if (currentMonth) {
        const monthLabel = document.querySelector(`#monthFilter option[value="${currentMonth}"]`)?.textContent || currentMonth;
        activeFilters.push({ type: 'month', label: monthLabel, value: currentMonth });
    }
    
    if (currentSearch) {
        activeFilters.push({ type: 'search', label: `검색: "${currentSearch}"`, value: currentSearch });
    }
    
    if (currentPassGubn) {
        const passGubnLabel = document.querySelector(`#passGubnFilter option[value="${currentPassGubn}"]`)?.textContent || currentPassGubn;
        activeFilters.push({ type: 'pass_gubn', label: passGubnLabel.split(' (')[0], value: currentPassGubn });
    }
    
    if (currentProcStage) {
        const procStageLabel = document.querySelector(`#procStageFilter option[value="${currentProcStage}"]`)?.textContent || currentProcStage;
        activeFilters.push({ type: 'proc_stage', label: procStageLabel.split(' (')[0], value: currentProcStage });
    }
    
    if (activeFilters.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    
    activeFilters.forEach(filter => {
        const tag = document.createElement('span');
        tag.className = 'filter-tag';
        tag.style.cssText = 'display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%); color: white; border-radius: 20px; font-size: 0.85rem; font-weight: 500;';
        
        tag.innerHTML = `
            <span>${escapeHtml(filter.label)}</span>
            <span style="cursor: pointer; font-weight: bold; font-size: 1.1em; opacity: 0.9;" onclick="removeFilter('${filter.type}')" title="필터 제거">×</span>
        `;
        
        filtersContainer.appendChild(tag);
    });
}

// 필터 제거 함수 (전역으로 등록)
window.removeFilter = function(filterType) {
    switch(filterType) {
        case 'month':
            document.getElementById('monthFilter').value = '';
            currentMonth = '';
            break;
        case 'search':
            document.getElementById('searchInput').value = '';
            currentSearch = '';
            break;
        case 'pass_gubn':
            document.getElementById('passGubnFilter').value = '';
            currentPassGubn = '';
            break;
        case 'proc_stage':
            document.getElementById('procStageFilter').value = '';
            currentProcStage = '';
            break;
    }
    loadBills(1);
};

// 이벤트 리스너 설정
function setupEventListeners() {
    const searchInput = document.getElementById('searchInput');
    const clearButton = document.getElementById('clearFilter');
    const monthFilter = document.getElementById('monthFilter');
    const passGubnFilter = document.getElementById('passGubnFilter');
    const procStageFilter = document.getElementById('procStageFilter');
    const sortBy = document.getElementById('sortBy');
    const orderBy = document.getElementById('orderBy');
    
    // 검색 입력 필드 - 디바운스 적용 (500ms)
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentSearch = e.target.value.trim();
            loadBills(1);
        }, 500);
    });
    
    // 검색 입력 필드에서 Enter 키 처리 (즉시 적용)
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            clearTimeout(searchTimeout);
            currentSearch = e.target.value.trim();
            loadBills(1);
        }
    });
    
    // 드롭다운 필터 - 즉시 적용
    monthFilter.addEventListener('change', () => {
        currentMonth = monthFilter.value;
        loadBills(1);
    });
    
    passGubnFilter.addEventListener('change', () => {
        currentPassGubn = passGubnFilter.value;
        loadBills(1);
    });
    
    procStageFilter.addEventListener('change', () => {
        currentProcStage = procStageFilter.value;
        loadBills(1);
    });
    
    sortBy.addEventListener('change', () => {
        currentSortBy = sortBy.value;
        loadBills(1);
    });
    
    orderBy.addEventListener('change', () => {
        currentOrder = orderBy.value;
        loadBills(1);
    });
    
    // 초기화 버튼
    clearButton.addEventListener('click', () => {
        searchInput.value = '';
        monthFilter.value = '';
        passGubnFilter.value = '';
        procStageFilter.value = '';
        sortBy.value = 'proposal_date';
        orderBy.value = 'desc';
        currentMonth = '';
        currentSearch = '';
        currentPassGubn = '';
        currentProcStage = '';
        currentSortBy = 'proposal_date';
        currentOrder = 'desc';
        loadBills(1);
    });
    
    // 모달 닫기
    const modal = document.getElementById('billModal');
    const closeButton = document.querySelector('.modal-close');
    
    closeButton.onclick = () => {
        modal.style.display = 'none';
    };
    
    window.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    };
}

// 진행단계별 통계 표시
function displayProcStageStats(procStageStats, totalBills) {
    const container = document.getElementById('procStageStats');
    if (!container) return;
    
    container.innerHTML = '';
    
    // 제목 추가
    const title = document.createElement('h4');
    title.style.cssText = 'margin-bottom: 15px; color: #2c3e50; font-size: 1.1rem;';
    title.textContent = '진행단계별 통계';
    container.appendChild(title);
    
    // 주요 진행단계 정의 (사용자가 이해하기 쉬운 핵심 단계만)
    const mainStages = [
        '접수',
        '소관위접수',
        '소관위심사',
        '본회의의결',
        '처리완료'  // 공포, 정부이송, 대안반영폐기, 철회 등을 묶음
    ];
    
    // 처리완료 단계들 (하위 단계)
    const completedStages = ['공포', '정부이송', '대안반영폐기', '철회', '본회의불부의', '재의(부결)'];
    
    // 기타 단계들
    const otherStages = ['소관위심사보고', '체계자구심사', '본회의부의안건', '재의요구', '미분류'];
    
    // 진행단계별 색상 매핑
    const stageColors = {
        '접수': { bg: 'linear-gradient(135deg, #fce4ec 0%, #f8bbd0 100%)', border: '#f48fb1', text: '#c2185b' },
        '소관위접수': { bg: 'linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%)', border: '#ba68c8', text: '#7b1fa2' },
        '소관위심사': { bg: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)', border: '#64b5f6', text: '#1565c0' },
        '본회의의결': { bg: 'linear-gradient(135deg, #e0f2f1 0%, #b2dfdb 100%)', border: '#4db6ac', text: '#00695c' },
        '처리완료': { bg: 'linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%)', border: '#81c784', text: '#2e7d32' },
        '기타': { bg: 'linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%)', border: '#bdbdbd', text: '#616161' }
    };
    
    // 처리완료 단계 합계 계산
    let completedCount = 0;
    completedStages.forEach(stage => {
        if (procStageStats[stage]) {
            completedCount += procStageStats[stage];
        }
    });
    
    // 기타 단계 합계 계산
    let otherCount = 0;
    otherStages.forEach(stage => {
        if (procStageStats[stage]) {
            otherCount += procStageStats[stage];
        }
    });
    
    // 주요 단계만 표시할 데이터 구성
    const displayData = [];
    
    mainStages.forEach(stage => {
        if (stage === '처리완료') {
            if (completedCount > 0) {
                displayData.push(['처리완료', completedCount]);
            }
        } else if (procStageStats[stage]) {
            displayData.push([stage, procStageStats[stage]]);
        }
    });
    
    // 기타 단계가 있으면 추가
    if (otherCount > 0) {
        displayData.push(['기타', otherCount]);
    }
    
    // 통계 그리드 (한 줄로 표시)
    const grid = document.createElement('div');
    grid.style.cssText = 'display: flex; flex-wrap: nowrap; gap: 15px; padding-bottom: 10px;';
    
    displayData.forEach(([stage, count]) => {
        const percent = totalBills > 0 ? ((count / totalBills) * 100).toFixed(1) : 0;
        const color = stageColors[stage] || stageColors['기타'];
        
        const card = document.createElement('div');
        card.style.cssText = `background: ${color.bg}; padding: 20px; border-radius: 12px; border: 2px solid ${color.border}; text-align: center; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); transition: transform 0.2s; flex: 1; min-width: 0;`;
        card.onmouseenter = () => card.style.transform = 'translateY(-3px)';
        card.onmouseleave = () => card.style.transform = 'translateY(0)';
        
        card.innerHTML = `
            <div style="font-size: 2rem; font-weight: 700; color: ${color.text}; margin-bottom: 8px;">${formatNumber(count)}</div>
            <div style="font-size: 1rem; color: ${color.text}; margin-bottom: 5px; font-weight: 600;">${escapeHtml(stage)}</div>
            <div style="font-size: 0.85rem; color: ${color.text}; opacity: 0.8;">${percent}%</div>
        `;
        
        grid.appendChild(card);
    });
    
    container.appendChild(grid);
}

// 처리/계류 통계 표시
function displayPassGubnStats(passGubnStats, totalBills) {
    const container = document.getElementById('passGubnStats');
    if (!container) return;
    
    container.innerHTML = '';
    
    // 제목 추가
    const title = document.createElement('h4');
    title.style.cssText = 'margin-bottom: 15px; color: #2c3e50; font-size: 1.1rem;';
    title.textContent = '처리구분별 통계';
    container.appendChild(title);
    
    // 통계 그리드
    const grid = document.createElement('div');
    grid.style.cssText = 'display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;';
    
    // 처리구분별 색상 매핑
    const gubnColors = {
        '처리의안': { bg: 'linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%)', border: '#81c784', text: '#2e7d32' },
        '계류의안': { bg: 'linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%)', border: '#ffb74d', text: '#e65100' },
        '미분류': { bg: 'linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%)', border: '#bdbdbd', text: '#616161' }
    };
    
    Object.entries(passGubnStats).forEach(([gubn, count]) => {
        const percent = totalBills > 0 ? ((count / totalBills) * 100).toFixed(1) : 0;
        const color = gubnColors[gubn] || gubnColors['미분류'];
        
        const card = document.createElement('div');
        card.style.cssText = `background: ${color.bg}; padding: 15px; border-radius: 10px; border: 2px solid ${color.border}; text-align: center; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); transition: transform 0.2s;`;
        card.onmouseenter = () => card.style.transform = 'translateY(-3px)';
        card.onmouseleave = () => card.style.transform = 'translateY(0)';
        
        card.innerHTML = `
            <div style="font-size: 1.8rem; font-weight: 700; color: ${color.text}; margin-bottom: 5px;">${formatNumber(count)}</div>
            <div style="font-size: 0.9rem; color: ${color.text}; margin-bottom: 3px; font-weight: 600;">${escapeHtml(gubn)}</div>
            <div style="font-size: 0.75rem; color: ${color.text}; opacity: 0.8;">${percent}%</div>
        `;
        
        grid.appendChild(card);
    });
    
    container.appendChild(grid);
}

// 유틸리티 함수들
function formatNumber(num) {
    if (num === null || num === undefined) return '0';
    return Number(num).toLocaleString('ko-KR');
}

function formatDate(dateString) {
    if (!dateString) return '미상';
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading(show) {
    const indicator = document.getElementById('loadingIndicator');
    indicator.style.display = show ? 'block' : 'none';
}

function showError(message) {
    alert(message);
}

