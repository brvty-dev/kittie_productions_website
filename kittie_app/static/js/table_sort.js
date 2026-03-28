document.addEventListener("DOMContentLoaded", function () {

    const tbody = document.querySelector("table tbody");
    const rows = Array.from(tbody.querySelectorAll("tr"));

    rows.sort((a, b) => {
        const dateA = new Date(a.cells[0].textContent.trim());
        const dateB = new Date(b.cells[0].textContent.trim());
        return dateB - dateA; // newest first
    });

    rows.forEach(row => tbody.appendChild(row));

});