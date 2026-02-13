document.addEventListener("DOMContentLoaded", function () {

    const dataElement = document.getElementById("daily-sales-data");
    if (!dataElement) return;

    const sales = JSON.parse(dataElement.textContent || "[]");

    if (!sales.length) return;

    const labels = sales.map(row => row.sale_date);
    const values = sales.map(row => row.daily_total);

    const ctx = document.getElementById("salesChart");
    if (!ctx) return;

    new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Daily Revenue",
                data: values,
                borderWidth: 2,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

});
