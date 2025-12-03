/**
 * ROSE Link - Chart.js Theme Configuration
 * Main color: #ca2625
 * Font: Alexandria Semi Bold
 * Logo: Logo.webp
 * Icon: icon.webp
 */

import { CHART_THEME } from './config.js';

/**
 * Default Chart.js configuration with ROSE Link branding
 */
export const chartDefaults = {
    // Global font settings
    font: {
        family: CHART_THEME.font.family,
        size: 12,
        weight: CHART_THEME.font.weight,
    },

    // Color settings
    color: CHART_THEME.colors.text,
    borderColor: CHART_THEME.colors.gridLines,
    backgroundColor: CHART_THEME.colors.background,
};

/**
 * Apply ROSE Link theme to Chart.js globally
 * Call this function once when the app initializes
 */
export function applyChartTheme(Chart) {
    if (!Chart) {
        console.warn('Chart.js not loaded, skipping theme application');
        return;
    }

    // Set global defaults
    Chart.defaults.font.family = CHART_THEME.font.family;
    Chart.defaults.font.weight = CHART_THEME.font.weight;
    Chart.defaults.color = CHART_THEME.colors.text;

    // Plugin defaults
    Chart.defaults.plugins.legend.labels.font = {
        family: CHART_THEME.font.family,
        weight: CHART_THEME.font.weight,
        size: 12,
    };
    Chart.defaults.plugins.legend.labels.color = CHART_THEME.colors.text;

    Chart.defaults.plugins.title.font = {
        family: CHART_THEME.font.family,
        weight: 700,
        size: 16,
    };
    Chart.defaults.plugins.title.color = CHART_THEME.colors.text;

    Chart.defaults.plugins.tooltip.titleFont = {
        family: CHART_THEME.font.family,
        weight: CHART_THEME.font.weight,
    };
    Chart.defaults.plugins.tooltip.bodyFont = {
        family: CHART_THEME.font.family,
    };
    Chart.defaults.plugins.tooltip.backgroundColor = CHART_THEME.colors.background;
    Chart.defaults.plugins.tooltip.borderColor = CHART_THEME.colors.primary;
    Chart.defaults.plugins.tooltip.borderWidth = 1;

    // Scale defaults
    Chart.defaults.scale.grid.color = CHART_THEME.colors.gridLines;
    Chart.defaults.scale.ticks.color = CHART_THEME.colors.textSecondary;
}

/**
 * Create a line chart configuration with ROSE Link styling
 * @param {Object} options - Chart options
 * @returns {Object} Chart.js configuration object
 */
export function createLineChartConfig(options = {}) {
    const {
        labels = [],
        data = [],
        label = 'Data',
        showLegend = true,
        title = '',
        yAxisLabel = '',
        xAxisLabel = '',
        fill = true,
    } = options;

    return {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label,
                data,
                borderColor: CHART_THEME.colors.primary,
                backgroundColor: fill
                    ? createGradient(CHART_THEME.colors.primary, CHART_THEME.colors.background)
                    : 'transparent',
                borderWidth: 2,
                tension: 0.4,
                fill: fill,
                pointBackgroundColor: CHART_THEME.colors.primary,
                pointBorderColor: CHART_THEME.colors.primary,
                pointHoverBackgroundColor: CHART_THEME.colors.primaryLight,
                pointHoverBorderColor: CHART_THEME.colors.primaryLight,
                pointRadius: 3,
                pointHoverRadius: 5,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: showLegend,
                    position: 'top',
                },
                title: {
                    display: !!title,
                    text: title,
                },
            },
            scales: {
                x: {
                    title: {
                        display: !!xAxisLabel,
                        text: xAxisLabel,
                        color: CHART_THEME.colors.text,
                    },
                    grid: {
                        color: CHART_THEME.colors.gridLines,
                    },
                    ticks: {
                        color: CHART_THEME.colors.textSecondary,
                    },
                },
                y: {
                    title: {
                        display: !!yAxisLabel,
                        text: yAxisLabel,
                        color: CHART_THEME.colors.text,
                    },
                    grid: {
                        color: CHART_THEME.colors.gridLines,
                    },
                    ticks: {
                        color: CHART_THEME.colors.textSecondary,
                    },
                    beginAtZero: true,
                },
            },
        },
    };
}

/**
 * Create a bar chart configuration with ROSE Link styling
 * @param {Object} options - Chart options
 * @returns {Object} Chart.js configuration object
 */
