import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { TeamHealth } from './pages/TeamHealth';
import { BusFactor } from './pages/BusFactor';
import { AssignmentHistory } from './pages/AssignmentHistory';
import { UserManagement } from './pages/UserManagement';
import { Settings } from './pages/Settings';
import { Configuration } from './pages/Configuration';

// Create a client
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: 2,
            staleTime: 30000, // 30 seconds
            refetchOnWindowFocus: false,
        },
    },
});

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <Router>
                <Routes>
                    <Route path="/" element={<Layout />}>
                        <Route index element={<Dashboard />} />
                        <Route path="team" element={<TeamHealth />} />
                        <Route path="bus-factor" element={<BusFactor />} />
                        <Route path="history" element={<AssignmentHistory />} />
                        <Route path="users" element={<UserManagement />} />
                        <Route path="settings" element={<Settings />} />
                        <Route path="configuration" element={<Configuration />} />
                    </Route>
                </Routes>
            </Router>
        </QueryClientProvider>
    );
}

export default App;