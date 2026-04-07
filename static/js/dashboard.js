document.addEventListener('DOMContentLoaded', () => {
  if (!window.dashboardChartData || typeof Chart === 'undefined') return;
  const ctx = document.getElementById('trendChart');
  if (!ctx) return;

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: window.dashboardChartData.labels,
      datasets: [
        {
          label: 'Stress',
          data: window.dashboardChartData.stress,
          tension: 0.35,
          borderWidth: 3,
        },
        {
          label: 'Energy',
          data: window.dashboardChartData.energy,
          tension: 0.35,
          borderWidth: 3,
        },
        {
          label: 'Sleep',
          data: window.dashboardChartData.sleep,
          tension: 0.35,
          borderWidth: 3,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          min: 0,
          max: 10,
          ticks: { stepSize: 1 }
        }
      }
    }
  });
});
