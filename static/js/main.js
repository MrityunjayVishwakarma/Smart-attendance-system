document.addEventListener("DOMContentLoaded", () => {
    const flashes = document.querySelectorAll(".flash");
    flashes.forEach((flash) => {
        setTimeout(() => {
            flash.style.opacity = "0";
            flash.style.transition = "opacity 0.3s";
            setTimeout(() => flash.remove(), 300);
        }, 4000);
    });
});
