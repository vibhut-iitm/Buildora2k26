// --- Supabase Direct Config (for Netlify/static hosting without backend) ---
const SUPABASE_URL = "https://buhqceccffabdvmdybjv.supabase.co";
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ1aHFjZWNjZmZhYmR2bWR5Ymp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODYwOTU0NTEsImV4cCI6MjEwMTY3MTQ1MX0.y6XslDB_PxoRBFvOGXYFguspK151A06oSeforfj41Tk";
const SUPABASE_TABLE = "Buildora2k26";

const SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": `Bearer ${SUPABASE_KEY}`,
    "Content-Type": "application/json"
};

function getApiBase() {
    const saved = localStorage.getItem("API_BASE");
    if (saved && saved.trim()) return saved.trim().replace(/\/+$/, "");

    const isLocal = window.location.hostname === "127.0.0.1" || 
                    window.location.hostname === "localhost" || 
                    window.location.hostname.startsWith("192.168.");

    return isLocal
        ? "http://127.0.0.1:8000"
        : "https://buildora2k26.onrender.com";
}

let API_BASE = getApiBase();
let useDirectSupabase = !API_BASE;

// Test backend connectivity, fallback to direct Supabase if unavailable
async function checkBackendAndFallback() {
    if (!API_BASE) {
        useDirectSupabase = true;
        console.log("No backend configured. Using direct Supabase mode.");
        return;
    }
    try {
        const res = await fetch(`${API_BASE}/health`, { timeout: 3000 });
        if (res.ok) {
            useDirectSupabase = false;
            console.log("Backend is live:", API_BASE);
        } else {
            useDirectSupabase = true;
            console.log("Backend returned error. Falling back to direct Supabase.");
        }
    } catch(e) {
        useDirectSupabase = true;
        console.log("Backend unreachable. Falling back to direct Supabase.");
    }
}


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

