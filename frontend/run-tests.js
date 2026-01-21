#!/usr/bin/env node

// Simple test runner to bypass UNC path issues
const { spawn } = require('child_process');
const path = require('path');

// Change to the frontend directory
process.chdir(__dirname);

// Run vitest with proper configuration
const vitest = spawn('npx', ['vitest', '--run'], {
    stdio: 'inherit',
    shell: true,
    env: {
        ...process.env,
        NODE_ENV: 'test'
    }
});

vitest.on('close', (code) => {
    process.exit(code);
});

vitest.on('error', (err) => {
    console.error('Failed to start vitest:', err);
    process.exit(1);
});