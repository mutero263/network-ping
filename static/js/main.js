// Update bandwidth every 2 seconds and log via backend
setInterval(() => {
    fetch('/api/simulate_bandwidth', {
        method: 'POST'
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById('dl-speed').textContent = data.download.toFixed(2);
        document.getElementById('ul-speed').textContent = data.upload.toFixed(2);
    })
    .catch(err => console.warn("Bandwidth simulation failed", err));
}, 2000);

// Ping Test
function runPing() {
    const target = document.getElementById('ping-target').value;
    fetch('/api/ping', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target })
    })
    .then(r => r.json())
    .then(data => {
        const res = document.getElementById('ping-result');
        res.innerHTML = `
            <p><strong>${target}</strong>: Avg Latency: ${data.avg_latency} ms | Packet Loss: ${data.packet_loss}%</p>
        `;
        if (data.avg_latency > 500 || data.packet_loss > 50) {
            alert("High latency or packet loss detected!");
        }
        loadPingLogs();
    });
}

// Uptime Check
function checkUptime() {
    const url = document.getElementById('uptime-url').value;
    fetch('/api/uptime', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
    })
    .then(r => r.json())
    .then(data => {
        const res = document.getElementById('uptime-result');
        const color = data.status === 'Online' ? 'green' : 'red';
        res.innerHTML = `<p><strong>${data.url}</strong>: <span style="color:${color}">${data.status}</span></p>`;
        if (data.status === 'Offline') {
            alert(`Website ${data.url} is DOWN!`);
        }
        loadUptimeLogs();
    });
}

// Load Logs
function loadPingLogs() {
    fetch('/api/logs/ping')
        .then(r => r.json())
        .then(logs => {
            const list = document.getElementById('ping-log-list');
            list.innerHTML = logs.map(l => 
                `<li>${l.time}: ${l.target} → ${l.avg}ms, ${l.loss}% loss</li>`
            ).join('');
        });
}

function loadUptimeLogs() {
    fetch('/api/logs/uptime')
        .then(r => r.json())
        .then(logs => {
            const list = document.getElementById('uptime-log-list');
            list.innerHTML = logs.map(l => 
                `<li>${l.time}: ${l.url} → ${l.status}</li>`
            ).join('');
        });
}

// Tab Switching
function openTab(tabName) {
    document.querySelectorAll('.log-content').forEach(t => t.style.display = 'none');
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(tabName).style.display = 'block';
    event.currentTarget.classList.add('active');
}

// Load logs on startup
document.addEventListener('DOMContentLoaded', () => {
    loadPingLogs();
    loadUptimeLogs();
});