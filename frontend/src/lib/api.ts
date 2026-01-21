const API_BASE_URL = 'http://localhost:8000/api';

export interface Developer {
    id: number;
    git_email: string;
    slack_id: string;
    display_name: string;
    is_active: boolean;
    created_at: string;
}

export interface Assignment {
    id: number;
    issue_id: string;
    issue_url: string;
    assigned_to_email: string;
    confidence: number;
    reasoning: string;
    status: string;
    created_at: string;
}

export interface TriageDecision {
    id: number;
    issue_id: string;
    stack_trace?: string;
    affected_files: string[];
    root_cause?: string;
    confidence: number;
    draft_pr_url?: string;
    processing_time_ms: number;
    created_at: string;
}

export interface TeamStats {
    developers: Array<{
        developer: Developer;
        active_bugs: number;
        is_overloaded: boolean;
    }>;
    recent_decisions: TriageDecision[];
    total_assignments: number;
    avg_confidence: number;
}

export interface BusFactorData {
    risk_files: Array<{
        file_path: string;
        owner_email: string;
        owner_name: string;
        commit_count: number;
        last_modified: string;
        is_critical: boolean;
        lines_of_code: number;
    }>;
    ownership_data: Array<{
        developer: Developer;
        files_owned: number;
        total_files: number;
        ownership_percentage: number;
        risk_level: 'low' | 'medium' | 'high' | 'critical';
        suggested_mentees: string[];
    }>;
    total_files_analyzed: number;
    high_risk_files: number;
    knowledge_transfer_suggestions: Array<{
        mentor: string;
        mentee: string;
        files: string[];
        priority: 'low' | 'medium' | 'high';
    }>;
}

export interface SystemSettings {
    confidence_threshold: number;
    draft_pr_enabled: boolean;
    duplicate_detection_window: number;
    notification_enabled: boolean;
}

class ApiClient {
    private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
        const url = `${API_BASE_URL}${endpoint}`;
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options?.headers,
            },
            ...options,
        });

        if (!response.ok) {
            throw new Error(`API request failed: ${response.status} ${response.statusText}`);
        }

        return response.json();
    }

    // Dashboard endpoints
    async getTeamStats(): Promise<TeamStats> {
        return this.request<TeamStats>('/dashboard/stats');
    }

    async getBusFactorData(): Promise<BusFactorData> {
        return this.request<BusFactorData>('/dashboard/bus-factor');
    }

    async getHealthMetrics(): Promise<{ status: string; uptime: number; version: string }> {
        return this.request('/dashboard/health');
    }

    // User management endpoints
    async getUsers(): Promise<Developer[]> {
        return this.request<Developer[]>('/config/users');
    }

    async createUser(user: Omit<Developer, 'id' | 'created_at'>): Promise<Developer> {
        return this.request<Developer>('/config/users', {
            method: 'POST',
            body: JSON.stringify(user),
        });
    }

    async updateUser(id: number, user: Partial<Developer>): Promise<Developer> {
        return this.request<Developer>(`/config/users/${id}`, {
            method: 'PUT',
            body: JSON.stringify(user),
        });
    }

    async deleteUser(id: number): Promise<void> {
        return this.request<void>(`/config/users/${id}`, {
            method: 'DELETE',
        });
    }

    // Configuration endpoints
    async getSettings(): Promise<SystemSettings> {
        return this.request<SystemSettings>('/config/settings');
    }

    async updateSettings(settings: Partial<SystemSettings>): Promise<SystemSettings> {
        return this.request<SystemSettings>('/config/settings', {
            method: 'PUT',
            body: JSON.stringify(settings),
        });
    }

    // Assignment endpoints
    async getAssignmentHistory(limit = 50, offset = 0): Promise<Assignment[]> {
        return this.request<Assignment[]>(`/assignments/history?limit=${limit}&offset=${offset}`);
    }

    async reassignBug(assignmentId: number, newAssigneeEmail: string, reason: string): Promise<Assignment> {
        return this.request<Assignment>(`/assignments/${assignmentId}/reassign`, {
            method: 'POST',
            body: JSON.stringify({ new_assignee_email: newAssigneeEmail, reason }),
        });
    }
}

export const apiClient = new ApiClient();