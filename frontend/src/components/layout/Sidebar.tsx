import React, { useCallback } from 'react';
import { NavLink } from 'react-router-dom';
import {
    BarChart3,
    Users,
    Settings,
    AlertTriangle,
    History,
    Home,
    Cog,
    BookOpen
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
    // Handle keyboard navigation within the sidebar
    const handleKeyDown = useCallback((event: React.KeyboardEvent<HTMLElement>) => {
        const currentElement = event.currentTarget;
        const navLinks = currentElement.querySelectorAll<HTMLAnchorElement>('a[role="menuitem"]');
        const currentIndex = Array.from(navLinks).findIndex(link => link === document.activeElement);

        if (event.key === 'ArrowDown') {
            event.preventDefault();
            const nextIndex = currentIndex < navLinks.length - 1 ? currentIndex + 1 : 0;
            navLinks[nextIndex]?.focus();
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            const prevIndex = currentIndex > 0 ? currentIndex - 1 : navLinks.length - 1;
            navLinks[prevIndex]?.focus();
        } else if (event.key === 'Home') {
            event.preventDefault();
            navLinks[0]?.focus();
        } else if (event.key === 'End') {
            event.preventDefault();
            navLinks[navLinks.length - 1]?.focus();
        }
    }, []);

    return (
        <aside className="w-64 bg-white shadow-sm border-r border-gray-200 h-full flex flex-col">
            <nav
                className="p-4 pt-8 space-y-2 flex-1"
                role="menu"
                aria-label="Main navigation"
                onKeyDown={handleKeyDown}
            >
                {navigation.map((item) => (
                    <NavLink
                        key={item.name}
                        to={item.href}
                        role="menuitem"
                        className={({ isActive }) =>
                            cn(
                                'flex items-center space-x-3 px-3 py-2 rounded-base text-sm font-medium transition-colors',
                                'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
                                isActive
                                    ? 'bg-primary text-white'
                                    : 'text-gray-700 hover:bg-accent hover:text-text-primary'
                            )
                        }
                    >
                        <item.icon className="w-5 h-5" aria-hidden="true" />
                        <span>{item.name}</span>
                    </NavLink>
                ))}
            </nav>

            {/* Glossary link at bottom */}
            <div className="p-4 border-t border-gray-200">
                <NavLink
                    to="/glossary"
                    role="menuitem"
                    className={({ isActive }) =>
                        cn(
                            'flex items-center space-x-3 px-3 py-2 rounded-base text-sm font-medium transition-colors',
                            'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
                            isActive
                                ? 'bg-primary text-white'
                                : 'text-gray-700 hover:bg-accent hover:text-text-primary'
                        )
                    }
                >
                    <BookOpen className="w-5 h-5" aria-hidden="true" />
                    <span>Glossary</span>
                </NavLink>
            </div>
        </aside>
    );
}