function getVn(key) {
    if (!key) return key;
    return localizationMap[key] || key;
}

function translateText(text) {
    if (!text) return text;
    // Lấy các key có độ dài lớn nhất trước để tránh lỗi replace một phần
    const keys = Object.keys(localizationMap).sort((a, b) => b.length - a.length);
    let result = text;
    keys.forEach(k => {
        const regex = new RegExp('\\b' + k + '\\b', 'g');
        result = result.replace(regex, localizationMap[k]);
    });
    return result;
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('diagnoseForm');
    const imageInput = document.getElementById('imageInput');
    const imagePreview = document.getElementById('imagePreview');
    const uploadArea = document.getElementById('uploadArea');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoader = document.getElementById('btnLoader');
    const resultSection = document.getElementById('resultSection');

    imageInput.addEventListener('change', function(e) {
        if (this.files && this.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                imagePreview.classList.remove('hidden');
                uploadArea.querySelector('.upload-icon').classList.add('hidden');
                uploadArea.querySelector('.upload-text').classList.add('hidden');
            }
            reader.readAsDataURL(this.files[0]);
        }
    });

    // Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Show loader
        btnText.classList.add('hidden');
        btnLoader.classList.remove('hidden');
        submitBtn.disabled = true;
        resultSection.classList.add('hidden');

        const formData = new FormData(form);

        try {
            const response = await fetch('http://127.0.0.1:8000/api/v1/diagnose', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Lỗi kết nối đến server');
            }

            const data = await response.json();
            renderResults(data);

        } catch (error) {
            alert('Lỗi: ' + error.message + '\n\nHãy đảm bảo bạn đã khởi động FastAPI server ở cổng 8000.');
            console.error(error);
        } finally {
            // Hide loader
            btnText.classList.remove('hidden');
            btnLoader.classList.add('hidden');
            submitBtn.disabled = false;
        }
    });

    function renderResults(data) {
        // NLG Message
        document.getElementById('naturalMessage').textContent = data.natural_message || "Thiết bị hoạt động bình thường.";

        // Diagnosis
        document.getElementById('resDevice').textContent = data.device_name_vn || data.device;
        
        if (data.fault_count > 0 && data.primary_diagnosis) {
            document.getElementById('resFaultCode').textContent = data.primary_diagnosis.fault_code;
            document.getElementById('resFaultName').textContent = data.primary_diagnosis.fault_name_vn;
            
            const components = data.primary_diagnosis.components || [];
            const mappedComponents = components.map(c => getVn(c));
            document.getElementById('resComponents').textContent = mappedComponents.join(', ');
            
            const conf = data.confidence_score || data.primary_diagnosis.confidence_score;
            document.getElementById('resConfidence').textContent = conf ? `${conf}%` : 'N/A';
        } else {
            document.getElementById('resFaultCode').textContent = 'NORMAL';
            document.getElementById('resFaultName').textContent = 'Không phát hiện lỗi';
            document.getElementById('resComponents').textContent = '-';
            document.getElementById('resConfidence').textContent = '100%';
        }

        // Pricing
        const formatVND = (val) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val || 0);
        document.getElementById('resTotalPrice').textContent = formatVND(data.estimated_price_vnd);
        document.getElementById('resDiscount').textContent = formatVND(data.discount_vnd);
        document.getElementById('resWarranty').textContent = `${data.warranty_months || 0} tháng`;

        // Workflow RAG (DAG)
        const wfStatesContainer = document.getElementById('workflowStates');
        wfStatesContainer.innerHTML = '';
        const workflow = data.repair_workflow;

        if (workflow && workflow.states && workflow.states.length > 0) {
            // Risk Badge
            const riskBadge = document.getElementById('workflowRisk');
            const score = workflow.risk_score || 0;
            riskBadge.textContent = `Risk Score: ${score}/100`;
            riskBadge.className = 'badge';
            if (score <= 30) riskBadge.classList.add('safe');
            else if (score <= 70) riskBadge.classList.add('warning');
            else riskBadge.classList.add('danger');

            // Render States
            workflow.states.forEach(state => {
                const item = document.createElement('div');
                item.className = 'timeline-item';
                
                let toolsHtml = '';
                if (state.tools && state.tools.length > 0) {
                    const mappedTools = state.tools.map(t => getVn(t));
                    toolsHtml = `<p class="timeline-desc" style="margin-top: 5px;"><strong>Dụng cụ:</strong> ${mappedTools.join(', ')}</p>`;
                }
                
                let voltageHtml = '';
                if (state.voltage_checkpoint) {
                    voltageHtml = `<p class="timeline-desc" style="margin-top: 5px; color: var(--warning);"><strong>Đo kiểm:</strong> ${state.voltage_checkpoint}</p>`;
                }

                item.innerHTML = `
                    <div class="timeline-phase">${getVn(state.phase)} - ${getVn(state.action)}</div>
                    <div class="timeline-content">
                        <div class="timeline-title">${getVn(state.target) || state.assembly || getVn(state.state_id)}</div>
                        <p class="timeline-desc">${translateText(state.instruction_vn) || ''}</p>
                        ${toolsHtml}
                        ${voltageHtml}
                    </div>
                `;
                wfStatesContainer.appendChild(item);
            });
        } else {
            document.getElementById('workflowRisk').textContent = '';
            wfStatesContainer.innerHTML = '<p class="timeline-desc">Không có quy trình kỹ thuật cho lỗi này.</p>';
        }

        // Render Markdown Guide
        const guideEl = document.getElementById('repairGuide');
        if (data.repair_guide) {
            guideEl.textContent = data.repair_guide;
        } else {
            guideEl.textContent = 'Không có báo cáo Markdown.';
        }

        resultSection.classList.remove('hidden');
        resultSection.scrollIntoView({ behavior: 'smooth' });
    }
});
