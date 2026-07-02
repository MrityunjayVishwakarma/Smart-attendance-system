document.addEventListener("DOMContentLoaded", async () => {
    const webcam = new WebcamCapture("webcam", "snapshotCanvas", "scanStatus");
    const video = document.getElementById("webcam");
    const overlay = document.getElementById("overlayCanvas");
    const overlayCtx = overlay.getContext("2d");
    const startBtn = document.getElementById("startScanBtn");
    const stopBtn = document.getElementById("stopScanBtn");
    const logEl = document.getElementById("recognitionLog");
    const faceCountEl = document.getElementById("faceCount");
    const lastRecognizedEl = document.getElementById("lastRecognized");
    const toast = document.getElementById("attendanceToast");
    const toastTitle = document.getElementById("toastTitle");
    const toastMessage = document.getElementById("toastMessage");

    const started = await webcam.start();
    if (!started) {
        addLog("Camera Error", "Could not access webcam.", "error");
    }

    let scanning = false;
    let scanTimer = null;
    let busy = false;
    let toastTimer = null;
    const recentLogs = new Map();

    startBtn.addEventListener("click", startScanning);
    stopBtn.addEventListener("click", stopScanning);
    window.addEventListener("resize", syncOverlaySize);

    function startScanning() {
        scanning = true;
        startBtn.classList.add("hidden");
        stopBtn.classList.remove("hidden");
        webcam.setStatus("Live", "success");
        syncOverlaySize();
        scanTimer = setInterval(processFrame, 1500);
        processFrame();
    }

    function stopScanning() {
        scanning = false;
        clearInterval(scanTimer);
        startBtn.classList.remove("hidden");
        stopBtn.classList.add("hidden");
        webcam.setStatus("Idle", "");
        clearOverlay();
        faceCountEl.textContent = "Faces: 0";
        lastRecognizedEl.textContent = "—";
    }

    function syncOverlaySize() {
        if (!video.videoWidth) return;
        overlay.width = video.clientWidth;
        overlay.height = video.clientHeight;
    }

    async function processFrame() {
        if (!scanning || busy) return;
        busy = true;
        syncOverlaySize();

        const image = webcam.captureFrame();
        if (!image) {
            busy = false;
            return;
        }

        try {
            const response = await fetch("/api/recognize-live", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ image }),
            });
            const data = await response.json();

            if (!data.success && data.message) {
                if (!shouldThrottle("error", 8000)) {
                    addLog("Notice", data.message, "warning");
                }
                clearOverlay();
                busy = false;
                return;
            }

            drawFaces(data.faces || [], data.frame_width, data.frame_height);
            faceCountEl.textContent = `Faces: ${(data.faces || []).length}`;

            (data.faces || []).forEach((face) => {
                if (face.recognized) {
                    lastRecognizedEl.textContent = `${face.name} (${face.roll_number})`;
                }
                handleFaceResult(face);
            });
        } catch {
            addLog("Error", "Network error during recognition.", "error");
        } finally {
            busy = false;
        }
    }

    function drawFaces(faces, frameWidth, frameHeight) {
        clearOverlay();
        if (!frameWidth || !frameHeight) return;

        const scaleX = overlay.width / frameWidth;
        const scaleY = overlay.height / frameHeight;

        faces.forEach((face) => {
            const x = face.left * scaleX;
            const y = face.top * scaleY;
            const w = (face.right - face.left) * scaleX;
            const h = (face.bottom - face.top) * scaleY;

            const recognized = face.recognized;
            const color = recognized ? "#10b981" : "#ef4444";

            overlayCtx.strokeStyle = color;
            overlayCtx.lineWidth = 3;
            overlayCtx.strokeRect(x, y, w, h);

            const label = recognized
                ? `${face.name} (${Math.round(face.confidence * 100)}%)`
                : "Unknown";

            overlayCtx.font = "bold 14px Inter, sans-serif";
            const textWidth = overlayCtx.measureText(label).width + 12;
            const labelY = y - 8 > 24 ? y - 8 : y + h + 20;

            overlayCtx.fillStyle = color;
            overlayCtx.fillRect(x, labelY - 20, textWidth, 22);
            overlayCtx.fillStyle = "#ffffff";
            overlayCtx.fillText(label, x + 6, labelY - 4);

            if (face.attendance_marked) {
                overlayCtx.fillStyle = "#3b82f6";
                overlayCtx.fillRect(x, y + h + 4, 160, 22);
                overlayCtx.fillStyle = "#ffffff";
                overlayCtx.font = "bold 12px Inter, sans-serif";
                overlayCtx.fillText("Attendance Marked", x + 6, y + h + 19);
            }
        });
    }

    function clearOverlay() {
        overlayCtx.clearRect(0, 0, overlay.width, overlay.height);
    }

    function handleFaceResult(face) {
        if (!face.recognized) return;

        const key = face.roll_number;
        if (face.attendance_marked) {
            if (shouldThrottle(`marked-${key}`, 15000)) return;
            showToast("Attendance Marked", `${face.name} · Roll ${face.roll_number}`);
            addLog(
                face.name,
                `Attendance Marked · Roll ${face.roll_number} · ${(face.confidence * 100).toFixed(0)}% confidence`,
                "success"
            );
        } else if (face.attendance_message) {
            if (shouldThrottle(`already-${key}`, 20000)) return;
            addLog(face.name, face.attendance_message, "warning");
        }
    }

    function showToast(title, message) {
        toastTitle.textContent = title;
        toastMessage.textContent = message;
        toast.classList.remove("hidden");
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => toast.classList.add("hidden"), 4000);
    }

    function shouldThrottle(key, ms) {
        const last = recentLogs.get(key);
        if (last && Date.now() - last < ms) return true;
        recentLogs.set(key, Date.now());
        return false;
    }

    function addLog(title, message, type) {
        if (logEl.querySelector(".empty-state")) {
            logEl.innerHTML = "";
        }
        const item = document.createElement("div");
        item.className = `log-item ${type}`;
        const time = new Date().toLocaleTimeString();
        item.innerHTML = `<strong>${title}</strong><span>${message} · ${time}</span>`;
        logEl.prepend(item);
    }
});
