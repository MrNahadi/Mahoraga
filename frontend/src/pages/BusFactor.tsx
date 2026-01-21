import React from 'react';
import { useBusFactorData } from '@/hooks/useApi';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, Users, FileText, TrendingUp, GitBranch, User, Target } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

interface RiskFile {
    file_path: string;
    owner_email: string;
    owner_name: string;
    commit_count: number;
    last_modified: string;
    is_critical: boolean;
    lines_of_code: number;
}

interface OwnershipData {
    developer: {
        id: number;
        display_name: string;
        git_email: string;
        slack_id: string;
        is_active: boolean;
        created_at: string;
    };
    files_owned: number;
    total_files: number;
    ownership_percentage: number;
    risk_level: 'low' | 'medium' | 'high' | 'critical';
    suggested_mentees: string[];
}

interface BusFactorStats {
    risk_files: RiskFile[];
    ownership_data: OwnershipData[];
    total_files_analyzed: number;
    high_risk_files: number;
    knowledge_transfer_suggestions: {
        mentor: string;
        mentee: string;
        files: string[];
        priority: 'low' | 'medium' | 'high';
    }[];
}

export function BusFactor() {
    const { data: busFactorData, isLoading, error } = useBusFactorData();

    if (isLoading) {
        return (
            <div className="space-y-6">
                <h1 className="text-3xl font-heading font-bold text-text-primary">Bus Factor Analysis</h1>
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
                <h1 className="text-3xl font-heading font-bold text-text-primary">Bus Factor Analysis</h1>
                <Card className="border-red-200 bg-red-50">
                    <CardContent className="pt-6">
                        <div className="flex items-center space-x-2">
                            <AlertTriangle className="h-5 w-5 text-red-600" />
                            <p className="text-red-600">Failed to load bus factor data. Please check if the backend is running.</p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    const stats = busFactorData as BusFactorStats;

    // Calculate summary statistics
    const criticalRiskFiles = stats?.risk_files.filter(f => f.is_critical).length || 0;
    const highRiskDevelopers = stats?.ownership_data.filter(d => d.risk_level === 'high' || d.risk_level === 'critical').length || 0;
    const avgOwnershipPercentage = stats?.ownership_data.reduce((sum, d) => sum + d.ownership_percentage, 0) / (stats?.ownership_data.length || 1) || 0;

    // Prepare data for ownership pie chart
    const ownershipChartData = stats?.ownership_data.map(dev => ({
        name: dev.developer.display_name.split(' ')[0],
        fullName: dev.developer.display_name,
        value: dev.ownership_percentage,
        files: dev.files_owned,
        riskLevel: dev.risk_level,
    })) || [];

    // Prepare data for risk level bar chart
    const riskLevelData = [
        { level: 'Low', count: stats?.ownership_data.filter(d => d.risk_level === 'low').length || 0, color: '#10b981' },
        { level: 'Medium', count: stats?.ownership_data.filter(d => d.risk_level === 'medium').length || 0, color: '#f59e0b' },
        { level: 'High', count: stats?.ownership_data.filter(d => d.risk_level === 'high').length || 0, color: '#ef4444' },
        { level: 'Critical', count: stats?.ownership_data.filter(d => d.risk_level === 'critical').length || 0, color: '#dc2626' },
    ];

    // Color mapping for risk levels
    const getRiskColor = (riskLevel: string) => {
        switch (riskLevel) {
            case 'low': return '#10b981';
            case 'medium': return '#f59e0b';
            case 'high': return '#ef4444';
            case 'critical': return '#dc2626';
            default: return '#6b7280';
        }
    };

    const summaryStats = [
        {
            title: 'Total Files Analyzed',
            value: stats?.total_files_analyzed || 0,
            icon: FileText,
            description: 'Files in repository',
            trend: 'Complete analysis'
        },
        {
            title: 'High Risk Files',
            value: criticalRiskFiles,
            icon: AlertTriangle,
            description: 'Single owner critical files',
            trend: criticalRiskFiles > 0 ? 'Needs attention' : 'All good'
        },
        {
            title: 'At-Risk Developers',
            value: highRiskDevelopers,
            icon: Users,
            description: 'High knowledge concentration',
            trend: highRiskDevelopers > 0 ? 'Knowledge sharing needed' : 'Well distributed'
        },
        {
            title: 'Avg. Ownership',
            value: `${Math.round(avgOwnershipPercentage)}%`,
            icon: TrendingUp,
            description: 'Average file ownership',
            trend: avgOwnershipPercentage > 30 ? 'High concentration' : 'Good distribution'
        },
    ];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-heading font-bold text-text-primary">Bus Factor Analysis</h1>
                    <p className="text-gray-600 mt-2">
                        Identify knowledge concentration risks and plan knowledge sharing
                    </p>
                </div>
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <GitBranch className="h-4 w-4" />
                    <span>Updated from git history</span>
                </div>
            </div>

            {/* Alert for critical risks */}
            {criticalRiskFiles > 0 && (
                <Card className="border-red-200 bg-red-50">
                    <CardContent className="pt-6">
                        <div className="flex items-center space-x-2">
                            <AlertTriangle className="h-5 w-5 text-red-600" />
                            <p className="text-red-800">
                                <span className="font-semibold">{criticalRiskFiles} critical file{criticalRiskFiles > 1 ? 's' : ''}</span> have single owners - immediate knowledge sharing recommended
                            </p>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {summaryStats.map((stat) => (
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
                                <TrendingUp className="h-3 w-3 text-blue-500 mr-1" />
                                <span className="text-blue-600">{stat.trend}</span>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Main Analysis Content */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Ownership Distribution Chart */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center space-x-2">
                            <User className="h-5 w-5" />
                            <span>Knowledge Distribution</span>
                        </CardTitle>
                        <CardDescription>
                            File ownership percentage by developer
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={ownershipChartData}
                                        cx="50%"
                                        cy="50%"
                                        outerRadius={80}
                                        dataKey="value"
                                        label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                                    >
                                        {ownershipChartData.map((entry, index) => (
                                            <Cell
                                                key={`cell-${index}`}
                                                fill={getRiskColor(entry.riskLevel)}
                                            />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        content={({ active, payload }) => {
                                            if (active && payload && payload.length) {
                                                const data = payload[0].payload;
                                                return (
                                                    <div className="bg-white p-3 border rounded-lg shadow-lg">
                                                        <p className="font-semibold">{data.fullName}</p>
                                                        <p className="text-sm">
                                                            <span className="font-medium">{data.value.toFixed(1)}% ownership</span>
                                                        </p>
                                                        <p className="text-sm text-gray-600">
                                                            {data.files} files owned
                                                        </p>
                                                        <p className="text-sm">
                                                            Risk: <span className={`font-medium ${data.riskLevel === 'critical' ? 'text-red-600' :
                                                                    data.riskLevel === 'high' ? 'text-orange-600' :
                                                                        data.riskLevel === 'medium' ? 'text-yellow-600' :
                                                                            'text-green-600'
                                                                }`}>
                                                                {data.riskLevel}
                                                            </span>
                                                        </p>
                                                    </div>
                                                );
                                            }
                                            return null;
                                        }}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                {/* Risk Level Distribution */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center space-x-2">
                            <AlertTriangle className="h-5 w-5" />
                            <span>Risk Level Distribution</span>
                        </CardTitle>
                        <CardDescription>
                            Number of developers by knowledge concentration risk
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={riskLevelData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                    <XAxis
                                        dataKey="level"
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
                                                        <p className="font-semibold">{label} Risk</p>
                                                        <p className="text-sm">
                                                            <span className="font-medium">{data.count} developer{data.count !== 1 ? 's' : ''}</span>
                                                        </p>
                                                    </div>
                                                );
                                            }
                                            return null;
                                        }}
                                    />
                                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                                        {riskLevelData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Knowledge Risk Files */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                        <FileText className="h-5 w-5" />
                        <span>High-Risk Files</span>
                    </CardTitle>
                    <CardDescription>
                        Files with single active contributors that pose knowledge risks
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {stats?.risk_files && stats.risk_files.length > 0 ? (
                        <div className="space-y-3">
                            {stats.risk_files.slice(0, 10).map((file, index) => (
                                <div
                                    key={index}
                                    className={`p-4 rounded-lg border-2 transition-all hover:shadow-md ${file.is_critical
                                            ? 'border-red-200 bg-red-50'
                                            : 'border-yellow-200 bg-yellow-50'
                                        }`}
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium text-text-primary truncate">
                                                {file.file_path}
                                            </p>
                                            <p className="text-xs text-gray-600 mt-1">
                                                Owner: {file.owner_name} ({file.owner_email})
                                            </p>
                                            <p className="text-xs text-gray-500 mt-1">
                                                {file.commit_count} commits • {file.lines_of_code} lines • Last modified: {new Date(file.last_modified).toLocaleDateString()}
                                            </p>
                                        </div>
                                        <div className="flex flex-col items-end space-y-1 ml-4">
                                            {file.is_critical && (
                                                <span className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded-full font-medium">
                                                    Critical
                                                </span>
                                            )}
                                            <span className="px-2 py-1 text-xs bg-orange-100 text-orange-700 rounded-full">
                                                Single Owner
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                            {stats.risk_files.length > 10 && (
                                <div className="text-center py-4 text-gray-500">
                                    <p className="text-sm">
                                        Showing 10 of {stats.risk_files.length} high-risk files
                                    </p>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-500">
                            <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                            <p className="text-sm">No high-risk files detected</p>
                            <p className="text-xs">Knowledge is well distributed across the team</p>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Knowledge Transfer Suggestions */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                        <Target className="h-5 w-5" />
                        <span>Knowledge Transfer Recommendations</span>
                    </CardTitle>
                    <CardDescription>
                        Suggested mentor-mentee pairings to reduce knowledge concentration
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {stats?.knowledge_transfer_suggestions && stats.knowledge_transfer_suggestions.length > 0 ? (
                        <div className="space-y-4">
                            {stats.knowledge_transfer_suggestions.map((suggestion, index) => (
                                <div
                                    key={index}
                                    className={`p-4 rounded-lg border-2 transition-all hover:shadow-md ${suggestion.priority === 'high'
                                            ? 'border-red-200 bg-red-50'
                                            : suggestion.priority === 'medium'
                                                ? 'border-yellow-200 bg-yellow-50'
                                                : 'border-blue-200 bg-blue-50'
                                        }`}
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <div className="flex items-center space-x-2 mb-2">
                                                <Users className="h-4 w-4 text-gray-600" />
                                                <p className="text-sm font-medium text-text-primary">
                                                    {suggestion.mentor} → {suggestion.mentee}
                                                </p>
                                            </div>
                                            <p className="text-xs text-gray-600 mb-2">
                                                Suggested files for knowledge transfer:
                                            </p>
                                            <div className="flex flex-wrap gap-1">
                                                {suggestion.files.slice(0, 3).map((file, fileIndex) => (
                                                    <span
                                                        key={fileIndex}
                                                        className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
                                                    >
                                                        {file.split('/').pop()}
                                                    </span>
                                                ))}
                                                {suggestion.files.length > 3 && (
                                                    <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                                                        +{suggestion.files.length - 3} more
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <div className="ml-4">
                                            <span className={`px-2 py-1 text-xs rounded-full font-medium ${suggestion.priority === 'high'
                                                    ? 'bg-red-100 text-red-700'
                                                    : suggestion.priority === 'medium'
                                                        ? 'bg-yellow-100 text-yellow-700'
                                                        : 'bg-blue-100 text-blue-700'
                                                }`}>
                                                {suggestion.priority} priority
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-500">
                            <Target className="h-8 w-8 mx-auto mb-2 opacity-50" />
                            <p className="text-sm">No knowledge transfer needed</p>
                            <p className="text-xs">Knowledge distribution is healthy across the team</p>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Detailed Developer Ownership */}
            <Card>
                <CardHeader>
                    <CardTitle>Developer Knowledge Ownership</CardTitle>
                    <CardDescription>
                        Detailed breakdown of file ownership and risk levels per developer
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {stats?.ownership_data.map((dev) => (
                            <div
                                key={dev.developer.id}
                                className={`p-4 rounded-lg border-2 transition-all hover:shadow-md ${dev.risk_level === 'critical'
                                        ? 'border-red-200 bg-red-50'
                                        : dev.risk_level === 'high'
                                            ? 'border-orange-200 bg-orange-50'
                                            : dev.risk_level === 'medium'
                                                ? 'border-yellow-200 bg-yellow-50'
                                                : 'border-green-200 bg-green-50'
                                    }`}
                            >
                                <div className="flex items-center space-x-3 mb-3">
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-medium ${dev.risk_level === 'critical' ? 'bg-red-500' :
                                            dev.risk_level === 'high' ? 'bg-orange-500' :
                                                dev.risk_level === 'medium' ? 'bg-yellow-500' :
                                                    'bg-green-500'
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

                                <div className="space-y-2">
                                    <div className="flex justify-between items-center">
                                        <span className="text-sm text-gray-600">Ownership</span>
                                        <span className="text-sm font-medium">
                                            {dev.ownership_percentage.toFixed(1)}%
                                        </span>
                                    </div>

                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                        <div
                                            className={`h-2 rounded-full transition-all ${dev.risk_level === 'critical' ? 'bg-red-500' :
                                                    dev.risk_level === 'high' ? 'bg-orange-500' :
                                                        dev.risk_level === 'medium' ? 'bg-yellow-500' :
                                                            'bg-green-500'
                                                }`}
                                            style={{
                                                width: `${Math.min(dev.ownership_percentage, 100)}%`
                                            }}
                                        ></div>
                                    </div>

                                    <div className="flex justify-between items-center text-xs text-gray-500">
                                        <span>{dev.files_owned} files owned</span>
                                        <span className={`font-medium ${dev.risk_level === 'critical' ? 'text-red-600' :
                                                dev.risk_level === 'high' ? 'text-orange-600' :
                                                    dev.risk_level === 'medium' ? 'text-yellow-600' :
                                                        'text-green-600'
                                            }`}>
                                            {dev.risk_level} risk
                                        </span>
                                    </div>

                                    {dev.suggested_mentees.length > 0 && (
                                        <div className="mt-2 pt-2 border-t border-gray-200">
                                            <p className="text-xs text-gray-600 mb-1">Suggested mentees:</p>
                                            <div className="flex flex-wrap gap-1">
                                                {dev.suggested_mentees.slice(0, 2).map((mentee, index) => (
                                                    <span
                                                        key={index}
                                                        className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded"
                                                    >
                                                        {mentee}
                                                    </span>
                                                ))}
                                                {dev.suggested_mentees.length > 2 && (
                                                    <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                                                        +{dev.suggested_mentees.length - 2}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
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