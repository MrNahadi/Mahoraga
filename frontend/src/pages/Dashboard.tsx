import React from 'react';
import { useTeamStats } from '@/hooks/useApi';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, Users, Target, Clock, AlertTriangle, TrendingUp, BarChart3 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export function Dashboard() {
    const { data: teamStats, isLoading, error } = useTeamStats();

    if (isLoading) {
        return (
            <div className="space-y-6">
                <h1 className="text-3xl font-heading font-bold text-text-primary">Team Dashboard</h1>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {[...Array(4)].map((_, i) => (
                        <Card key={i} className="animate-pulse">
                            <CardHeader className="pb-2">
                                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                            </CardHeader>
                            <CardContent>
                                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Card className="animate-pulse">
                        <CardHeader>
                            <div className="h-6 bg-gray-200 rounded w-1/2"></div>
                        </CardHeader>
                        <CardContent>
                            <div className="h-64 bg-gray-200 rounded"></div>
                        </CardContent>
                    </Card>
                    <Card className="animate-pulse">
                        <CardHeader>
                            <div className="h-6 bg-gray-200 rounded w-1/2"></div>
                        </CardHeader>
                        <CardContent>
                            <div className="h-64 bg-gray-200 rounded"></div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="space-y-6">
                <h1 className="text-3xl font-heading font-bold text-text-primary">Team Dashboard</h1>
                <Card className="border-red-200 bg-red-50">
                    <CardContent className="pt-6">
                        <div className="flex items-center space-x-2">
                            <AlertTriangle className="h-5 w-5 text-red-600" />
                            <p className="text-red-600">Failed to load dashboard data. Please check if the backend is running.</p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Prepare data for the bug count bar chart
    const bugCountData = teamStats?.developers.map(dev => ({
        name: dev.developer.display_name.split(' ')[0], // Use first name for chart
        fullName: dev.developer.display_name,
        bugs: dev.active_bugs,
        isOverloaded: dev.is_overloaded,
        email: dev.developer.git_email
    })) || [];

    // Sort by bug count for better visualization
    bugCountData.sort((a, b) => b.bugs - a.bugs);

    const stats = [
        {
            title: 'Active Developers',
            value: teamStats?.developers.length || 0,
            icon: Users,
            description: 'Team members with assignments',
            trend: '+2 this week'
        },
        {
            title: 'Total Assignments',
            value: teamStats?.total_assignments || 0,
            icon: Target,
            description: 'Bugs triaged and assigned',
            trend: '+12 today'
        },
        {
            title: 'Average Confidence',
            value: `${Math.round(teamStats?.avg_confidence || 0)}%`,
            icon: Activity,
            description: 'Assignment confidence score',
            trend: (teamStats?.avg_confidence ?? 0) >= 75 ? 'High confidence' : 'Needs attention'
        },
        {
            title: 'Recent Decisions',
            value: teamStats?.recent_decisions.length || 0,
            icon: Clock,
            description: 'Triage decisions today',
            trend: 'Last updated now'
        },
    ];

    // Count overloaded developers
    const overloadedCount = teamStats?.developers.filter(dev => dev.is_overloaded).length || 0;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-heading font-bold text-text-primary">Team Dashboard</h1>
                    <p className="text-gray-600 mt-2">
                        Real-time overview of your autonomous bug triage system
                    </p>
                </div>
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <Activity className="h-4 w-4" />
                    <span>Auto-refreshes every 30s</span>
                </div>
            </div>

            {/* Alert for overloaded developers */}
            {overloadedCount > 0 && (
                <Card className="border-orange-200 bg-orange-50">
                    <CardContent className="pt-6">
                        <div className="flex items-center space-x-2">
                            <AlertTriangle className="h-5 w-5 text-orange-600" />
                            <p className="text-orange-800">
                                <span className="font-semibold">{overloadedCount} developer{overloadedCount > 1 ? 's' : ''}</span> currently overloaded with more than 5 active bugs
                            </p>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {stats.map((stat) => (
                    <Card key={stat.title} className="hover:shadow-md transition-shadow">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium text-gray-600">
                                {stat.title}
                            </CardTitle>
                            <stat.icon className="h-4 w-4 text-gray-400" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-text-primary">{stat.value}</div>
                            <p className="text-xs text-gray-500 mt-1">
                                {stat.description}
                            </p>
                            <div className="flex items-center mt-2 text-xs">
                                <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
                                <span className="text-green-600">{stat.trend}</span>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Main Dashboard Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Bug Count Visualization - Takes 2 columns */}
                <Card className="lg:col-span-2">
                    <CardHeader>
                        <CardTitle className="flex items-center space-x-2">
                            <BarChart3 className="h-5 w-5" />
                            <span>Team Bug Load</span>
                        </CardTitle>
                        <CardDescription>
                            Current bug assignments per developer with overload warnings
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={bugCountData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                    <XAxis
                                        dataKey="name"
                                        tick={{ fontSize: 12 }}
                                        stroke="#666"
                                    />
                                    <YAxis
                                        tick={{ fontSize: 12 }}
                                        stroke="#666"
                                    />
                                    <Tooltip
                                        content={({ active, payload, label }) => {
                                            if (active && payload && payload.length) {
                                                const data = payload[0].payload;
                                                return (
                                                    <div className="bg-white p-3 border rounded-lg shadow-lg">
                                                        <p className="font-semibold">{data.fullName}</p>
                                                        <p className="text-sm text-gray-600">{data.email}</p>
                                                        <p className="text-sm">
                                                            <span className="font-medium">{data.bugs} active bugs</span>
                                                            {data.isOverloaded && (
                                                                <span className="ml-2 px-2 py-1 text-xs bg-red-100 text-red-600 rounded">
                                                                    Overloaded
                                                                </span>
                                                            )}
                                                        </p>
                                                    </div>
                                                );
                                            }
                                            return null;
                                        }}
                                    />
                                    <Bar dataKey="bugs" radius={[4, 4, 0, 0]}>
                                        {bugCountData.map((entry, index) => (
                                            <Cell
                                                key={`cell-${index}`}
                                                fill={entry.isOverloaded ? '#ef4444' : '#f97316'}
                                            />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Legend */}
                        <div className="flex items-center justify-center space-x-6 mt-4 text-sm">
                            <div className="flex items-center space-x-2">
                                <div className="w-3 h-3 bg-primary rounded"></div>
                                <span>Normal load (≤5 bugs)</span>
                            </div>
                            <div className="flex items-center space-x-2">
                                <div className="w-3 h-3 bg-red-500 rounded"></div>
                                <span>Overloaded (&gt;5 bugs)</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Recent Triage Decisions - Takes 1 column */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center space-x-2">
                            <Clock className="h-5 w-5" />
                            <span>Live Triage Feed</span>
                        </CardTitle>
                        <CardDescription>
                            Latest autonomous assignments with confidence scores
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4 max-h-64 overflow-y-auto">
                            {teamStats?.recent_decisions.slice(0, 8).map((decision) => (
                                <div key={decision.id} className="flex items-start justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-text-primary truncate">
                                            Issue #{decision.issue_id}
                                        </p>
                                        <p className="text-xs text-gray-500 mt-1">
                                            {new Date(decision.created_at).toLocaleString()}
                                        </p>
                                        {decision.root_cause && (
                                            <p className="text-xs text-gray-600 mt-1 truncate">
                                                {decision.root_cause}
                                            </p>
                                        )}
                                        <p className="text-xs text-gray-500 mt-1">
                                            Processed in {decision.processing_time_ms}ms
                                        </p>
                                    </div>
                                    <div className="flex flex-col items-end space-y-1 ml-2">
                                        <span className={`px-2 py-1 text-xs rounded-full font-medium ${decision.confidence >= 85
                                            ? 'bg-green-100 text-green-700'
                                            : decision.confidence >= 70
                                                ? 'bg-blue-100 text-blue-700'
                                                : decision.confidence >= 60
                                                    ? 'bg-yellow-100 text-yellow-700'
                                                    : 'bg-red-100 text-red-700'
                                            }`}>
                                            {Math.round(decision.confidence)}%
                                        </span>
                                        {decision.draft_pr_url && (
                                            <span className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded-full">
                                                Draft PR
                                            </span>
                                        )}
                                    </div>
                                </div>
                            ))}
                            {(!teamStats?.recent_decisions || teamStats.recent_decisions.length === 0) && (
                                <div className="text-center py-8 text-gray-500">
                                    <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
                                    <p className="text-sm">No recent triage decisions</p>
                                    <p className="text-xs">Decisions will appear here as bugs are processed</p>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Team Load Overview - Detailed List */}
            <Card>
                <CardHeader>
                    <CardTitle>Detailed Team Load</CardTitle>
                    <CardDescription>
                        Individual developer workloads and status
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {teamStats?.developers.map((dev) => (
                            <div
                                key={dev.developer.id}
                                className={`p-4 rounded-lg border-2 transition-all hover:shadow-md ${dev.is_overloaded
                                    ? 'border-red-200 bg-red-50'
                                    : 'border-gray-200 bg-white hover:border-primary/20'
                                    }`}
                            >
                                <div className="flex items-center space-x-3">
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-medium ${dev.is_overloaded ? 'bg-red-500' : 'bg-primary'
                                        }`}>
                                        {dev.developer.display_name.charAt(0).toUpperCase()}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-text-primary truncate">
                                            {dev.developer.display_name}
                                        </p>
                                        <p className="text-xs text-gray-500 truncate">
                                            {dev.developer.git_email}
                                        </p>
                                    </div>
                                </div>
                                <div className="mt-3 flex items-center justify-between">
                                    <span className={`text-lg font-bold ${dev.is_overloaded ? 'text-red-600' : 'text-gray-900'
                                        }`}>
                                        {dev.active_bugs} bugs
                                    </span>
                                    {dev.is_overloaded && (
                                        <div className="flex items-center space-x-1">
                                            <AlertTriangle className="h-4 w-4 text-red-500" />
                                            <span className="text-xs text-red-600 font-medium">
                                                Overloaded
                                            </span>
                                        </div>
                                    )}
                                </div>
                                <div className="mt-2">
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                        <div
                                            className={`h-2 rounded-full transition-all ${dev.is_overloaded ? 'bg-red-500' : 'bg-primary'
                                                }`}
                                            style={{
                                                width: `${Math.min((dev.active_bugs / 10) * 100, 100)}%`
                                            }}
                                        ></div>
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">
                                        Load: {dev.active_bugs}/10 capacity
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}