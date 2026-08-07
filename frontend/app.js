const IS_LOCAL = window.location.hostname === "127.0.0.1" || 
                 window.location.hostname === "localhost" || 
                 window.location.hostname.startsWith("192.168.");

const API_BASE = IS_LOCAL
    ? "http://127.0.0.1:8000"
    : "https://farewell-system-ulp2.onrender.com";

// --- Toast Non-Blocking UI Helper ---
function showToast(msg) {
    const toast = document.getElementById("toast-loader");
    const toastText = document.getElementById("toast-text");
    if (toastText) toastText.innerText = msg;
    if (toast) toast.classList.remove("hidden");
}

function hideToast() {
    const toast = document.getElementById("toast-loader");
    if (toast) toast.classList.add("hidden");
}

// --- Navigation Logic ---
const navScanner = document.getElementById("nav-scanner");
const navDashboard = document.getElementById("nav-dashboard");
const secScanner = document.getElementById("scanner-section");
const secDashboard = document.getElementById("dashboard-section");

navScanner.addEventListener("click", () => {
    navScanner.classList.add("active");
    navDashboard.classList.remove("active");
    secScanner.classList.remove("hidden");
    secDashboard.classList.add("hidden");
});

navDashboard.addEventListener("click", () => {
    navDashboard.classList.add("active");
    navScanner.classList.remove("active");
    secDashboard.classList.remove("hidden");
    secScanner.classList.add("hidden");
    fetchStats(); // Fast stats load on opening dashboard
});

// --- Fast Pre-Warm Ping ---
function preWarmServer() {
    fetch(`${API_BASE}/health`, { timeout: 3000 }).catch(() => {});
}
preWarmServer();

// --- Auto Stats Refresh ---
setInterval(() => {
    if (!secDashboard.classList.contains("hidden")) {
        fetchStats();
    }
}, 15000);

// --- Scanner Logic & Two-Step Verification ---
let html5QrCode;
let scannerIsRunning = false;
let currentScannedToken = "";

function startScanner() {
    html5QrCode = new Html5Qrcode("reader");
    html5QrCode.start(
        { facingMode: "environment" },
        { fps: 25, qrbox: { width: 250, height: 250 } },
        onScanSuccess
    ).then(() => {
        scannerIsRunning = true;
        if (navigator.vibrate) navigator.vibrate(40);
        console.log("Buildora QR Scanner ready.");
    }).catch(err => {
        console.error("Camera access failed", err);
        document.getElementById("reader").innerHTML = "<p style='color:#ef4444; padding:20px; text-align:center;'>Camera access denied or unreadable.</p>";
    });
}

