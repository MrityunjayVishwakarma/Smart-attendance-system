document.addEventListener("DOMContentLoaded", async () => {
  const webcam = new WebcamCapture("webcam", "snapshotCanvas", "cameraStatus");
  const started = await webcam.start();
  if (!started) {
    showAlert("Camera access is required for face registration.", "error");
  }

  const captureBtn = document.getElementById("captureBtn");
  const retakeBtn = document.getElementById("retakeBtn");
  const registerBtn = document.getElementById("registerBtn");
  const registerForm = document.getElementById("registerForm");
  const statusBox = document.getElementById("registerStatus");
  const alertBox = document.getElementById("alertBox");
  const capturePreview = document.getElementById("capturePreview");
  const previewImg = document.getElementById("previewImg");

  captureBtn.addEventListener("click", () => {
    clearFieldErrors();
    const image = webcam.captureFrame();
    if (!image) {
      setFieldError(
        "image",
        "Could not capture frame. Wait for the camera to load.",
      );
      showAlert(
        "Could not capture frame. Please wait for the camera.",
        "error",
      );
      return;
    }

    previewImg.src = image;
    capturePreview.classList.remove("hidden");
    registerBtn.disabled = false;
    retakeBtn.disabled = false;
    webcam.setStatus("Face captured", "success");
    showAlert(
      "Face captured successfully. You can now register the student.",
      "success",
    );
    hideStatusBox();
  });

  retakeBtn.addEventListener("click", () => {
    webcam.clearCapture();
    registerBtn.disabled = true;
    retakeBtn.disabled = true;
    capturePreview.classList.add("hidden");
    previewImg.src = "";
    webcam.setStatus("Camera ready", "success");
    clearFieldErrors();
    hideAlert();
    hideStatusBox();
  });

  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearFieldErrors();
    hideAlert();
    hideStatusBox();

    const name = document.getElementById("name").value.trim();
    const rollNumber = document.getElementById("roll_number").value.trim();
    const image = webcam.getCapturedImage();

    const clientErrors = validateForm(name, rollNumber, image);
    if (Object.keys(clientErrors).length > 0) {
      applyFieldErrors(clientErrors);
      showAlert("Please fix the highlighted fields.", "error");
      return;
    }

    registerBtn.disabled = true;
    registerBtn.textContent = "Registering...";

    try {
      const apiUrl = "/api/register-student";
      console.debug(
        "Register request to",
        apiUrl,
        "origin",
        window.location.origin,
      );
      console.debug("Register payload", {
        name,
        roll_number: rollNumber,
        imageLength: image?.length,
      });
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ name, roll_number: rollNumber, image }),
      });

      const contentType = response.headers.get("content-type") || "";
      let data;

      if (contentType.includes("application/json")) {
        data = await response.json();
      } else {
        const text = await response.text();
        console.error(
          "Unexpected register response headers:",
          Object.fromEntries(response.headers.entries()),
        );
        const message = text.includes("<html")
          ? "Session expired or login required. Please refresh and log in again."
          : "Unexpected response from the server.";
        console.error("Unexpected register response:", response.status, text);
        throw new Error(message);
      }

      if (response.ok && data.success) {
        const detail = data.data
          ? ` Roll: ${data.data.roll_number} · Saved to ${data.data.image_path}`
          : "";
        showAlert(data.message + detail, "success");
        showStatus(data.message, "success");
        registerForm.reset();
        webcam.clearCapture();
        capturePreview.classList.add("hidden");
        previewImg.src = "";
        retakeBtn.disabled = true;
        registerBtn.disabled = true;
        webcam.setStatus("Camera ready", "success");
        return;
      }

      console.error("Register request failed:", response.status, data);
      if (data.errors) {
        applyFieldErrors(data.errors);
      }
      showAlert(data.message || "Registration failed.", "error");
      showStatus(data.message || "Registration failed.", "error");
    } catch (err) {
      console.error("Register fetch error:", err);
      const message =
        err?.message || "Network error. Check your connection and try again.";
      showAlert(message, "error");
      showStatus(message, "error");
    } finally {
      registerBtn.disabled = !webcam.getCapturedImage();
      registerBtn.textContent = "Register Student";
    }
  });

  function validateForm(name, rollNumber, image) {
    const errors = {};
    if (!name || name.length < 2) {
      errors.name = "Name must be at least 2 characters.";
    }
    if (!rollNumber) {
      errors.roll_number = "Roll number is required.";
    } else if (!/^[A-Za-z0-9_-]{2,20}$/.test(rollNumber)) {
      errors.roll_number =
        "Use 2–20 letters, numbers, hyphens, or underscores.";
    }
    if (!image || !image.startsWith("data:image/") || image.length < 500) {
      errors.image = "Please capture a valid face image first.";
    }
    return errors;
  }

  function setFieldError(field, message) {
    const el = document.getElementById(`error-${field}`);
    if (el) {
      el.textContent = message;
      el.classList.remove("hidden");
    }
    const input = document.getElementById(field);
    if (input) input.classList.add("input-error");
  }

  function applyFieldErrors(errors) {
    Object.entries(errors).forEach(([field, message]) =>
      setFieldError(field, message),
    );
  }

  function clearFieldErrors() {
    document.querySelectorAll(".field-error").forEach((el) => {
      el.textContent = "";
      el.classList.add("hidden");
    });
    document
      .querySelectorAll(".input-error")
      .forEach((el) => el.classList.remove("input-error"));
  }

  function showAlert(message, type) {
    alertBox.textContent = message;
    alertBox.className = `alert-banner alert-${type}`;
    alertBox.classList.remove("hidden");
  }

  function hideAlert() {
    alertBox.classList.add("hidden");
  }

  function showStatus(message, type) {
    statusBox.textContent = message;
    statusBox.className = `status-box ${type}`;
    statusBox.classList.remove("hidden");
  }

  function hideStatusBox() {
    statusBox.classList.add("hidden");
  }
});
