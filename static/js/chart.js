// 1. Initialize the Chart.js instance
const ctx = document.getElementById('energyChart').getContext('2d');
let chartData = {
    labels: [],
    datasets: [{
        label: 'Live Consumption (kWh)',
        data: [],
        borderColor: '#00d4ff',
        backgroundColor: 'rgba(0, 212, 255, 0.1)',
        borderWidth: 3,
        tension: 0.4,
        fill: true
    }]
};

const energyChart = new Chart(ctx, {
    type: 'line',
    data: chartData,
    options: {
        responsive: true,
        scales: {
            y: { beginAtZero: true, grid: { color: '#333' } },
            x: { grid: { display: false } }
        },
        plugins: { legend: { display: false } }
    }
});

// 2. The Main Update Function
async function updateDashboard() {
    try {
        const response = await fetch('/api/data'); // Points to your Flask route
        const data = await response.json();

        if (data.records.length > 0) {
            const latest = data.records[data.records.length - 1];
            const prediction = data.prediction;

            // Update UI Numbers
            document.getElementById('curr-load').innerText = `${latest.energy.toFixed(2)} kWh`;
            document.getElementById('ai-pred').innerText = `${prediction.toFixed(2)} kWh`;

            // Update Chart Data
            energyChart.data.labels = data.records.map(r => r.timestamp.split(' ')[1]);
            energyChart.data.datasets[0].data = data.records.map(r => r.energy);
            energyChart.update('none'); // 'none' prevents annoying animation jitters

            // Trigger the AI Protection Logic
            runLoadSheddingLogic(latest.energy, prediction);
        }
    } catch (err) {
        console.error("Connection lost to Smart Grid API", err);
    }
}

// 3. The "Brain": Load Shedding & Alert Logic
function runLoadSheddingLogic(current, forecast) {
    const alertCard = document.getElementById('grid-alert-card');
    const statusText = document.getElementById('grid-status-text');
    const lsBadge = document.getElementById('ls-badge');
    const relayDesc = document.getElementById('relay-desc');

    // CRITICAL: AI predicts a surge over 85kWh
    if (forecast > 85) {
        alertCard.className = "card p-3 shadow-sm bg-danger text-white border-0 transition";
        statusText.innerText = "CRITICAL: OVERLOAD PREDICTED";
        lsBadge.className = "badge bg-danger blink_me";
        lsBadge.innerText = "LOAD SHEDDING: ACTIVE";
        relayDesc.innerHTML = "<b>Action:</b> Sector B disconnected to save Grid Transformer.";
        
        // Log the event only once per surge
        if (statusText.dataset.lastState !== "critical") {
            addLog("CRITICAL: AI initiated Load Shedding on Sector B");
            statusText.dataset.lastState = "critical";
        }
    } 
    // WARNING: High usage but no immediate surge
    else if (current > 70) {
        alertCard.className = "card p-3 shadow-sm bg-warning text-dark border-0 transition";
        statusText.innerText = "WARNING: HIGH CONSUMPTION";
        lsBadge.className = "badge bg-warning text-dark";
        lsBadge.innerText = "SENSORS ALERT";
        relayDesc.innerText = "Monitoring non-essential loads. System near threshold.";
        statusText.dataset.lastState = "warning";
    } 
    // SAFE: Normal operation
    else {
        alertCard.className = "card p-3 shadow-sm bg-success text-white border-0 transition";
        statusText.innerText = "SYSTEM STABLE";
        lsBadge.className = "badge bg-secondary";
        lsBadge.innerText = "INACTIVE";
        relayDesc.innerText = "All sectors (A, B, C) drawing power normally.";
        statusText.dataset.lastState = "stable";
    }
}

// 4. Helper to add events to the Log Table
function addLog(message) {
    const body = document.getElementById('log-body');
    const time = new Date().toLocaleTimeString();
    const row = `<tr class="small border-0">
                    <td class="text-secondary">${time}</td>
                    <td class="text-info">${message}</td>
                 </tr>`;
    body.insertAdjacentHTML('afterbegin', row);
}

// Start the live loop (every 2 seconds)
setInterval(updateDashboard, 2000);
updateDashboard();