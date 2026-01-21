import React, { useState, useMemo } from 'react';
import { useSettings, useUpdateSettings, useUsers, useCreateUser, useUpdateUser, useDeleteUser } from '@/hooks/useApi';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
    Settings as SettingsIcon,
    Save,
    AlertCircle,
    CheckCircle,
    Users,
    Plus,
    Edit,
    Trash2,
    Mail,
    MessageSquare,
    Search,
    Filter,
    Download,
    Upload,
    RefreshCw
} from 'lucide-react';
import type { Developer } from '@/lib/api';

interface ConfigurationPanelProps {
    className?: string;
}

export function ConfigurationPanel({ className }: ConfigurationPanelProps) {
    const { data: settings, isLoading: settingsLoading, error: settingsError } = useSettings();
    const { data: users, isLoading: usersLoading, error: usersError } = useUsers();
    const updateSettingsMutation = useUpdateSettings();
    const createUserMutation = useCreateUser();
    const updateUserMutation = useUpdateUser();
    const deleteUserMutation = useDeleteUser();

    // Settings form state
    const [settingsForm, setSettingsForm] = useState({
        confidence_threshold: 60,
        draft_pr_enabled: true,
        duplicate_detection_window: 10,
        notification_enabled: true,
    });

    // User management state
    const [showAddUserForm, setShowAddUserForm] = useState(false);
    const [editingUser, setEditingUser] = useState<Developer | null>(null);
    const [userForm, setUserForm] = useState({
        git_email: '',
        slack_id: '',
        display_name: '',
        is_active: true,
    });

    // Search and filter state
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');

    // Update form data when settings are loaded
    React.useEffect(() => {
        if (settings) {
            setSettingsForm(settings);
        }
    }, [settings]);

    // Filtered and searched users
    const filteredUsers = useMemo(() => {
        if (!users) return [];

        return users.filter(user => {
            const matchesSearch = searchTerm === '' ||
                user.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                user.git_email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                user.slack_id.toLowerCase().includes(searchTerm.toLowerCase());

            const matchesStatus = statusFilter === 'all' ||
                (statusFilter === 'active' && user.is_active) ||
                (statusFilter === 'inactive' && !user.is_active);

            return matchesSearch && matchesStatus;
        });
    }, [users, searchTerm, statusFilter]);

    // Settings handlers
    const handleSettingsSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await updateSettingsMutation.mutateAsync(settingsForm);
        } catch (error) {
            console.error('Failed to update settings:', error);
        }
    };

    const handleSettingsChange = (field: string, value: number | boolean) => {
        setSettingsForm(prev => ({ ...prev, [field]: value }));
    };

    // User management handlers
    const resetUserForm = () => {
        setUserForm({
            git_email: '',
            slack_id: '',
            display_name: '',
            is_active: true,
        });
        setShowAddUserForm(false);
        setEditingUser(null);
    };

    const handleUserSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            if (editingUser) {
                await updateUserMutation.mutateAsync({ id: editingUser.id, user: userForm });
            } else {
                await createUserMutation.mutateAsync(userForm);
            }
            resetUserForm();
        } catch (error) {
            console.error('Failed to save user:', error);
        }
    };

    const handleEditUser = (user: Developer) => {
        setEditingUser(user);
        setUserForm({
            git_email: user.git_email,
            slack_id: user.slack_id,
            display_name: user.display_name,
            is_active: user.is_active,
        });
        setShowAddUserForm(true);
    };

    const handleDeleteUser = async (userId: number) => {
        if (window.confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
            try {
                await deleteUserMutation.mutateAsync(userId);
            } catch (error) {
                console.error('Failed to delete user:', error);
            }
        }
    };

    // Bulk operations
    const handleExportUsers = () => {
        if (!users) return;

        const csvContent = [
            'Display Name,Git Email,Slack ID,Active',
            ...users.map(user =>
                `"${user.display_name}","${user.git_email}","${user.slack_id}",${user.is_active}`
            )
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'mahoraga-users.csv';
        a.click();
        window.URL.revokeObjectURL(url);
    };

    const isLoading = settingsLoading || usersLoading;
    const hasError = settingsError || usersError;

    if (isLoading) {
        return (
            <div className={`space-y-6 ${className}`}>
                <div className="flex items-center space-x-2">
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    <span>Loading configuration...</span>
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {[...Array(4)].map((_, i) => (
                        <Card key={i} className="animate-pulse">
                            <CardHeader>
                                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    <div className="h-16 bg-gray-200 rounded"></div>
                                    <div className="h-16 bg-gray-200 rounded"></div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        );
    }

    if (hasError) {
        return (
            <div className={`space-y-6 ${className}`}>
                <Card className="border-red-200 bg-red-50">
                    <CardContent className="pt-6">
                        <div className="flex items-center space-x-2 text-red-600">
                            <AlertCircle className="w-5 h-5" />
                            <span>Failed to load configuration. Please check if the backend is running.</span>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className={`space-y-6 ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-heading font-bold text-text-primary">Configuration Panel</h2>
                    <p className="text-gray-600 mt-1">
                        Manage system settings and user mappings
                    </p>
                </div>
                <div className="flex items-center space-x-2">
                    {updateSettingsMutation.isSuccess && (
                        <div className="flex items-center space-x-1 text-green-600">
                            <CheckCircle className="w-4 h-4" />
                            <span className="text-sm">Configuration updated</span>
                        </div>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* System Settings */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center space-x-2">
                            <SettingsIcon className="w-5 h-5" />
                            <span>System Settings</span>
                        </CardTitle>
                        <CardDescription>
                            Configure autonomous triage behavior and thresholds
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleSettingsSubmit} className="space-y-6">
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
                                        value={settingsForm.confidence_threshold}
                                        onChange={(e) => handleSettingsChange('confidence_threshold', parseInt(e.target.value))}
                                        className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                                    />
                                    <span className="text-sm font-medium text-text-primary w-12">
                                        {settingsForm.confidence_threshold}%
                                    </span>
                                </div>
                                <p className="text-xs text-gray-500">
                                    Minimum confidence for auto-assignment. Lower confidence → human triage.
                                </p>
                            </div>

                            {/* Duplicate Detection Window */}
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-text-primary">
                                    Duplicate Detection Window
                                </label>
                                <div className="flex items-center space-x-4">
                                    <input
                                        type="range"
                                        min="1"
                                        max="60"
                                        value={settingsForm.duplicate_detection_window}
                                        onChange={(e) => handleSettingsChange('duplicate_detection_window', parseInt(e.target.value))}
                                        className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                                    />
                                    <span className="text-sm font-medium text-text-primary w-12">
                                        {settingsForm.duplicate_detection_window}m
                                    </span>
                                </div>
                                <p className="text-xs text-gray-500">
                                    Time window for consolidating duplicate issues.
                                </p>
                            </div>

                            {/* Toggle Settings */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="text-sm font-medium text-text-primary">Draft PR Mode</h3>
                                        <p className="text-xs text-gray-500">
                                            Generate draft PRs for high-confidence bugs (&gt;85%)
                                        </p>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => handleSettingsChange('draft_pr_enabled', !settingsForm.draft_pr_enabled)}
                                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${settingsForm.draft_pr_enabled ? 'bg-primary' : 'bg-gray-200'
                                            }`}
                                    >
                                        <span
                                            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${settingsForm.draft_pr_enabled ? 'translate-x-6' : 'translate-x-1'
                                                }`}
                                        />
                                    </button>
                                </div>

                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="text-sm font-medium text-text-primary">Notifications</h3>
                                        <p className="text-xs text-gray-500">
                                            Send Slack DMs for bug assignments
                                        </p>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => handleSettingsChange('notification_enabled', !settingsForm.notification_enabled)}
                                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${settingsForm.notification_enabled ? 'bg-primary' : 'bg-gray-200'
                                            }`}
                                    >
                                        <span
                                            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${settingsForm.notification_enabled ? 'translate-x-6' : 'translate-x-1'
                                                }`}
                                        />
                                    </button>
                                </div>
                            </div>

                            <Button
                                type="submit"
                                disabled={updateSettingsMutation.isPending}
                                className="w-full flex items-center justify-center space-x-2"
                            >
                                <Save className="w-4 h-4" />
                                <span>{updateSettingsMutation.isPending ? 'Applying...' : 'Apply Settings'}</span>
                            </Button>
                        </form>
                    </CardContent>
                </Card>

                {/* Current Configuration Status */}
                <Card>
                    <CardHeader>
                        <CardTitle>Configuration Status</CardTitle>
                        <CardDescription>
                            Current system behavior and effects
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="p-4 bg-gray-50 rounded-base">
                                <h4 className="font-medium text-text-primary">Auto-Assignment</h4>
                                <p className="text-sm text-gray-600 mt-1">
                                    Bugs with ≥{settingsForm.confidence_threshold}% confidence → automatic assignment
                                </p>
                                <p className="text-sm text-gray-600">
                                    Bugs with &lt;{settingsForm.confidence_threshold}% confidence → human triage
                                </p>
                            </div>

                            <div className="p-4 bg-gray-50 rounded-base">
                                <h4 className="font-medium text-text-primary">Draft PR Generation</h4>
                                <p className="text-sm text-gray-600 mt-1">
                                    {settingsForm.draft_pr_enabled
                                        ? 'Enabled for bugs with >85% confidence'
                                        : 'Disabled - no draft PRs generated'
                                    }
                                </p>
                            </div>

                            <div className="p-4 bg-gray-50 rounded-base">
                                <h4 className="font-medium text-text-primary">Duplicate Detection</h4>
                                <p className="text-sm text-gray-600 mt-1">
                                    Issues within {settingsForm.duplicate_detection_window} minutes are consolidated
                                </p>
                            </div>

                            <div className="p-4 bg-gray-50 rounded-base">
                                <h4 className="font-medium text-text-primary">Notifications</h4>
                                <p className="text-sm text-gray-600 mt-1">
                                    {settingsForm.notification_enabled
                                        ? 'Slack DMs sent for all assignments'
                                        : 'Notifications disabled'
                                    }
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* User Management Section */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                            <Users className="w-5 h-5" />
                            <span>User Mapping Management</span>
                        </div>
                        <div className="flex items-center space-x-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleExportUsers}
                                className="flex items-center space-x-1"
                            >
                                <Download className="w-3 h-3" />
                                <span>Export</span>
                            </Button>
                            <Button
                                size="sm"
                                onClick={() => setShowAddUserForm(true)}
                                className="flex items-center space-x-1"
                            >
                                <Plus className="w-3 h-3" />
                                <span>Add User</span>
                            </Button>
                        </div>
                    </CardTitle>
                    <CardDescription>
                        Manage Git email ↔ Slack ID mappings for automatic notifications
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {/* Search and Filter Controls */}
                    <div className="flex items-center space-x-4 mb-6">
                        <div className="flex-1 relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                            <input
                                type="text"
                                placeholder="Search users by name, email, or Slack ID..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-base focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                            />
                        </div>
                        <div className="flex items-center space-x-2">
                            <Filter className="w-4 h-4 text-gray-400" />
                            <select
                                value={statusFilter}
                                onChange={(e) => setStatusFilter(e.target.value as 'all' | 'active' | 'inactive')}
                                className="px-3 py-2 border border-gray-300 rounded-base focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                            >
                                <option value="all">All Users</option>
                                <option value="active">Active Only</option>
                                <option value="inactive">Inactive Only</option>
                            </select>
                        </div>
                    </div>

                    {/* Add/Edit User Form */}
                    {showAddUserForm && (
                        <div className="mb-6 p-4 border border-gray-200 rounded-base bg-gray-50">
                            <h3 className="font-medium text-text-primary mb-4">
                                {editingUser ? 'Edit User' : 'Add New User'}
                            </h3>
                            <form onSubmit={handleUserSubmit} className="space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-text-primary mb-1">
                                            Display Name *
                                        </label>
                                        <input
                                            type="text"
                                            value={userForm.display_name}
                                            onChange={(e) => setUserForm(prev => ({ ...prev, display_name: e.target.value }))}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-base focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                                            placeholder="John Doe"
                                            required
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-text-primary mb-1">
                                            Git Email *
                                        </label>
                                        <input
                                            type="email"
                                            value={userForm.git_email}
                                            onChange={(e) => setUserForm(prev => ({ ...prev, git_email: e.target.value }))}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-base focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                                            placeholder="john.doe@company.com"
                                            required
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-text-primary mb-1">
                                            Slack User ID *
                                        </label>
                                        <input
                                            type="text"
                                            value={userForm.slack_id}
                                            onChange={(e) => setUserForm(prev => ({ ...prev, slack_id: e.target.value }))}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-base focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                                            placeholder="U1234567890"
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="flex items-center space-x-2">
                                    <input
                                        type="checkbox"
                                        id="user_is_active"
                                        checked={userForm.is_active}
                                        onChange={(e) => setUserForm(prev => ({ ...prev, is_active: e.target.checked }))}
                                        className="rounded border-gray-300 text-primary focus:ring-primary"
                                    />
                                    <label htmlFor="user_is_active" className="text-sm font-medium text-text-primary">
                                        Active (receives bug assignments)
                                    </label>
                                </div>

                                <div className="flex items-center space-x-2">
                                    <Button
                                        type="submit"
                                        size="sm"
                                        disabled={createUserMutation.isPending || updateUserMutation.isPending}
                                    >
                                        {editingUser ? 'Update User' : 'Add User'}
                                    </Button>
                                    <Button type="button" variant="outline" size="sm" onClick={resetUserForm}>
                                        Cancel
                                    </Button>
                                </div>
                            </form>
                        </div>
                    )}

                    {/* Users Table */}
                    {filteredUsers && filteredUsers.length > 0 ? (
                        <div className="space-y-2">
                            <div className="text-sm text-gray-500 mb-4">
                                Showing {filteredUsers.length} of {users?.length || 0} users
                            </div>
                            <div className="space-y-2">
                                {filteredUsers.map((user) => (
                                    <div key={user.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-base hover:bg-gray-50 transition-colors">
                                        <div className="flex items-center space-x-4">
                                            <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center">
                                                <span className="text-white font-medium text-sm">
                                                    {user.display_name.charAt(0).toUpperCase()}
                                                </span>
                                            </div>
                                            <div>
                                                <h3 className="font-medium text-text-primary">
                                                    {user.display_name}
                                                    {!user.is_active && (
                                                        <span className="ml-2 px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full">
                                                            Inactive
                                                        </span>
                                                    )}
                                                </h3>
                                                <div className="flex items-center space-x-4 mt-1">
                                                    <div className="flex items-center space-x-1 text-sm text-gray-500">
                                                        <Mail className="w-3 h-3" />
                                                        <span>{user.git_email}</span>
                                                    </div>
                                                    <div className="flex items-center space-x-1 text-sm text-gray-500">
                                                        <MessageSquare className="w-3 h-3" />
                                                        <span>{user.slack_id}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handleEditUser(user)}
                                                className="flex items-center space-x-1"
                                            >
                                                <Edit className="w-3 h-3" />
                                                <span>Edit</span>
                                            </Button>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handleDeleteUser(user.id)}
                                                className="flex items-center space-x-1 text-red-600 hover:text-red-700 hover:border-red-300"
                                            >
                                                <Trash2 className="w-3 h-3" />
                                                <span>Delete</span>
                                            </Button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="text-center py-8">
                            <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                            <p className="text-gray-500">
                                {searchTerm || statusFilter !== 'all' ? 'No users match your search criteria' : 'No users configured'}
                            </p>
                            <p className="text-sm text-gray-400 mt-1">
                                {searchTerm || statusFilter !== 'all'
                                    ? 'Try adjusting your search or filter settings'
                                    : 'Add team members to enable automatic bug assignment'
                                }
                            </p>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}