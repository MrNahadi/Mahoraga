import React from 'react';
import { ConfigurationPanel } from '@/components/ConfigurationPanel';

export function Configuration() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-heading font-bold text-text-primary">Configuration</h1>
                <p className="text-gray-600 mt-2">
                    Manage system settings and user mappings for autonomous bug triage
                </p>
            </div>

            <ConfigurationPanel />
        </div>
    );
}