document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".delete-student").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const row = btn.closest("tr");
            const rollNumber = row.dataset.rollNumber;
            if (!confirm(`Delete student ${rollNumber}? This cannot be undone.`)) return;

            btn.disabled = true;
            try {
                const response = await fetch(`/api/students/${encodeURIComponent(rollNumber)}`, {
                    method: "DELETE",
                });
                const data = await response.json();
                if (data.success) {
                    row.remove();
                } else {
                    alert(data.message || "Delete failed.");
                    btn.disabled = false;
                }
            } catch {
                alert("Network error.");
                btn.disabled = false;
            }
        });
    });
});
