import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

export function Layout() {
    return (
        <div className="min-h-screen bg-background flex flex-col">
            <div className="sticky top-0 z-50">
                <Header />
            </div>
            <div className="flex flex-1">
                <div className="fixed h-[calc(100vh-theme(spacing.20))] top-20 hidden md:block z-40">
                    <Sidebar />
                </div>
                <main className="flex-1 p-6 md:ml-64">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}