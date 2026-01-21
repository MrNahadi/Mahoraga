import React, { useState } from 'react';
import { useSettings, useUpdateSettings } from '@/hooks/useApi';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Settings as SettingsIcon, Save, AlertCircle, CheckCircle } from 'lucide-react';

export function Settings() {
    const { data: settings, isLoading, error } = useSettings();
    const updateSettingsMutation = useUpdateSettings();

    const [formData, setFormData] = useState({
        confidence_threshold: 60,
        draft_pr_enabled: true,
        duplicate_detection_window: 10,
        notification_enabled: true,
    });

    // Update form data when settings are loaded
    React.useEffect(() => {
        if (settings) {
            setFormData(settings);
        }
    }, [settings]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await updateSettingsMutation.mutateAsync(formData);
        } catch (error) {
            console.error('Failed to update settings:', error);
        }
    };

    const handleInputChange = (field: string, value: number | boolean) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    if (isLoading) {
        return (
            <div className="space-y-6">
                <h1 className="text-3xl font-heading font-bold text-text-primary">Settings</h1>
                <Card className="animate-pulse">
                    <CardHeader>
                        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {[...Array(4)].map((_, i) => (
                                <div key={i} className="h-16 bg-gray-200 rounded"></div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    if (error) {
        return (
            <div className="space-y-6">
                <h1 className="text-3xl font-heading font-bold text-text-primary">Settings</h1>
                <Card className="border-red-200 bg-red-50">
                    <CardContent className="pt-6">
                        <p className="text-red-600">Failed to load settings. Please check if the backend is running.</p>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-heading font-bold text-text-primary">Settings</h1>
                <p className="text-gray-600 mt-2">
                    Configure system behavior and thresholds
                </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center space-x-2">
                            <SettingsIcon className="w-5 h-5" />
                            <span>Triage Configuration</span>
                        </CardTitle>
                        <CardDescription>
                            Adjust how the autonomous triage system makes decisions
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        {/* Confidence Threshold */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-text-primary">
                                Confidence Threshold
                            </label>
                            <div className="flex items-center space-x-4">
                                <input
                                    type="range"
                                    min="0"
                                    max="100"
                                    value={formData.confidence_threshold}
                                    onChange={(e) => handleInputChange('confidence_threshold', parseInt(e.target.value))}
                                    className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                                />
                                <span className="text-sm font-medium text-text-primary w-12">
                                    {formData.confidence_threshold}%
                                </span>
                            </div>
                            <p className="text-xs text-gray-500">
                                Minimum confidence required for automatic assignment. Lower confidence assignments go to human triage.
                            </p>
                        </div>

                        {/* Duplicate Detection Window */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-text-primary">
                                Duplicate Detection Window (minutes)
                            </label>
                            <div className="flex items-center space-x-4">
                                <input
                                    type="range"
                                    min="1"
                                    max="60"
                                    value={formData.duplicate_detection_window}
                                    onChange={(e) => handleInputChange('duplicate_detection_window', parseInt(e.target.value))}
                                    className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                                />
                                <span className="text-sm font-medium text-text-primary w-12">
                                    {formData.duplicate_detection_window}m
                                </span>
                            </div>
                            <p className="text-xs text-gray-500">
                                Time window for detecting duplicate issues. Issues within this window are consolidated.
                            </p>
                        </div>

                        {/* Toggle Settings */}
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-sm font-medium text-text-primary">Draft PR Generation</h3>
                                    <p className="text-xs text-gray-500">
                                        Generate draft pull requests for high-confidence bugs (&gt;85% confidence)
                                    </p>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => handleInputChange('draft_pr_enabled', !formData.draft_pr_enabled)}
                                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${formData.draft_pr_enabled ? 'bg-primary' : 'bg-gray-200'
                                        }`}
                                >
                                    <span
                                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${formData.draft_pr_enabled ? 'translate-x-6' : 'translate-x-1'
                                            }`}
                                    />
                                </button>
                            </div>

                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-sm font-medium text-text-primary">Slack Notifications</h3>
                                    <p className="text-xs text-gray-500">
                                        Send Slack DMs to developers when bugs are assigned
                                    </p>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => handleInputChange('notification_enabled', !formData.notification_enabled)}
                                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${formData.notification_enabled ? 'bg-primary' : 'bg-gray-200'
                                        }`}
                                >
                                    <span
                                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${formData.notification_enabled ? 'translate-x-6' : 'translate-x-1'
                                            }`}
                                    />
                                </button>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Save Button */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        {updateSettingsMutation.isSuccess && (
                            <div className="flex items-center space-x-1 text-green-600">
                                <CheckCircle className="w-4 h-4" />
                                <span className="text-sm">Settings saved successfully</span>
                            </div>
                        )}
                        {updateSettingsMutation.isError && (
                            <div className="flex items-center space-x-1 text-red-600">
                                <AlertCircle className="w-4 h-4" />
                                <span className="text-sm">Failed to save settings</span>
                            </div>
                        )}
                    </div>

                    <Button
                        type="submit"
                        disabled={updateSettingsMutation.isPending}
                        className="flex items-center space-x-2"
                    >
                        <Save className="w-4 h-4" />
                        <span>{updateSettingsMutation.isPending ? 'Saving...' : 'Save Settings'}</span>
                    </Button>
                </div>
            </form>

            {/* Current Settings Display */}
            <Card>
                <CardHeader>
                    <CardTitle>Current Configuration</CardTitle>
                    <CardDescription>
                        Active system settings and their effects
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-4 bg-gray-50 rounded-base">
                            <h4 className="font-medium text-text-primary">Auto-Assignment</h4>
                            <p className="text-sm text-gray-600 mt-1">
                                Bugs with ≥{formData.confidence_threshold}% confidence are automatically assigned
                            </p>
                        </div>

                        <div className="p-4 bg-gray-50 rounded-base">
                            <h4 className="font-medium text-text-primary">Draft PRs</h4>
                            <p className="text-sm text-gray-600 mt-1">
                                {formData.draft_pr_enabled
                                    ? 'Generated for bugs with >85% confidence'
                                    : 'Disabled - no draft PRs will be created'
                                }
                            </p>
                        </div>

                        <div className="p-4 bg-gray-50 rounded-base">
                            <h4 className="font-medium text-text-primary">Duplicate Detection</h4>
                            <p className="text-sm text-gray-600 mt-1">
                                Issues within {formData.duplicate_detection_window} minutes are consolidated
                            </p>
                        </div>

                        <div className="p-4 bg-gray-50 rounded-base">
                            <h4 className="font-medium text-text-primary">Notifications</h4>
                            <p className="text-sm text-gray-600 mt-1">
                                {formData.notification_enabled
                                    ? 'Slack DMs sent for all assignments'
                                    : 'Notifications disabled'
                                }
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}