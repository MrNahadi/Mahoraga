import React, { useState } from 'react';
import { useUsers, useCreateUser, useUpdateUser, useDeleteUser } from '@/hooks/useApi';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Users, Plus, Edit, Trash2, Mail, MessageSquare } from 'lucide-react';
import type { Developer } from '@/lib/api';

export function UserManagement() {
    const { data: users, isLoading, error } = useUsers();
    const createUserMutation = useCreateUser();
    const updateUserMutation = useUpdateUser();
    const deleteUserMutation = useDeleteUser();

    const [showAddForm, setShowAddForm] = useState(false);
    const [editingUser, setEditingUser] = useState<Developer | null>(null);
    const [formData, setFormData] = useState({
        git_email: '',
        slack_id: '',
        display_name: '',
        is_active: true,
    });

    const resetForm = () => {
        setFormData({
            git_email: '',
            slack_id: '',
            display_name: '',
            is_active: true,
        });
        setShowAddForm(false);
        setEditingUser(null);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            if (editingUser) {
                await updateUserMutation.mutateAsync({ id: editingUser.id, user: formData });
            } else {
                await createUserMutation.mutateAsync(formData);
            }
            resetForm();
        } catch (error) {
            console.error('Failed to save user:', error);
        }
    };

    const handleEdit = (user: Developer) => {
        setEditingUser(user);
        setFormData({
            git_email: user.git_email,
            slack_id: user.slack_id,
            display_name: user.display_name,
            is_active: user.is_active,
        });
        setShowAddForm(true);
    };

    const handleDelete = async (userId: number) => {
        if (window.confirm('Are you sure you want to delete this user?')) {
            try {
                await deleteUserMutation.mutateAsync(userId);
            } catch (error) {
                console.error('Failed to delete user:', error);
            }
        }
    };

    if (isLoading) {
        return (
            <div className="space-y-6">
                <h1 className="text-3xl font-heading font-bold text-text-primary">User Management</h1>
                <Card className="animate-pulse">
                    <CardContent className="pt-6">
                        <div className="space-y-4">
                            {[...Array(5)].map((_, i) => (
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
                <h1 className="text-3xl font-heading font-bold text-text-primary">User Management</h1>
                <Card className="border-red-200 bg-red-50">
                    <CardContent className="pt-6">
                        <p className="text-red-600">Failed to load users. Please check if the backend is running.</p>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-heading font-bold text-text-primary">User Management</h1>
                    <p className="text-gray-600 mt-2">
                        Manage developer profiles and Git ↔ Slack mappings
                    </p>
                </div>
                <Button
                    onClick={() => setShowAddForm(true)}
                    className="flex items-center space-x-2"
                >
                    <Plus className="w-4 h-4" />
                    <span>Add User</span>
                </Button>
            </div>

            {/* Add/Edit User Form */}
            {showAddForm && (
                <Card>
                    <CardHeader>
                        <CardTitle>
                            {editingUser ? 'Edit User' : 'Add New User'}
                        </CardTitle>
                        <CardDescription>
                            Map Git email addresses to Slack user IDs for notifications
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-text-primary mb-1">
                                        Display Name
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.display_name}
                                        onChange={(e) => setFormData(prev => ({ ...prev, display_name: e.target.value }))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-base focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                                        placeholder="John Doe"
                                        required
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-text-primary mb-1">
                                        Git Email
                                    </label>
                                    <input
                                        type="email"
                                        value={formData.git_email}
                                        onChange={(e) => setFormData(prev => ({ ...prev, git_email: e.target.value }))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-base focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                                        placeholder="john.doe@company.com"
                                        required
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-text-primary mb-1">
                                        Slack User ID
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.slack_id}
                                        onChange={(e) => setFormData(prev => ({ ...prev, slack_id: e.target.value }))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-base focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                                        placeholder="U1234567890"
                                        required
                                    />
                                </div>

                                <div className="flex items-center space-x-2">
                                    <input
                                        type="checkbox"
                                        id="is_active"
                                        checked={formData.is_active}
                                        onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                                        className="rounded border-gray-300 text-primary focus:ring-primary"
                                    />
                                    <label htmlFor="is_active" className="text-sm font-medium text-text-primary">
                                        Active (receives assignments)
                                    </label>
                                </div>
                            </div>

                            <div className="flex items-center space-x-2">
                                <Button type="submit" disabled={createUserMutation.isPending || updateUserMutation.isPending}>
                                    {editingUser ? 'Update User' : 'Add User'}
                                </Button>
                                <Button type="button" variant="outline" onClick={resetForm}>
                                    Cancel
                                </Button>
                            </div>
                        </form>
                    </CardContent>
                </Card>
            )}

            {/* Users List */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                        <Users className="w-5 h-5" />
                        <span>Team Members</span>
                    </CardTitle>
                    <CardDescription>
                        Current Git ↔ Slack mappings and user status
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {users && users.length > 0 ? (
                        <div className="space-y-4">
                            {users.map((user) => (
                                <div key={user.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-base">
                                    <div className="flex items-center space-x-4">
                                        <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center">
                                            <span className="text-white font-medium">
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
                                            onClick={() => handleEdit(user)}
                                            className="flex items-center space-x-1"
                                        >
                                            <Edit className="w-3 h-3" />
                                            <span>Edit</span>
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleDelete(user.id)}
                                            className="flex items-center space-x-1 text-red-600 hover:text-red-700"
                                        >
                                            <Trash2 className="w-3 h-3" />
                                            <span>Delete</span>
                                        </Button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8">
                            <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                            <p className="text-gray-500">No users configured</p>
                            <p className="text-sm text-gray-400 mt-1">
                                Add team members to enable automatic bug assignment
                            </p>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}