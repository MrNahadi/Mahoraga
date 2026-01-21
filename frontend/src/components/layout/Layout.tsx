import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { Breadcrumbs } from '../ui/Breadcrumbs';

export function Layout() {
    return (
        <div className="min-h-screen bg-background flex flex-col">
            {/* Skip link for keyboard users */}
            <a
                href="#main-content"
                className="skip-link"
            >
                Skip to main content
            </a>
            <div className="sticky top-0 z-50">
                <Header />
                <Breadcrumbs />
            </div>
            <div className="flex flex-1">
                <div className="fixed h-[calc(100vh-theme(spacing.20))] top-20 hidden md:block z-40">
                    <Sidebar />
                </div>
                <main id="main-content" className="flex-1 p-6 md:ml-64" tabIndex={-1}>
                    <Outlet />
                </main>
            </div>
        </div>
    );
}