// --- Logout Handler ---
function logout() {
    localStorage.removeItem("isLoggedIn");
    window.location.href = "login.html";
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
    if (scannerIsRunning) return;
    const readerEl = document.getElementById("reader");
    if (!readerEl) return;
    readerEl.innerHTML = "";

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
        scannerIsRunning = false;
        console.error("Camera access failed", err);
        readerEl.innerHTML = "<p style='color:#ef4444; padding:20px; text-align:center;'>Camera access denied or unreadable.</p>";
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
        banner.innerText = "✕ UNREGISTERED / FAKE PASS";
        document.getElementById("part-name").innerText = "Unregistered Pass";
        document.getElementById("part-reg-id").innerText = "N/A";
        document.getElementById("part-team").innerText = "N/A";
        document.getElementById("part-college").innerText = "IERT";
        document.getElementById("part-role").innerText = "N/A";
        document.getElementById("part-status-badge").innerHTML = `<span class="badge danger">Unregistered Pass</span>`;
        document.getElementById("checkin-time-row").classList.add("hidden");
        btnMark.classList.add("hidden");
        btnNext.classList.remove("hidden");
        playAudio("invalid");
        return;
    }

    // Populate details
    document.getElementById("part-name").innerText = data.name || data.participant_name || "Unknown";
    document.getElementById("part-reg-id").innerText = data.registration_id || "N/A";
    document.getElementById("part-team").innerText = data.team_name || "N/A";
    document.getElementById("part-college").innerText = data.college || data.college_name || "IERT";
    document.getElementById("part-role").innerText = data.role || "Participant";

    const isAlreadyPresent = data.already_checked_in || data.attendance_status === "Present" || data.status === "used";
    document.getElementById("checkin-time-row").classList.remove("hidden");

    if (isAlreadyPresent) {
        banner.className = "status-banner used";
        banner.innerText = "🚨 ALREADY CHECKED IN — RE-ENTRY DENIED";
        document.getElementById("part-status-badge").innerHTML = `<span class="badge danger">Already Checked In</span>`;
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

// window.addEventListener load handled below

// --- Fast Metrics & Dashboard Logic ---
async function fetchStats() {
    if (useDirectSupabase) {
        return fetchStatsDirectSupabase();
    }
    try {
        const res = await fetch(`${API_BASE}/stats`);
        const data = await res.json();
        if (data.status === "success") {
            const d = data.data;
            document.getElementById("metric-total").innerText = d.total || 0;
            document.getElementById("metric-present").innerText = d.present || 0;
            document.getElementById("metric-pending").innerText = d.pending || 0;
            document.getElementById("metric-percentage").innerText = `${d.percentage || 0}%`;
        }
    } catch(err) {
        console.warn("Backend stats failed, trying direct Supabase...", err);
        return fetchStatsDirectSupabase();
    }
}

async function fetchStatsDirectSupabase() {
    try {
        const res = await fetch(
            `${SUPABASE_URL}/rest/v1/${SUPABASE_TABLE}?select=attendance_status`,
            { headers: SUPABASE_HEADERS }
        );
        const rows = await res.json();
        if (!Array.isArray(rows)) { console.error("Supabase returned non-array:", rows); return; }
        const total = rows.length;
        const present = rows.filter(r => r.attendance_status === "Present" || r.attendance_status === "Checked In").length;
        const pending = total - present;
        const percentage = total > 0 ? Math.round((present / total * 100) * 10) / 10 : 0;
        document.getElementById("metric-total").innerText = total;
        document.getElementById("metric-present").innerText = present;
        document.getElementById("metric-pending").innerText = pending;
        document.getElementById("metric-percentage").innerText = `${percentage}%`;
    } catch(e) {
        console.error("Direct Supabase stats error:", e);
    }
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
document.getElementById("btn-download-qr").addEventListener("click", async () => {
    const btn = document.getElementById("btn-download-qr");
    const originalText = btn.innerText;
    btn.innerText = "⏳ Checking server...";
    btn.disabled = true;

    try {
        // Quick health check before triggering download
        const healthRes = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(5000) });
        if (!healthRes.ok) throw new Error("Backend server is not responding.");

        btn.innerText = "⏳ Download starting...";
        showToast("Opening download — your browser will handle the file. Please wait...");

        // Use direct navigation in a new tab — browser's native download manager
        // handles large files reliably (unlike fetch which can fail on big responses)
        window.open(`${API_BASE}/qr-codes`, "_blank");

        setTimeout(() => {
            hideToast();
            btn.innerText = originalText;
            btn.disabled = false;
        }, 3000);
    } catch (err) {
        hideToast();
        console.error("Download failed:", err);
        alert(`Cannot reach the backend server at:\n${API_BASE}\n\nMake sure the server is running.`);
        btn.innerText = originalText;
        btn.disabled = false;
    }
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

function updateApiDisplay() {
    const disp = document.getElementById("current-api-display");
    const input = document.getElementById("api-url-input");
    if (disp) disp.innerText = API_BASE;
    if (input && localStorage.getItem("API_BASE")) {
        input.value = localStorage.getItem("API_BASE");
    }
}

const btnSaveApi = document.getElementById("btn-save-api-url");
if (btnSaveApi) {
    btnSaveApi.addEventListener("click", () => {
        const inputVal = document.getElementById("api-url-input").value;
        if (!inputVal || !inputVal.trim()) {
            localStorage.removeItem("API_BASE");
            alert("Reset API URL to default.");
        } else {
            let url = inputVal.trim();
            if (!url.startsWith("http://") && !url.startsWith("https://")) {
                url = "https://" + url;
            }
            localStorage.setItem("API_BASE", url);
            alert(`Backend API URL updated to: ${url}`);
        }
        API_BASE = getApiBase();
        updateApiDisplay();
        fetchStats();
        fetchPasses();
    });
}

const btnReset = document.getElementById("btn-reset-db");
if (btnReset) {
    btnReset.addEventListener("click", () => {
        if (!confirm("Are you sure you want to reset all attendance records back to Pending?")) return;
        showToast("Resetting attendance records...");
        fetch(`${API_BASE}/reset`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            hideToast();
            alert(data.message || "Attendance records reset successfully.");
            fetchStats();
            fetchPasses();
        })
        .catch(err => {
            hideToast();
            alert("Error resetting attendance records.");
        });
    });
}

const btnDelete = document.getElementById("btn-delete-db");
if (btnDelete) {
    btnDelete.addEventListener("click", () => {
        if (!confirm("WARNING: Are you sure you want to DELETE ALL participants from the database? This cannot be undone!")) return;
        showToast("Deleting all participants...");
        fetch(`${API_BASE}/delete-all`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            hideToast();
            alert(data.message || "All participants deleted.");
            fetchStats();
            fetchPasses();
        })
        .catch(err => {
            hideToast();
            alert("Error deleting participants.");
        });
    });
}

// Auto-unlock & auto-load stats/passes on window load
window.addEventListener("load", () => {
    unlockManagement();
    updateApiDisplay();
    startScanner();
    fetchStats();
    fetchPasses();
});
