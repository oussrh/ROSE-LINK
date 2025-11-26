/**
 * ROSE Link - ESLint Flat Configuration
 * ESLint v9+ compatible configuration
 *
 * @see https://eslint.org/docs/latest/use/configure/configuration-files-new
 */

import js from '@eslint/js';
import tseslint from '@typescript-eslint/eslint-plugin';
import tsparser from '@typescript-eslint/parser';
import globals from 'globals';

export default [
    // Base JavaScript recommended rules
    js.configs.recommended,

    // Global ignores
    {
        ignores: [
            'node_modules/**',
            'coverage/**',
            'vendor/**',
            '*.min.js',
            'sw.js', // Service worker has different requirements
        ],
    },

    // JavaScript files configuration
    {
        files: ['js/**/*.js'],
        languageOptions: {
            ecmaVersion: 'latest',
            sourceType: 'module',
            globals: {
                ...globals.browser,
                ...globals.es2021,
                htmx: 'readonly',
                lucide: 'readonly',
                tailwind: 'readonly',
            },
        },
        rules: {
            // Error prevention
            'no-unused-vars': ['warn', {
                argsIgnorePattern: '^_',
                varsIgnorePattern: '^_',
            }],
            'no-undef': 'error',
            'no-console': ['warn', { allow: ['warn', 'error'] }],

            // Code style
            'semi': ['error', 'always'],
            'quotes': ['error', 'single', { avoidEscape: true }],
            'indent': ['error', 4, { SwitchCase: 1 }],
            'comma-dangle': ['error', 'only-multiline'],
            'no-trailing-spaces': 'error',
            'eol-last': ['error', 'always'],

            // Best practices
            'eqeqeq': ['error', 'always', { null: 'ignore' }],
            'no-var': 'error',
            'prefer-const': 'warn',
            'prefer-arrow-callback': 'warn',
            'no-throw-literal': 'error',

            // Import/Export
            'no-duplicate-imports': 'error',

            // Security
            'no-eval': 'error',
            'no-implied-eval': 'error',
            'no-new-func': 'error',
        },
    },

    // TypeScript declaration files - minimal linting
    {
        files: ['js/types/**/*.d.ts'],
        languageOptions: {
            parser: tsparser,
            parserOptions: {
                ecmaVersion: 'latest',
                sourceType: 'module',
            },
            globals: {
                ...globals.browser,
                ...globals.es2021,
                htmx: 'readonly',
                lucide: 'readonly',
            },
        },
        plugins: {
            '@typescript-eslint': tseslint,
        },
        rules: {
            // Minimal rules for .d.ts files (no type-aware rules)
            '@typescript-eslint/no-unused-vars': 'off',
            'no-unused-vars': 'off',
        },
    },

    // TypeScript files configuration
    {
        files: ['js/**/*.ts'],
        ignores: ['js/types/**/*.d.ts'],
        languageOptions: {
            parser: tsparser,
            parserOptions: {
                ecmaVersion: 'latest',
                sourceType: 'module',
            },
            globals: {
                ...globals.browser,
                ...globals.es2021,
                htmx: 'readonly',
                lucide: 'readonly',
            },
        },
        plugins: {
            '@typescript-eslint': tseslint,
        },
        rules: {
            // TypeScript specific rules (no type-aware rules without project config)
            '@typescript-eslint/no-unused-vars': ['warn', {
                argsIgnorePattern: '^_',
                varsIgnorePattern: '^_',
            }],
            '@typescript-eslint/explicit-function-return-type': 'off',
            '@typescript-eslint/no-explicit-any': 'warn',

            // Disable base rules that conflict with TypeScript
            'no-unused-vars': 'off',
        },
    },

    // Test files configuration
    {
        files: ['__tests__/**/*.js', '**/*.test.js', '**/*.spec.js'],
        languageOptions: {
            globals: {
                ...globals.browser,
                ...globals.jest,
                ...globals.node,
            },
        },
        rules: {
            'no-console': 'off',
        },
    },
];