function onScanSuccess(decodedText) {
    if (decodedText === currentScannedToken) return;
    currentScannedToken = decodedText;

    // Visual feedback on reader box
    document.getElementById("reader").style.borderColor = "#4ade80";
    setTimeout(() => document.getElementById("reader").style.borderColor = "var(--glass-border)", 400);

    showToast("Verifying participant pass...");

    // Perform fast lookup
    fetch(`${API_BASE}/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: decodedText, action: "lookup" })
    })
    .then(res => res.json())
    .then(data => {
        hideToast();
        displayParticipantPanel(data);
    })
    .catch(err => {
        hideToast();
        console.error("Verification error", err);
        displayInvalidPanel("Unable to verify right now. Please try again.");
    });
}

function displayParticipantPanel(data) {
    const defaultPlaceholder = document.getElementById("verification-default");
    const participantPanel = document.getElementById("participant-panel");
    const banner = document.getElementById("status-banner");
    const btnMark = document.getElementById("btn-mark-present");
    const btnNext = document.getElementById("btn-scan-next");

    defaultPlaceholder.classList.add("hidden");
    participantPanel.classList.remove("hidden");

    if (data.status === "invalid") {
        banner.className = "status-banner invalid";
        banner.innerText = "✕ INVALID QR / PARTICIPANT NOT FOUND";
        document.getElementById("part-name").innerText = "Unknown";
        document.getElementById("part-reg-id").innerText = "N/A";
        document.getElementById("part-team").innerText = "N/A";
        document.getElementById("part-college").innerText = "N/A";
        document.getElementById("part-role").innerText = "N/A";
        document.getElementById("part-status-badge").innerHTML = `<span class="badge danger">Invalid</span>`;
        document.getElementById("checkin-time-row").classList.add("hidden");
        btnMark.classList.add("hidden");
        btnNext.classList.remove("hidden");
        playAudio("invalid");
        return;
    }

    // Populate details
    document.getElementById("part-name").innerText = data.name || "Unknown";
    document.getElementById("part-reg-id").innerText = data.registration_id || "N/A";
    document.getElementById("part-team").innerText = data.team_name || "N/A";
    document.getElementById("part-college").innerText = data.college || "N/A";
    document.getElementById("part-role").innerText = data.role || "Participant";

    const isAlreadyPresent = data.already_checked_in || data.attendance_status === "Present";
    document.getElementById("checkin-time-row").classList.remove("hidden");

    if (isAlreadyPresent) {
        banner.className = "status-banner used";
        banner.innerText = "⚠️ ALREADY CHECKED IN";
        document.getElementById("part-status-badge").innerHTML = `<span class="badge orange">Present</span>`;
        document.getElementById("part-checkin-time").innerText = data.check_in_time || "Already Marked";
        btnMark.classList.add("hidden");
        btnNext.classList.remove("hidden");
        playAudio("used");
    } else {
        banner.className = "status-banner valid";
        banner.innerText = "✅ VERIFIED PARTICIPANT";
        document.getElementById("part-status-badge").innerHTML = `<span class="badge green">Pending Check-in</span>`;
        document.getElementById("part-checkin-time").innerText = "Not Marked Yet";
        btnMark.classList.remove("hidden");
        btnNext.classList.add("hidden");
        playAudio("valid");
    }
}

function displayInvalidPanel(msg) {
    const defaultPlaceholder = document.getElementById("verification-default");
    const participantPanel = document.getElementById("participant-panel");
    const banner = document.getElementById("status-banner");
    
    defaultPlaceholder.classList.add("hidden");
    participantPanel.classList.remove("hidden");
    banner.className = "status-banner invalid";
    banner.innerText = `✕ ${msg}`;
    
    document.getElementById("btn-mark-present").classList.add("hidden");
    document.getElementById("btn-scan-next").classList.remove("hidden");
}

// Mark Present Handler
document.getElementById("btn-mark-present").addEventListener("click", () => {
    if (!currentScannedToken) return;

    showToast("Recording attendance...");

    fetch(`${API_BASE}/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: currentScannedToken, action: "mark" })
    })
    .then(res => res.json())
    .then(data => {
        hideToast();
        const banner = document.getElementById("status-banner");
        banner.className = "status-banner valid";
        banner.innerText = `✓ PRESENT — Check-in: ${data.check_in_time || 'Just now'}`;
        document.getElementById("part-status-badge").innerHTML = `<span class="badge green">Present</span>`;
        document.getElementById("part-checkin-time").innerText = data.check_in_time || "Just now";
        
        document.getElementById("btn-mark-present").classList.add("hidden");
        document.getElementById("btn-scan-next").classList.remove("hidden");
        if (navigator.vibrate) navigator.vibrate([100, 50, 100]);
    })
    .catch(err => {
        hideToast();
        alert("Failed to mark attendance. Please check network connection.");
    });
});

window.resetScannerUI = function() {
    currentScannedToken = "";
    document.getElementById("participant-panel").classList.add("hidden");
    document.getElementById("verification-default").classList.remove("hidden");
    document.getElementById("reader").style.borderColor = "var(--glass-border)";
};