export function createBarChartConfig(options = {}) {
    const {
        labels = [],
        data = [],
        label = 'Data',
        showLegend = true,
        title = '',
        horizontal = false,
    } = options;

    return {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label,
                data,
                backgroundColor: CHART_THEME.palette,
                borderColor: CHART_THEME.colors.primary,
                borderWidth: 1,
                borderRadius: 4,
            }],
        },
        options: {
            indexAxis: horizontal ? 'y' : 'x',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: showLegend,
                    position: 'top',
                },
                title: {
                    display: !!title,
                    text: title,
                },
            },
            scales: {
                x: {
                    grid: {
                        color: CHART_THEME.colors.gridLines,
                    },
                    ticks: {
                        color: CHART_THEME.colors.textSecondary,
                    },
                },
                y: {
                    grid: {
                        color: CHART_THEME.colors.gridLines,
                    },
                    ticks: {
                        color: CHART_THEME.colors.textSecondary,
                    },
                    beginAtZero: true,
                },
            },
        },
    };
}

/**
 * Create a doughnut/pie chart configuration with ROSE Link styling
 * @param {Object} options - Chart options
 * @returns {Object} Chart.js configuration object
 */
export function createDoughnutChartConfig(options = {}) {
    const {
        labels = [],
        data = [],
        title = '',
        showLegend = true,
        cutout = '60%', // Use '0%' for pie chart
    } = options;

    return {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: CHART_THEME.palette,
                borderColor: CHART_THEME.colors.background,
                borderWidth: 2,
                hoverBorderColor: CHART_THEME.colors.primary,
                hoverBorderWidth: 3,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout,
            plugins: {
                legend: {
                    display: showLegend,
                    position: 'right',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle',
                    },
                },
                title: {
                    display: !!title,
                    text: title,
                },
            },
        },
    };
}

/**
 * Create a gradient for chart backgrounds
 * @param {string} colorStart - Start color (hex)
 * @param {string} colorEnd - End color (hex)
 * @returns {Function} Gradient creator function for Chart.js
 */
export function createGradient(colorStart, colorEnd) {
    return (context) => {
        const chart = context.chart;
        const { ctx, chartArea } = chart;

        if (!chartArea) {
            return colorStart;
        }

        const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
        gradient.addColorStop(0, hexToRgba(colorEnd, 0.1));
        gradient.addColorStop(1, hexToRgba(colorStart, 0.4));
        return gradient;
    };
}

/**
 * Convert hex color to rgba
 * @param {string} hex - Hex color code
 * @param {number} alpha - Alpha value (0-1)
 * @returns {string} RGBA color string
 */
function hexToRgba(hex, alpha = 1) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/**
 * Bandwidth chart specific configuration
 * For network statistics display
 */
export function createBandwidthChartConfig(options = {}) {
    const {
        labels = [],
        downloadData = [],
        uploadData = [],
        title = 'Bandwidth Usage',
    } = options;

    return {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Download',
                    data: downloadData,
                    borderColor: CHART_THEME.colors.primary,
                    backgroundColor: createGradient(CHART_THEME.colors.primary, CHART_THEME.colors.background),
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 2,
                },
                {
                    label: 'Upload',
                    data: uploadData,
                    borderColor: CHART_THEME.colors.primaryLight,
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false,
                    pointRadius: 2,
                    borderDash: [5, 5],
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                },
                title: {
                    display: !!title,
                    text: title,
                },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const value = context.parsed.y;
                            return `${context.dataset.label}: ${formatBytes(value)}/s`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Time',
                        color: CHART_THEME.colors.text,
                    },
                    grid: {
                        color: CHART_THEME.colors.gridLines,
                    },
                    ticks: {
                        color: CHART_THEME.colors.textSecondary,
                        maxRotation: 45,
                    },
                },
                y: {
                    title: {
                        display: true,
                        text: 'Bandwidth',
                        color: CHART_THEME.colors.text,
                    },
                    grid: {
                        color: CHART_THEME.colors.gridLines,
                    },
                    ticks: {
                        color: CHART_THEME.colors.textSecondary,
                        callback: (value) => formatBytes(value),
                    },
                    beginAtZero: true,
                },
            },
        },
    };
}

/**
 * Format bytes to human readable format
 * @param {number} bytes - Bytes value
 * @returns {string} Formatted string
 */
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Export theme colors for external use
export { CHART_THEME };
