import React from 'react';
import { useAssignmentHistory } from '@/hooks/useApi';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { History, ExternalLink, Clock } from 'lucide-react';

export function AssignmentHistory() {
    const { data: assignments, isLoading, error } = useAssignmentHistory();

    if (isLoading) {
        return (
            <div className="space-y-6">
                <h1 className="text-3xl font-heading font-bold text-text-primary">Assignment History</h1>
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
                <h1 className="text-3xl font-heading font-bold text-text-primary">Assignment History</h1>
                <Card className="border-red-200 bg-red-50">
                    <CardContent className="pt-6">
                        <p className="text-red-600">Failed to load assignment history. Please check if the backend is running.</p>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-heading font-bold text-text-primary">Assignment History</h1>
                <p className="text-gray-600 mt-2">
                    Track all bug assignments and their outcomes
                </p>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                        <History className="w-5 h-5" />
                        <span>Recent Assignments</span>
                    </CardTitle>
                    <CardDescription>
                        Complete history of autonomous bug triage decisions
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {assignments && assignments.length > 0 ? (
                        <div className="space-y-4">
                            {assignments.map((assignment) => (
                                <div key={assignment.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-base">
                                    <div className="flex-1">
                                        <div className="flex items-center space-x-2">
                                            <h3 className="font-medium text-text-primary">
                                                Issue #{assignment.issue_id}
                                            </h3>
                                            <a
                                                href={assignment.issue_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-primary hover:text-primary/80"
                                            >
                                                <ExternalLink className="w-4 h-4" />
                                            </a>
                                        </div>
                                        <p className="text-sm text-gray-600 mt-1">
                                            Assigned to: {assignment.assigned_to_email}
                                        </p>
                                        <p className="text-xs text-gray-500 mt-1">
                                            {assignment.reasoning}
                                        </p>
                                    </div>
                                    <div className="text-right">
                                        <div className={`px-2 py-1 text-xs rounded-full ${assignment.confidence >= 80
                                                ? 'bg-green-100 text-green-600'
                                                : assignment.confidence >= 60
                                                    ? 'bg-yellow-100 text-yellow-600'
                                                    : 'bg-red-100 text-red-600'
                                            }`}>
                                            {Math.round(assignment.confidence)}% confidence
                                        </div>
                                        <div className="flex items-center space-x-1 text-xs text-gray-500 mt-2">
                                            <Clock className="w-3 h-3" />
                                            <span>{new Date(assignment.created_at).toLocaleDateString()}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8">
                            <History className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                            <p className="text-gray-500">No assignment history available</p>
                            <p className="text-sm text-gray-400 mt-1">
                                Assignments will appear here once the triage engine processes bugs
                            </p>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}