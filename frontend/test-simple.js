// Simple test to verify setup
console.log('Testing basic setup...');

// Test 1: Check if we can import React
try {
    const React = require('react');
    console.log('✓ React import successful');
} catch (e) {
    console.log('✗ React import failed:', e.message);
}

// Test 2: Check if we can import testing library
try {
    const { render } = require('@testing-library/react');
    console.log('✓ Testing Library import successful');
} catch (e) {
    console.log('✗ Testing Library import failed:', e.message);
}

// Test 3: Check if we can import Vitest
try {
    const { describe, it, expect } = require('vitest');
    console.log('✓ Vitest import successful');
} catch (e) {
    console.log('✗ Vitest import failed:', e.message);
}

console.log('Basic setup verification complete');