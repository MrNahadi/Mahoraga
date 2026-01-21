import { useHealthMetrics } from '@/hooks/useApi';
import { AlertCircle } from 'lucide-react';

export function Header() {
    const { data: health, isError } = useHealthMetrics();

    return (
        <header className="bg-primary text-white shadow-lg">
            <div className="px-6 py-4 md:pl-72 pr-10">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <img
                            src="/mahoraga-logo-white.svg"
                            alt="Mahoraga Logo"
                            className="w-16 h-16"
                        />
                        <div>
                            <h1 className="text-2xl font-heading font-bold">Mahoraga Command Center</h1>
                            <p className="text-sm opacity-90">Autonomous Bug Triage Dashboard</p>
                        </div>
                    </div>

                    <div className="flex items-center space-x-4">
                        {/* System Health Indicator */}
                        <div className="flex items-center space-x-2">
                            {isError ? (
                                <>
                                    <AlertCircle className="w-5 h-5 text-red-300" />
                                    <span className="text-sm">System Offline</span>
                                </>
                            ) : (
                                <>
                                    <span className="relative flex h-3 w-3">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                                    </span>
                                    <span className="text-sm">
                                        {health ? `Uptime: ${Math.floor((health.uptime || 0) / 3600)}h` : 'Connecting...'}
                                    </span>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );
}