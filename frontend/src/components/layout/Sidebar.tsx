import React from 'react';
import { NavLink } from 'react-router-dom';
import {
    BarChart3,
    Users,
    Settings,
    AlertTriangle,
    History,
    Home,
    Cog
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Team Health', href: '/team', icon: BarChart3 },
    { name: 'Bus Factor', href: '/bus-factor', icon: AlertTriangle },
    { name: 'Assignment History', href: '/history', icon: History },
    { name: 'User Management', href: '/users', icon: Users },
    { name: 'Configuration', href: '/configuration', icon: Cog },
    { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
    return (
        <aside className="w-64 bg-white shadow-sm border-r border-gray-200">
            <nav className="p-4 pt-8 space-y-2">
                {navigation.map((item) => (
                    <NavLink
                        key={item.name}
                        to={item.href}
                        className={({ isActive }) =>
                            cn(
                                'flex items-center space-x-3 px-3 py-2 rounded-base text-sm font-medium transition-colors',
                                isActive
                                    ? 'bg-primary text-white'
                                    : 'text-gray-700 hover:bg-accent hover:text-text-primary'
                            )
                        }
                    >
                        <item.icon className="w-5 h-5" />
                        <span>{item.name}</span>
                    </NavLink>
                ))}
            </nav>
        </aside>
    );
}