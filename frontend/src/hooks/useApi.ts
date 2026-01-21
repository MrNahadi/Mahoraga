import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, type Developer, type SystemSettings } from '@/lib/api';

// Dashboard hooks
export const useTeamStats = () => {
    return useQuery({
        queryKey: ['team-stats'],
        queryFn: () => apiClient.getTeamStats(),
        refetchInterval: 30000, // 30 second refresh
        staleTime: 25000, // Consider data stale after 25 seconds
    });
};

export const useBusFactorData = () => {
    return useQuery({
        queryKey: ['bus-factor'],
        queryFn: () => apiClient.getBusFactorData(),
        refetchInterval: 300000, // 5 minute refresh
        staleTime: 240000, // Consider data stale after 4 minutes
    });
};

export const useHealthMetrics = () => {
    return useQuery({
        queryKey: ['health-metrics'],
        queryFn: () => apiClient.getHealthMetrics(),
        refetchInterval: 60000, // 1 minute refresh
        staleTime: 50000,
    });
};

// User management hooks
export const useUsers = () => {
    return useQuery({
        queryKey: ['users'],
        queryFn: () => apiClient.getUsers(),
        staleTime: 300000, // 5 minutes
    });
};

export const useCreateUser = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (user: Omit<Developer, 'id' | 'created_at'>) =>
            apiClient.createUser(user),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
        },
    });
};

export const useUpdateUser = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, user }: { id: number; user: Partial<Developer> }) =>
            apiClient.updateUser(id, user),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
        },
    });
};

export const useDeleteUser = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: number) => apiClient.deleteUser(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
        },
    });
};

// Configuration hooks
export const useSettings = () => {
    return useQuery({
        queryKey: ['system-settings'],
        queryFn: () => apiClient.getSettings(),
        staleTime: 300000, // 5 minutes
    });
};

export const useUpdateSettings = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (settings: Partial<SystemSettings>) =>
            apiClient.updateSettings(settings),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['system-settings'] });
            // Also refresh team stats as settings changes might affect them
            queryClient.invalidateQueries({ queryKey: ['team-stats'] });
        },
    });
};

// Assignment hooks
export const useAssignmentHistory = (limit = 50, offset = 0) => {
    return useQuery({
        queryKey: ['assignment-history', limit, offset],
        queryFn: () => apiClient.getAssignmentHistory(limit, offset),
        staleTime: 60000, // 1 minute
    });
};

export const useReassignBug = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ assignmentId, newAssigneeEmail, reason }: {
            assignmentId: number;
            newAssigneeEmail: string;
            reason: string;
        }) => apiClient.reassignBug(assignmentId, newAssigneeEmail, reason),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['assignment-history'] });
            queryClient.invalidateQueries({ queryKey: ['team-stats'] });
        },
    });
};