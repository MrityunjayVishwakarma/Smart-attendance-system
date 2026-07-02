class WebcamCapture {
  constructor(videoId, canvasId, statusId) {
    this.video = document.getElementById(videoId);
    this.canvas = document.getElementById(canvasId);
    this.statusEl = statusId ? document.getElementById(statusId) : null;
    this.stream = null;
    this.capturedImage = null;
  }

  async start() {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Webcam access is not supported by this browser.");
      }
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "user",
          width: { ideal: 640 },
          height: { ideal: 480 },
        },
        audio: false,
      });
      this.video.srcObject = this.stream;
      this.setStatus("Camera ready", "success");
      return true;
    } catch (err) {
      const message =
        err.name === "NotAllowedError" || err.name === "PermissionDeniedError"
          ? "Camera access denied. Allow the webcam and refresh."
          : "Unable to start the camera. Open the browser console for details.";
      this.setStatus(message, "error");
      console.error("Webcam start failed:", err);
      return false;
    }
  }

  stop() {
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }
    if (this.video) {
      this.video.srcObject = null;
    }
  }

  captureFrame() {
    if (!this.video || !this.canvas) return null;

    const width = this.video.videoWidth;
    const height = this.video.videoHeight;
    if (!width || !height) return null;

    this.canvas.width = width;
    this.canvas.height = height;
    const ctx = this.canvas.getContext("2d");
    ctx.drawImage(this.video, 0, 0, width, height);
    this.capturedImage = this.canvas.toDataURL("image/jpeg", 0.85);
    return this.capturedImage;
  }

  getCapturedImage() {
    return this.capturedImage;
  }

  clearCapture() {
    this.capturedImage = null;
  }

  setStatus(text, type) {
    if (!this.statusEl) return;
    this.statusEl.textContent = text;
    this.statusEl.className = "badge";
    if (type) this.statusEl.classList.add(type);
  }
}

window.WebcamCapture = WebcamCapture;
