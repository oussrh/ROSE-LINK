/**
 * Tests for Chart Theme Module
 */

import {
    chartDefaults,
    applyChartTheme,
    createLineChartConfig,
    createBarChartConfig,
    createDoughnutChartConfig,
    createGradient,
    createBandwidthChartConfig,
    CHART_THEME
} from '../js/chartTheme.js';

describe('Chart Theme Module', () => {
    describe('chartDefaults', () => {
        it('should export chart defaults object', () => {
            expect(chartDefaults).toBeDefined();
        });

        it('should have font configuration', () => {
            expect(chartDefaults.font).toBeDefined();
            expect(chartDefaults.font.family).toContain('Alexandria');
            expect(chartDefaults.font.size).toBe(12);
            expect(chartDefaults.font.weight).toBe(600);
        });

        it('should have color settings', () => {
            expect(chartDefaults.color).toBe(CHART_THEME.colors.text);
            expect(chartDefaults.borderColor).toBe(CHART_THEME.colors.gridLines);
            expect(chartDefaults.backgroundColor).toBe(CHART_THEME.colors.background);
        });
    });

    describe('applyChartTheme', () => {
        it('should handle null Chart instance gracefully', () => {
            const originalWarn = console.warn;
            console.warn = jest.fn();

            applyChartTheme(null);

            expect(console.warn).toHaveBeenCalledWith('Chart.js not loaded, skipping theme application');

            console.warn = originalWarn;
        });

        it('should handle undefined Chart instance gracefully', () => {
            const originalWarn = console.warn;
            console.warn = jest.fn();

            applyChartTheme(undefined);

            expect(console.warn).toHaveBeenCalledWith('Chart.js not loaded, skipping theme application');

            console.warn = originalWarn;
        });

        it('should apply theme to Chart.js defaults', () => {
            const mockChart = {
                defaults: {
                    font: {},
                    color: null,
                    plugins: {
                        legend: { labels: {} },
                        title: {},
                        tooltip: {}
                    },
                    scale: {
                        grid: {},
                        ticks: {}
                    }
                }
            };

            applyChartTheme(mockChart);

            expect(mockChart.defaults.font.family).toContain('Alexandria');
            expect(mockChart.defaults.font.weight).toBe(600);
            expect(mockChart.defaults.color).toBe(CHART_THEME.colors.text);
        });

        it('should configure legend labels', () => {
            const mockChart = {
                defaults: {
                    font: {},
                    color: null,
                    plugins: {
                        legend: { labels: {} },
                        title: {},
                        tooltip: {}
                    },
                    scale: {
                        grid: {},
                        ticks: {}
                    }
                }
            };

            applyChartTheme(mockChart);

            expect(mockChart.defaults.plugins.legend.labels.font).toBeDefined();
            expect(mockChart.defaults.plugins.legend.labels.font.family).toContain('Alexandria');
            expect(mockChart.defaults.plugins.legend.labels.color).toBe(CHART_THEME.colors.text);
        });

        it('should configure title settings', () => {
            const mockChart = {
                defaults: {
                    font: {},
                    color: null,
                    plugins: {
                        legend: { labels: {} },
                        title: {},
                        tooltip: {}
                    },
                    scale: {
                        grid: {},
                        ticks: {}
                    }
                }
            };

            applyChartTheme(mockChart);

            expect(mockChart.defaults.plugins.title.font).toBeDefined();
            expect(mockChart.defaults.plugins.title.font.weight).toBe(700);
            expect(mockChart.defaults.plugins.title.font.size).toBe(16);
            expect(mockChart.defaults.plugins.title.color).toBe(CHART_THEME.colors.text);
        });

        it('should configure tooltip settings', () => {
            const mockChart = {
                defaults: {
                    font: {},
                    color: null,
                    plugins: {
                        legend: { labels: {} },
                        title: {},
                        tooltip: {}
                    },
                    scale: {
                        grid: {},
                        ticks: {}
                    }
                }
            };

            applyChartTheme(mockChart);

            expect(mockChart.defaults.plugins.tooltip.titleFont).toBeDefined();
            expect(mockChart.defaults.plugins.tooltip.bodyFont).toBeDefined();
            expect(mockChart.defaults.plugins.tooltip.backgroundColor).toBe(CHART_THEME.colors.background);
            expect(mockChart.defaults.plugins.tooltip.borderColor).toBe(CHART_THEME.colors.primary);
            expect(mockChart.defaults.plugins.tooltip.borderWidth).toBe(1);
        });

        it('should configure scale defaults', () => {
            const mockChart = {
                defaults: {
                    font: {},
                    color: null,
                    plugins: {
                        legend: { labels: {} },
                        title: {},
                        tooltip: {}
                    },
                    scale: {
                        grid: {},
                        ticks: {}
                    }
                }
            };

            applyChartTheme(mockChart);

            expect(mockChart.defaults.scale.grid.color).toBe(CHART_THEME.colors.gridLines);
            expect(mockChart.defaults.scale.ticks.color).toBe(CHART_THEME.colors.textSecondary);
        });
    });

    describe('createLineChartConfig', () => {
        it('should return a line chart configuration', () => {
            const config = createLineChartConfig();

            expect(config.type).toBe('line');
            expect(config.data).toBeDefined();
            expect(config.options).toBeDefined();
        });

        it('should use default options when none provided', () => {
            const config = createLineChartConfig();

            expect(config.data.labels).toEqual([]);
            expect(config.data.datasets[0].data).toEqual([]);
            expect(config.data.datasets[0].label).toBe('Data');
        });

        it('should accept custom options', () => {
            const options = {
                labels: ['Jan', 'Feb', 'Mar'],
                data: [10, 20, 30],
                label: 'Sales',
                showLegend: false,
                title: 'Monthly Sales',
                yAxisLabel: 'Amount',
                xAxisLabel: 'Month',
                fill: false
            };

            const config = createLineChartConfig(options);

            expect(config.data.labels).toEqual(['Jan', 'Feb', 'Mar']);
            expect(config.data.datasets[0].data).toEqual([10, 20, 30]);
            expect(config.data.datasets[0].label).toBe('Sales');
            expect(config.options.plugins.legend.display).toBe(false);
            expect(config.options.plugins.title.display).toBe(true);
            expect(config.options.plugins.title.text).toBe('Monthly Sales');
        });

        it('should configure chart styling with ROSE theme colors', () => {
            const config = createLineChartConfig();

            expect(config.data.datasets[0].borderColor).toBe(CHART_THEME.colors.primary);
            expect(config.data.datasets[0].pointBackgroundColor).toBe(CHART_THEME.colors.primary);
            expect(config.data.datasets[0].borderWidth).toBe(2);
            expect(config.data.datasets[0].tension).toBe(0.4);
        });

        it('should set fill based on option', () => {
            const configWithFill = createLineChartConfig({ fill: true });
            const configWithoutFill = createLineChartConfig({ fill: false });

            expect(configWithFill.data.datasets[0].fill).toBe(true);
            expect(configWithoutFill.data.datasets[0].fill).toBe(false);
            expect(configWithoutFill.data.datasets[0].backgroundColor).toBe('transparent');
        });

        it('should configure axes labels when provided', () => {
            const config = createLineChartConfig({
                xAxisLabel: 'Time',
                yAxisLabel: 'Value'
            });

            expect(config.options.scales.x.title.display).toBe(true);
            expect(config.options.scales.x.title.text).toBe('Time');
            expect(config.options.scales.y.title.display).toBe(true);
            expect(config.options.scales.y.title.text).toBe('Value');
        });

        it('should not display axes labels when not provided', () => {
            const config = createLineChartConfig({});

            expect(config.options.scales.x.title.display).toBe(false);
            expect(config.options.scales.y.title.display).toBe(false);
        });

        it('should not display title when not provided', () => {
            const config = createLineChartConfig({});

            expect(config.options.plugins.title.display).toBe(false);
        });
    });

    describe('createBarChartConfig', () => {
        it('should return a bar chart configuration', () => {
            const config = createBarChartConfig();

            expect(config.type).toBe('bar');
            expect(config.data).toBeDefined();
            expect(config.options).toBeDefined();
        });

        it('should use default options when none provided', () => {
            const config = createBarChartConfig();

            expect(config.data.labels).toEqual([]);
            expect(config.data.datasets[0].data).toEqual([]);
            expect(config.data.datasets[0].label).toBe('Data');
        });

        it('should accept custom options', () => {
            const options = {
                labels: ['A', 'B', 'C'],
                data: [100, 200, 300],
                label: 'Categories',
                showLegend: false,
                title: 'Category Chart',
                horizontal: true
            };

            const config = createBarChartConfig(options);

            expect(config.data.labels).toEqual(['A', 'B', 'C']);
            expect(config.data.datasets[0].data).toEqual([100, 200, 300]);
            expect(config.data.datasets[0].label).toBe('Categories');
            expect(config.options.plugins.legend.display).toBe(false);
            expect(config.options.indexAxis).toBe('y');
        });

        it('should use palette colors for background', () => {
            const config = createBarChartConfig();

            expect(config.data.datasets[0].backgroundColor).toEqual(CHART_THEME.palette);
        });

        it('should set vertical orientation by default', () => {
            const config = createBarChartConfig();

            expect(config.options.indexAxis).toBe('x');
        });

        it('should set horizontal orientation when specified', () => {
            const config = createBarChartConfig({ horizontal: true });

            expect(config.options.indexAxis).toBe('y');
        });

        it('should configure bar styling', () => {
            const config = createBarChartConfig();

            expect(config.data.datasets[0].borderColor).toBe(CHART_THEME.colors.primary);
            expect(config.data.datasets[0].borderWidth).toBe(1);
            expect(config.data.datasets[0].borderRadius).toBe(4);
        });

        it('should display title when provided', () => {
            const config = createBarChartConfig({ title: 'My Chart' });

            expect(config.options.plugins.title.display).toBe(true);
            expect(config.options.plugins.title.text).toBe('My Chart');
        });
    });

    describe('createDoughnutChartConfig', () => {
        it('should return a doughnut chart configuration', () => {
            const config = createDoughnutChartConfig();

            expect(config.type).toBe('doughnut');
            expect(config.data).toBeDefined();
            expect(config.options).toBeDefined();
        });

        it('should use default options when none provided', () => {
            const config = createDoughnutChartConfig();

            expect(config.data.labels).toEqual([]);
            expect(config.data.datasets[0].data).toEqual([]);
            expect(config.options.cutout).toBe('60%');
        });

        it('should accept custom options', () => {
            const options = {
                labels: ['Red', 'Blue', 'Green'],
                data: [30, 40, 30],
                title: 'Distribution',
                showLegend: false,
                cutout: '0%' // Pie chart
            };

            const config = createDoughnutChartConfig(options);

            expect(config.data.labels).toEqual(['Red', 'Blue', 'Green']);
            expect(config.data.datasets[0].data).toEqual([30, 40, 30]);
            expect(config.options.plugins.legend.display).toBe(false);
            expect(config.options.cutout).toBe('0%');
        });

        it('should use palette colors', () => {
            const config = createDoughnutChartConfig();

            expect(config.data.datasets[0].backgroundColor).toEqual(CHART_THEME.palette);
        });

        it('should configure legend position to right', () => {
            const config = createDoughnutChartConfig();

            expect(config.options.plugins.legend.position).toBe('right');
            expect(config.options.plugins.legend.labels.padding).toBe(20);
            expect(config.options.plugins.legend.labels.usePointStyle).toBe(true);
        });

        it('should configure hover effects', () => {
            const config = createDoughnutChartConfig();

            expect(config.data.datasets[0].hoverBorderColor).toBe(CHART_THEME.colors.primary);
            expect(config.data.datasets[0].hoverBorderWidth).toBe(3);
        });
    });

    describe('createGradient', () => {
        it('should return a function', () => {
            const gradient = createGradient('#ca2625', '#1f2937');

            expect(typeof gradient).toBe('function');
        });

        it('should return start color when chartArea is not available', () => {
            const gradient = createGradient('#ca2625', '#1f2937');
            const mockContext = {
                chart: {
                    ctx: {},
                    chartArea: null
                }
            };

            const result = gradient(mockContext);

            expect(result).toBe('#ca2625');
        });

        it('should create a gradient when chartArea is available', () => {
            const gradient = createGradient('#ca2625', '#1f2937');
            const mockGradient = {
                addColorStop: jest.fn()
            };
            const mockContext = {
                chart: {
                    ctx: {
                        createLinearGradient: jest.fn(() => mockGradient)
                    },
                    chartArea: {
                        top: 0,
                        bottom: 100
                    }
                }
            };

            const result = gradient(mockContext);

            expect(mockContext.chart.ctx.createLinearGradient).toHaveBeenCalledWith(0, 100, 0, 0);
            expect(mockGradient.addColorStop).toHaveBeenCalledTimes(2);
            expect(result).toBe(mockGradient);
        });
    });

    describe('createBandwidthChartConfig', () => {
        it('should return a bandwidth chart configuration', () => {
            const config = createBandwidthChartConfig();

            expect(config.type).toBe('line');
            expect(config.data).toBeDefined();
            expect(config.options).toBeDefined();
        });

        it('should have two datasets for download and upload', () => {
            const config = createBandwidthChartConfig();

            expect(config.data.datasets.length).toBe(2);
            expect(config.data.datasets[0].label).toBe('Download');
            expect(config.data.datasets[1].label).toBe('Upload');
        });

        it('should accept custom options', () => {
            const options = {
                labels: ['10:00', '10:01', '10:02'],
                downloadData: [1000, 2000, 1500],
                uploadData: [500, 600, 550],
                title: 'Network Stats'
            };

            const config = createBandwidthChartConfig(options);

            expect(config.data.labels).toEqual(['10:00', '10:01', '10:02']);
            expect(config.data.datasets[0].data).toEqual([1000, 2000, 1500]);
            expect(config.data.datasets[1].data).toEqual([500, 600, 550]);
            expect(config.options.plugins.title.text).toBe('Network Stats');
        });

        it('should configure download dataset with primary color', () => {
            const config = createBandwidthChartConfig();

            expect(config.data.datasets[0].borderColor).toBe(CHART_THEME.colors.primary);
            expect(config.data.datasets[0].fill).toBe(true);
        });

        it('should configure upload dataset with dashed line', () => {
            const config = createBandwidthChartConfig();

            expect(config.data.datasets[1].borderColor).toBe(CHART_THEME.colors.primaryLight);
            expect(config.data.datasets[1].borderDash).toEqual([5, 5]);
            expect(config.data.datasets[1].fill).toBe(false);
        });

        it('should have tooltip callback for formatting bytes', () => {
            const config = createBandwidthChartConfig();
            const callback = config.options.plugins.tooltip.callbacks.label;

            expect(typeof callback).toBe('function');

            // Test the callback
            const mockContext = {
                parsed: { y: 1024 },
                dataset: { label: 'Download' }
            };
            const result = callback(mockContext);

            expect(result).toBe('Download: 1 KB/s');
        });

        it('should have y-axis tick callback for formatting bytes', () => {
            const config = createBandwidthChartConfig();
            const callback = config.options.scales.y.ticks.callback;

            expect(typeof callback).toBe('function');

            // Test the callback
            expect(callback(0)).toBe('0 B');
            expect(callback(1024)).toBe('1 KB');
            expect(callback(1048576)).toBe('1 MB');
            expect(callback(1073741824)).toBe('1 GB');
        });

        it('should configure interaction mode to index', () => {
            const config = createBandwidthChartConfig();

            expect(config.options.interaction.mode).toBe('index');
            expect(config.options.interaction.intersect).toBe(false);
        });

        it('should display x-axis label', () => {
            const config = createBandwidthChartConfig();

            expect(config.options.scales.x.title.display).toBe(true);
            expect(config.options.scales.x.title.text).toBe('Time');
        });

        it('should display y-axis label', () => {
            const config = createBandwidthChartConfig();

            expect(config.options.scales.y.title.display).toBe(true);
            expect(config.options.scales.y.title.text).toBe('Bandwidth');
        });

        it('should not display title when not provided', () => {
            const config = createBandwidthChartConfig({ title: '' });

            expect(config.options.plugins.title.display).toBe(false);
        });

        it('should display title when provided', () => {
            const config = createBandwidthChartConfig({ title: 'Network' });

            expect(config.options.plugins.title.display).toBe(true);
        });
    });

    describe('CHART_THEME re-export', () => {
        it('should re-export CHART_THEME from config', () => {
            expect(CHART_THEME).toBeDefined();
            expect(CHART_THEME.primaryColor).toBe('#ca2625');
            expect(CHART_THEME.colors).toBeDefined();
            expect(CHART_THEME.palette).toBeDefined();
        });
    });

    describe('formatBytes helper (internal)', () => {
        // We test this through the bandwidth chart tooltip callback
        it('should format bytes correctly through bandwidth chart', () => {
            const config = createBandwidthChartConfig();
            const callback = config.options.scales.y.ticks.callback;

            expect(callback(0)).toBe('0 B');
            expect(callback(512)).toBe('512 B');
            expect(callback(1024)).toBe('1 KB');
            expect(callback(1536)).toBe('1.5 KB');
            expect(callback(1048576)).toBe('1 MB');
            expect(callback(1073741824)).toBe('1 GB');
            expect(callback(1099511627776)).toBe('1 TB');
        });
    });

    describe('hexToRgba helper (internal)', () => {
        // We test this through the gradient function which uses hexToRgba internally
        it('should convert hex to rgba through gradient', () => {
            const gradient = createGradient('#ff0000', '#00ff00');
            const mockGradient = {
                addColorStop: jest.fn()
            };
            const mockContext = {
                chart: {
                    ctx: {
                        createLinearGradient: jest.fn(() => mockGradient)
                    },
                    chartArea: {
                        top: 0,
                        bottom: 100
                    }
                }
            };

            gradient(mockContext);

            // Check that addColorStop was called with rgba values
            expect(mockGradient.addColorStop).toHaveBeenCalledWith(0, expect.stringMatching(/rgba\(\d+,\s*\d+,\s*\d+,\s*[\d.]+\)/));
            expect(mockGradient.addColorStop).toHaveBeenCalledWith(1, expect.stringMatching(/rgba\(\d+,\s*\d+,\s*\d+,\s*[\d.]+\)/));
        });
    });
});
