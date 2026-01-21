import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
    Bot,
    GitBranch,
    Users,
    AlertTriangle,
    Target,
    Zap,
    Shield,
    BarChart3,
    Clock,
    Settings,
    BookOpen,
    HelpCircle
} from 'lucide-react';

interface GlossaryItem {
    term: string;
    definition: string;
    icon: React.ElementType;
}

const glossaryItems: GlossaryItem[] = [
    {
        term: 'Mahoraga',
        definition: 'An autonomous bug triage system that automatically analyzes, categorizes, and assigns incoming bug reports to the most suitable developers based on their expertise, current workload, and historical performance.',
        icon: Bot,
    },
    {
        term: 'Bug Triage',
        definition: 'The process of reviewing, prioritizing, and assigning bug reports to appropriate team members. Mahoraga automates this traditionally manual process using machine learning algorithms.',
        icon: Target,
    },
    {
        term: 'Confidence Score',
        definition: 'A percentage indicating how certain Mahoraga is about its assignment decision. Higher scores (85%+) indicate strong matches, while lower scores may require human review.',
        icon: BarChart3,
    },
    {
        term: 'Bus Factor',
        definition: 'A measure of risk associated with knowledge concentration. It represents the minimum number of team members who would need to be unavailable before a project or area of code becomes unmaintainable.',
        icon: AlertTriangle,
    },
    {
        term: 'Team Health',
        definition: 'Metrics and indicators that show the overall wellbeing and productivity of the development team, including workload distribution, burnout risk, and collaboration patterns.',
        icon: Users,
    },
    {
        term: 'Developer Workload',
        definition: 'The current number of active bug assignments for each developer. Mahoraga considers workload when making assignments to prevent overloading individual team members.',
        icon: Clock,
    },
    {
        term: 'Overloaded Status',
        definition: 'A warning state triggered when a developer has more than 5 active bug assignments. Mahoraga will avoid assigning new bugs to overloaded developers.',
        icon: AlertTriangle,
    },
    {
        term: 'Root Cause Analysis',
        definition: 'Mahoraga attempts to identify the underlying cause of a bug based on the report content, helping developers understand what needs to be fixed.',
        icon: GitBranch,
    },
    {
        term: 'Draft PR',
        definition: 'An automated pull request created by Mahoraga with a proposed fix for simple bugs. These require human review before merging.',
        icon: Zap,
    },
    {
        term: 'Processing Time',
        definition: 'The time taken by Mahoraga to analyze a bug report and make an assignment decision. Typical processing times are under 1 second.',
        icon: Clock,
    },
];

const systemFeatures = [
    {
        title: 'Autonomous Assignment',
        description: 'Mahoraga analyzes bug reports and automatically assigns them to the most qualified developers without human intervention.',
        icon: Bot,
    },
    {
        title: 'Workload Balancing',
        description: 'The system monitors developer workloads and distributes assignments evenly to prevent burnout and maintain productivity.',
        icon: Shield,
    },
    {
        title: 'Real-time Dashboard',
        description: 'Monitor team health, assignment statistics, and system performance through an intuitive dashboard interface.',
        icon: BarChart3,
    },
    {
        title: 'Configurable Rules',
        description: 'Customize assignment rules, thresholds, and preferences to match your team workflow and policies.',
        icon: Settings,
    },
];

export function Glossary() {
    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-3xl font-heading font-bold text-text-primary">About Mahoraga</h1>
                <p className="text-gray-600 mt-2">
                    Learn about the Mahoraga autonomous bug triage system and its terminology
                </p>
            </div>

            {/* System Overview */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                        <BookOpen className="h-5 w-5" />
                        <span>System Overview</span>
                    </CardTitle>
                    <CardDescription>
                        Understanding the Mahoraga autonomous bug triage system
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <p className="text-gray-700 leading-relaxed mb-6">
                        Mahoraga is an intelligent bug triage system designed to streamline your development workflow.
                        Named after a concept of relentless adaptation, the system continuously learns from your team's
                        patterns and preferences to make increasingly accurate assignment decisions. By automating the
                        time-consuming process of bug triage, Mahoraga allows your team to focus on what matters most:
                        writing great code and building amazing products.
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {systemFeatures.map((feature) => (
                            <div
                                key={feature.title}
                                className="flex items-start space-x-3 p-4 bg-gray-50 rounded-lg"
                            >
                                <div className="flex-shrink-0 w-10 h-10 bg-primary text-white rounded-lg flex items-center justify-center">
                                    <feature.icon className="w-5 h-5" />
                                </div>
                                <div>
                                    <h4 className="font-medium text-gray-900">{feature.title}</h4>
                                    <p className="text-sm text-gray-600 mt-1">{feature.description}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Glossary Terms */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                        <HelpCircle className="h-5 w-5" />
                        <span>Terminology</span>
                    </CardTitle>
                    <CardDescription>
                        Key terms and concepts used throughout the Mahoraga dashboard
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="divide-y divide-gray-200">
                        {glossaryItems.map((item) => (
                            <div
                                key={item.term}
                                className="py-4 first:pt-0 last:pb-0"
                            >
                                <div className="flex items-start space-x-3">
                                    <div className="flex-shrink-0 w-8 h-8 bg-gray-100 text-gray-600 rounded-lg flex items-center justify-center">
                                        <item.icon className="w-4 h-4" />
                                    </div>
                                    <div>
                                        <dt className="font-semibold text-gray-900">
                                            {item.term}
                                        </dt>
                                        <dd className="text-gray-600 mt-1">
                                            {item.definition}
                                        </dd>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Usage Tips */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                        <Zap className="h-5 w-5" />
                        <span>Tips for Best Results</span>
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <ul className="space-y-3 text-gray-700">
                        <li className="flex items-start space-x-2">
                            <span className="flex-shrink-0 w-6 h-6 bg-primary text-white rounded-full flex items-center justify-center text-sm font-medium">1</span>
                            <span>Write clear, descriptive bug reports with steps to reproduce for more accurate assignments.</span>
                        </li>
                        <li className="flex items-start space-x-2">
                            <span className="flex-shrink-0 w-6 h-6 bg-primary text-white rounded-full flex items-center justify-center text-sm font-medium">2</span>
                            <span>Regularly review and provide feedback on assignments to help Mahoraga learn your preferences.</span>
                        </li>
                        <li className="flex items-start space-x-2">
                            <span className="flex-shrink-0 w-6 h-6 bg-primary text-white rounded-full flex items-center justify-center text-sm font-medium">3</span>
                            <span>Monitor the Bus Factor page to identify knowledge concentration risks in your codebase.</span>
                        </li>
                        <li className="flex items-start space-x-2">
                            <span className="flex-shrink-0 w-6 h-6 bg-primary text-white rounded-full flex items-center justify-center text-sm font-medium">4</span>
                            <span>Use the Configuration page to adjust assignment thresholds and rules for your team.</span>
                        </li>
                    </ul>
                </CardContent>
            </Card>
        </div>
    );
}
