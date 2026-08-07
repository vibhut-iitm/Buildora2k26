const resultBox = document.getElementById("result");

function onScanSuccess(decodedText) {
    resultBox.innerHTML = "Checking...";

    verifyToken(decodedText).then(data => {
        if (data.status === "valid") {
            resultBox.innerHTML = `<span class="text-success">Entry Allowed<br>${data.name}</span>`;
        } else if (data.status === "used") {
            resultBox.innerHTML = `<span class="text-warning">Already Used</span>`;
        } else {
            resultBox.innerHTML = `<span class="text-danger">Invalid Pass</span>`;
        }
    }).catch(() => {
        resultBox.innerHTML = `<span class="text-danger">Error</span>`;
    });
}

const html5QrCode = new Html5Qrcode("reader");
html5QrCode.start(
    { facingMode: "environment" },
    { fps: 10, qrbox: 250 },
    onScanSuccess
);