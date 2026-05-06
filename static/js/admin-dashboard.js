'use strict';

document.addEventListener('DOMContentLoaded', function () {
  var dataNode = document.getElementById('dashboard-chart-data');
  if (!dataNode || typeof ApexCharts === 'undefined') {
    return;
  }

  var chartData = {};
  try {
    chartData = JSON.parse(dataNode.textContent || '{}');
  } catch (error) {
    return;
  }

  var colors = (window.config && window.config.colors) || {};
  var palette = {
    primary: colors.primary || '#696cff',
    success: colors.success || '#71dd37',
    danger: colors.danger || '#ff3e1d',
    warning: colors.warning || '#ffab00',
    info: colors.info || '#03c3ec',
    muted: (colors.textMuted || '#8592a3')
  };

  function renderChart(selector, options) {
    var el = document.querySelector(selector);
    if (!el) {
      return;
    }
    var chart = new ApexCharts(el, options);
    chart.render();
  }

  renderChart('#adminChartTrend', {
    chart: { type: 'area', height: 300, toolbar: { show: false } },
    series: [
      { name: 'Etudiants', data: chartData.series_etudiants || [] },
      { name: 'Documents', data: chartData.series_documents || [] }
    ],
    stroke: { curve: 'smooth', width: 3 },
    fill: { type: 'gradient', gradient: { shadeIntensity: 0.4, opacityFrom: 0.35, opacityTo: 0.05, stops: [0, 90, 100] } },
    colors: [palette.primary, palette.info],
    xaxis: { categories: chartData.labels_months || [] },
    yaxis: { min: 0, forceNiceScale: true },
    dataLabels: { enabled: false },
    legend: { position: 'top' },
    grid: { strokeDashArray: 6 }
  });

  renderChart('#adminChartDocumentsDonut', {
    chart: { type: 'donut', height: 260 },
    labels: ['Publies', 'En attente'],
    series: chartData.documents_split || [0, 0],
    colors: [palette.success, palette.danger],
    legend: { show: false },
    dataLabels: { enabled: true },
    stroke: { width: 0 },
    plotOptions: { pie: { donut: { size: '72%' } } }
  });

  renderChart('#adminChartFilieres', {
    chart: { type: 'bar', height: 290, toolbar: { show: false } },
    series: [{ name: 'Etudiants', data: chartData.filieres_values || [] }],
    colors: [palette.warning],
    plotOptions: { bar: { borderRadius: 6, horizontal: true, barHeight: '58%' } },
    xaxis: { categories: chartData.filieres_labels || [] },
    dataLabels: { enabled: false },
    grid: { strokeDashArray: 5 }
  });

  renderChart('#adminChartTransport', {
    chart: { type: 'radialBar', height: 260 },
    series: [chartData.transport_occupation || 0],
    labels: ['Taux occupation'],
    colors: [palette.primary],
    plotOptions: {
      radialBar: {
        hollow: { size: '62%' },
        track: { background: '#ecf1f7' },
        dataLabels: {
          value: { formatter: function (value) { return Math.round(value) + '%'; } }
        }
      }
    }
  });
});
