import React from 'react';
import { useTeamStats } from '@/hooks/useApi';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { AlertTriangle, TrendingUp, Users } from 'lucide-react';

const COLORS = ['#1A73E8', '#FBE0DD', '#34D399', '#F59E0B', '#EF4444'];

export function TeamHealth() {
    const { data: teamStats, isLoading, error } = useTeamStats();

    if (isLoading) {
        return (
            <div className="space-y-6">
                <h1 className="text-3xl font-heading font-bold text-text-primary">Team Health</h1>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {[...Array(4)].map((_, i) => (
                        <Card key={i} className="animate-pulse">
                            <CardHeader>
                                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                            </CardHeader>
                            <CardContent>
                                <div className="h-64 bg-gray-200 rounded"></div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="space-y-6">
                <h1 className="text-3xl font-heading font-bold text-text-primary">Team Health</h1>
                <Card className="border-red-200 bg-red-50">
                    <CardContent className="pt-6">
                        <p className="text-red-600">Failed to load team health data. Please check if the backend is running.</p>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Prepare data for charts
    const workloadData = teamStats?.developers.map(dev => ({
        name: dev.developer.display_name.split(' ')[0], // First name only for chart
        bugs: dev.active_bugs,
        isOverloaded: dev.is_overloaded,
    })) || [];

    const confidenceData = teamStats?.recent_decisions.reduce((acc, decision) => {
        const range = decision.confidence >= 80 ? 'High (80-100%)' :
            decision.confidence >= 60 ? 'Medium (60-79%)' : 'Low (0-59%)';
        acc[range] = (acc[range] || 0) + 1;
        return acc;
    }, {} as Record<string, number>) || {};

    const confidencePieData = Object.entries(confidenceData).map(([range, count]) => ({
        name: range,
        value: count,
    }));

    const overloadedCount = teamStats?.developers.filter(dev => dev.is_overloaded).length || 0;
    const totalDevelopers = teamStats?.developers.length || 0;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-heading font-bold text-text-primary">Team Health</h1>
                <p className="text-gray-600 mt-2">
                    Monitor workload distribution and team capacity
                </p>
            </div>

            {/* Health Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-gray-600">
                            Active Developers
                        </CardTitle>
                        <Users className="h-4 w-4 text-gray-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-text-primary">{totalDevelopers}</div>
                        <p className="text-xs text-gray-500 mt-1">
                            Team members with assignments
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-gray-600">
                            Overloaded Developers
                        </CardTitle>
                        <AlertTriangle className="h-4 w-4 text-red-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-red-600">{overloadedCount}</div>
                        <p className="text-xs text-gray-500 mt-1">
                            Developers with &gt;5 active bugs
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-gray-600">
                            Average Confidence
                        </CardTitle>
                        <TrendingUp className="h-4 w-4 text-green-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-green-600">
                            {Math.round(teamStats?.avg_confidence || 0)}%
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                            Assignment confidence score
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                    <CardHeader>
                        <CardTitle>Bug Distribution by Developer</CardTitle>
                        <CardDescription>
                            Current active bug assignments per team member
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={workloadData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="name" />
                                <YAxis />
                                <Tooltip
                                    formatter={(value, name) => [value, 'Active Bugs']}
                                    labelFormatter={(label) => `Developer: ${label}`}
                                />
                                <Bar
                                    dataKey="bugs"
                                    fill="#1A73E8"
                                    radius={[4, 4, 0, 0]}
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Assignment Confidence Distribution</CardTitle>
                        <CardDescription>
                            Confidence levels of recent triage decisions
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                            <PieChart>
                                <Pie
                                    data={confidencePieData}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                    outerRadius={80}
                                    fill="#8884d8"
                                    dataKey="value"
                                >
                                    {confidencePieData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>
            </div>

            {/* Detailed Team List */}
            <Card>
                <CardHeader>
                    <CardTitle>Team Member Details</CardTitle>
                    <CardDescription>
                        Detailed view of each developer's current workload
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {teamStats?.developers.map((dev) => (
                            <div
                                key={dev.developer.id}
                                className={`flex items-center justify-between p-4 rounded-base border ${dev.is_overloaded ? 'border-red-200 bg-red-50' : 'border-gray-200'
                                    }`}
                            >
                                <div className="flex items-center space-x-4">
                                    <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center">
                                        <span className="text-white font-medium">
                                            {dev.developer.display_name.charAt(0).toUpperCase()}
                                        </span>
                                    </div>
                                    <div>
                                        <h3 className="font-medium text-text-primary">
                                            {dev.developer.display_name}
                                        </h3>
                                        <p className="text-sm text-gray-500">
                                            {dev.developer.git_email}
                                        </p>
                                        <p className="text-xs text-gray-400">
                                            Slack: {dev.developer.slack_id}
                                        </p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className={`text-lg font-bold ${dev.is_overloaded ? 'text-red-600' : 'text-text-primary'
                                        }`}>
                                        {dev.active_bugs} bugs
                                    </div>
                                    {dev.is_overloaded && (
                                        <span className="inline-flex items-center px-2 py-1 text-xs bg-red-100 text-red-600 rounded-full mt-1">
                                            <AlertTriangle className="w-3 h-3 mr-1" />
                                            Overloaded
                                        </span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}