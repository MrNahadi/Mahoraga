import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '@/lib/utils';

interface BreadcrumbItem {
    label: string;
    href: string;
}

const routeLabels: Record<string, string> = {
    '': 'Dashboard',
    'team': 'Team Health',
    'bus-factor': 'Bus Factor',
    'history': 'Assignment History',
    'users': 'User Management',
    'settings': 'Settings',
    'configuration': 'Configuration',
    'glossary': 'Glossary',
};

export function Breadcrumbs() {
    const location = useLocation();
    const pathSegments = location.pathname.split('/').filter(Boolean);

    const breadcrumbs: BreadcrumbItem[] = [
        { label: 'Home', href: '/' },
    ];

    let currentPath = '';
    pathSegments.forEach((segment) => {
        currentPath += `/${segment}`;
        const label = routeLabels[segment] || segment.charAt(0).toUpperCase() + segment.slice(1);
        breadcrumbs.push({ label, href: currentPath });
    });

    // Don't show breadcrumbs on home page
    if (pathSegments.length === 0) {
        return null;
    }

    return (
        <nav
            aria-label="Breadcrumb"
            className="flex items-center space-x-2 text-sm text-gray-600 py-3 px-6 md:pl-72 bg-gray-50 border-b border-gray-200"
        >
            {breadcrumbs.map((crumb, index) => {
                const isLast = index === breadcrumbs.length - 1;
                const isFirst = index === 0;

                return (
                    <React.Fragment key={crumb.href}>
                        {index > 0 && (
                            <ChevronRight className="w-4 h-4 text-gray-400" aria-hidden="true" />
                        )}
                        {isLast ? (
                            <span
                                className="font-medium text-gray-900"
                                aria-current="page"
                            >
                                {crumb.label}
                            </span>
                        ) : (
                            <Link
                                to={crumb.href}
                                className={cn(
                                    "hover:text-primary transition-colors",
                                    "focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded",
                                    isFirst && "flex items-center space-x-1"
                                )}
                            >
                                {isFirst && <Home className="w-4 h-4" aria-hidden="true" />}
                                <span>{crumb.label}</span>
                            </Link>
                        )}
                    </React.Fragment>
                );
            })}
        </nav>
    );
}
