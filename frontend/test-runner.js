#!/usr/bin/env node

// Simple test runner to check if our React setup is working
const { execSync } = require('child_process');
const path = require('path');

console.log('🧪 Running React Setup Tests...\n');

try {
    // Change to frontend directory
    process.chdir(path.join(__dirname));

    console.log('📦 Checking dependencies...');
    execSync('npm list --depth=0', { stdio: 'inherit' });

    console.log('\n🔧 Running TypeScript compilation check...');
    execSync('npx tsc --noEmit', { stdio: 'inherit' });

    console.log('\n✅ TypeScript compilation successful!');

    console.log('\n🎯 Running unit tests...');
    execSync('npx vitest run --reporter=verbose', { stdio: 'inherit' });

    console.log('\n🎉 All tests passed! React setup is working correctly.');

} catch (error) {
    console.error('\n❌ Test execution failed:', error.message);
    process.exit(1);
}