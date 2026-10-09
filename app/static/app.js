import { request } from './api.js';

let state = null;
let pollTimeout = null;

async function bootstrap() {
    const btnCreate = document.getElementById('btn-create-lab');
    const btnNew = document.getElementById('btn-new-lab');
    const overlay = document.getElementById('create-lab-overlay');
    const dashboard = document.getElementById('dashboard');

    if (sessionStorage.getItem("chaoslab_token") && sessionStorage.getItem("chaoslab_id")) {
        overlay.style.display = 'none';
        dashboard.style.display = 'block';
        startPolling();
    } else {
        overlay.style.display = 'flex';
        dashboard.style.display = 'none';
    }

    btnCreate.onclick = async () => {
        btnCreate.disabled = true;
        try {
            const res = await request('/api/labs', { method: 'POST', body: JSON.stringify({}) });
            sessionStorage.setItem("chaoslab_token", res.token);
            sessionStorage.setItem("chaoslab_id", res.lab_id);
            overlay.style.display = 'none';
            dashboard.style.display = 'block';
            startPolling();
        } catch (e) {
            alert(e.message);
        } finally {
            btnCreate.disabled = false;
        }
    };

    btnNew.onclick = () => {
        if (confirm("Leave this experiment? You will lose access to it.")) {
            sessionStorage.removeItem("chaoslab_token");
            sessionStorage.removeItem("chaoslab_id");
            location.reload();
        }
    };

    setupControls();
}

async function startPolling() {
    const labId = sessionStorage.getItem("chaoslab_id");
    const statusEl = document.getElementById('connection-status');
    
    try {
        const newData = await request(`/api/labs/${labId}`);
        if (!state || newData.revision >= state.revision) {
            state = newData;
            render(state);
        }
        statusEl.textContent = state.worker_status === 'online' ? 'Live' : 'Worker Offline';
        statusEl.className = `badge ${state.worker_status === 'online' ? 'succeeded' : 'rejected'}`;
        
        pollTimeout = setTimeout(startPolling, 1000);
    } catch (e) {
        statusEl.textContent = `Reconnecting (${new Date().toLocaleTimeString()})`;
        statusEl.className = 'badge retry_wait';
        pollTimeout = setTimeout(startPolling, 3000);
    }
}

function setupControls() {
    const bindCommand = (btnId, action, value = null) => {
        const btn = document.getElementById(btnId);
        btn.onclick = async () => {
            const labId = sessionStorage.getItem("chaoslab_id");
            btn.disabled = true;
            try {
                const body = {
                    command_id: crypto.randomUUID(),
                    action: action
                };
                if (value !== null) body.value = value;
                const newData = await request(`/api/labs/${labId}/commands`, {
                    method: 'POST',
                    body: JSON.stringify(body)
                });
                if (!state || newData.revision >= state.revision) {
                    state = newData;
                    render(state);
                }
            } catch (e) {
                alert(e.message);
            } finally {
                btn.disabled = false;
            }
        };
    };

    bindCommand('btn-start-gen', 'start_generation');
    bindCommand('btn-stop-gen', 'stop_generation');
    bindCommand('btn-pause', 'set_paused', true);
    bindCommand('btn-restore', 'restore');
    bindCommand('btn-inject', 'inject_malformed');
    bindCommand('btn-temp-errors', 'set_temporary_errors', true);
    
    document.getElementById('btn-report').onclick = async () => {
        const labId = sessionStorage.getItem("chaoslab_id");
        try {
            const res = await request(`/api/labs/${labId}/report`);
            const blob = new Blob([JSON.stringify(res, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `chaoslab-report-${labId.slice(0, 8)}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch(e) {
            alert("Failed to download report");
        }
    };
}

function render(data) {
    document.getElementById('lab-id-display').textContent = `Lab ID: ${data.lab_id.slice(0, 8)}`;
    document.getElementById('btn-report').disabled = false;
    
    const c = data.counts;
    document.getElementById('metric-queued').textContent = c.queued;
    document.getElementById('metric-processing').textContent = c.processing;
    document.getElementById('metric-retry').textContent = c.retry_wait;
    document.getElementById('metric-succeeded').textContent = c.succeeded;
    document.getElementById('metric-failed').textContent = c.rejected + c.dead_letter;
    
    const ct = data.controls;
    document.getElementById('btn-start-gen').style.display = ct.generating ? 'none' : 'inline-block';
    document.getElementById('btn-stop-gen').style.display = ct.generating ? 'inline-block' : 'none';
    
    const btnPause = document.getElementById('btn-pause');
    if (ct.paused) {
        btnPause.textContent = "Processing paused";
        btnPause.disabled = true;
    } else {
        btnPause.textContent = "Pause worker";
        btnPause.disabled = false;
    }

    const btnTemp = document.getElementById('btn-temp-errors');
    if (ct.temporary_errors) {
        btnTemp.textContent = "Enabled";
        btnTemp.disabled = true;
    } else {
        btnTemp.textContent = "Enable";
        btnTemp.disabled = false;
    }
    
    const tbody = document.getElementById('orders-tbody');
    tbody.innerHTML = '';
    const orders = [...data.orders].reverse().slice(0, 50);
    for (const o of orders) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${o.id}</td>
            <td>${o.payload.category}</td>
            <td><span class="badge ${o.state}">${o.state}</span></td>
            <td>${o.attempts}</td>
        `;
        tbody.appendChild(tr);
    }
    
    const timeline = document.getElementById('event-timeline');
    timeline.innerHTML = '';
    const events = [...data.events].reverse().slice(0, 50);
    for (const e of events) {
        const div = document.createElement('div');
        div.className = 'event-item';
        div.innerHTML = `
            <div class="event-time">${new Date(e.time * 1000).toLocaleTimeString()} - ${e.type}</div>
            <div>${e.message} ${e.order_id ? `(${e.order_id})` : ''}</div>
        `;
        timeline.appendChild(div);
    }
    
    renderChart(data.samples);
}

function renderChart(samples) {
    const container = document.getElementById('queue-chart');
    if (samples.length < 2) {
        container.innerHTML = '<div style="padding:20px; color:var(--muted)">Waiting for data...</div>';
        return;
    }
    
    const w = container.clientWidth;
    const h = container.clientHeight;
    
    let maxQ = 10;
    for (const s of samples) {
        if (s.queued > maxQ) maxQ = s.queued;
    }
    
    const pts = samples.map((s, i) => {
        const x = (i / (samples.length - 1)) * w;
        const y = h - (s.queued / maxQ) * h;
        return `${x},${y}`;
    }).join(' ');
    
    container.innerHTML = `
        <svg class="chart-svg" viewBox="0 0 ${w} ${h}">
            <polyline class="chart-line" points="${pts}" />
        </svg>
    `;
}

bootstrap();
