/**
 * Babel configuration for Jest testing
 */
module.exports = {
    presets: [
        ['@babel/preset-env', { targets: { node: 'current' } }],
    ],
};