function playAudio(type) {
    let src = "";
    if (type === "valid") src = "https://www.soundjay.com/buttons/sounds/button-unwrap-1.mp3";
    else if (type === "used") src = "https://www.soundjay.com/buttons/sounds/button-8.mp3";
    else src = "https://www.soundjay.com/buttons/sounds/button-10.mp3";

    try {
        const a = new Audio(src);
        a.volume = 0.6;
        a.play().catch(() => {});
    } catch(e) {}
}

window.addEventListener("load", () => {
    startScanner();
});

// --- Fast Metrics & Dashboard Logic ---
function fetchStats() {
    fetch(`${API_BASE}/stats`)
    .then(res => res.json())
    .then(res => {
        if (res.status === "success") {
            const d = res.data;
            document.getElementById("metric-total").innerText = d.total || 0;
            document.getElementById("metric-present").innerText = d.present || 0;
            document.getElementById("metric-pending").innerText = d.pending || 0;
            document.getElementById("metric-percentage").innerText = `${d.percentage || 0}%`;
        }
    })
    .catch(err => console.error("Stats fetch error", err));
}

document.getElementById("btn-refresh-stats").addEventListener("click", () => fetchStats());

// Directory Table Load
document.getElementById("btn-refresh-passes").addEventListener("click", () => fetchPasses());

function fetchPasses() {
    showToast("Loading directory list...");
    
    fetch(`${API_BASE}/passes`)
    .then(res => res.json())
    .then(data => {
        hideToast();
        if (data.status === "success") {
            const tableBody = document.querySelector("#passes-table tbody");
            if (!data.data || data.data.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:2rem; color:var(--text-muted);">No registered participants found in database.</td></tr>`;
                return;
            }

            let rowsHtml = "";
            data.data.forEach(pass => {
                const isUsed = pass.used;
                const badge = isUsed 
                    ? `<span class="badge orange">Present</span>` 
                    : `<span class="badge green">Pending</span>`;
                
                rowsHtml += `
                    <tr>
                        <td><strong>${pass.participant_name || pass.student_name}</strong></td>
                        <td>${pass.team_name || 'N/A'}</td>
                        <td><span style="color:#94a3b8">${pass.branch || 'N/A'}</span></td>
                        <td>${badge}</td>
                        <td>${pass.check_in_time || '-'}</td>
                    </tr>
                `;
            });
            tableBody.innerHTML = rowsHtml;
        }
    })
    .catch(err => {
        hideToast();
        console.error("Error fetching passes", err);
    });
}

// Download QR ZIP
document.getElementById("btn-download-qr").addEventListener("click", () => {
    window.location.href = `${API_BASE}/qr-codes`;
});

// CSV Upload
document.getElementById("btn-upload-csv").addEventListener("click", () => {
    const fileInput = document.getElementById("csv-file");
    if (!fileInput.files.length) return alert("Select a CSV file first");

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    showToast("Uploading CSV...");
    fetch(`${API_BASE}/upload`, { method: "POST", body: formData })
    .then(res => res.json())
    .then(data => {
        hideToast();
        if (data.status === "success") {
            alert(`Uploaded ${data.total_uploaded} participants successfully!`);
            fetchStats();
        } else alert("Error uploading CSV");
    })
    .catch(() => {
        hideToast();
        alert("Server error uploading CSV");
    });
});

// Stealth Unlock (10 taps on main logo) or Auto-unlock if logged in
let clickCount = 0;
const mainLogo = document.getElementById("main-logo");

function unlockManagement() {
    document.querySelectorAll(".management-control").forEach(el => el.classList.remove("hidden"));
}

mainLogo.addEventListener("click", () => {
    clickCount++;
    if (clickCount >= 10) {
        unlockManagement();
        alert("Admin management controls unlocked.");
        clickCount = 0;
    }
});

// Auto-unlock if isLoggedIn is stored in localStorage
window.addEventListener("load", () => {
    if (localStorage.getItem("isLoggedIn") === "true") {
        unlockManagement();
    }
});
