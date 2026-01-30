/**
 * Pulse AI API Service
 * Complete API client for connecting frontend to backend
 */

import axios, { AxiosError, AxiosResponse } from 'axios';

// API Base URL - configurable via environment
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with defaults
const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000,
});

// Add request interceptor for auth
api.interceptors.request.use((config) => {
    const apiKey = localStorage.getItem('pulse_api_key');

    if (apiKey) {
        config.headers['X-API-Key'] = apiKey;
    }

    return config;
});

// Add response interceptor for error handling
api.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error: AxiosError) => {
        if (error.response?.status === 401) {
            // Clear auth and redirect to login
            localStorage.removeItem('pulse_api_key');
            localStorage.removeItem('pulse_user_id');
            localStorage.removeItem('pulse_user');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// ============================================
// Types
// ============================================

export interface User {
    id: number;
    email: string;
    name: string;
    age?: number;
    gender?: string;
}

export interface HealthMetric {
    value: number | null;
    baseline: number | null;
    unit: string;
}

export interface CareScoreData {
    score: number | null;
    status: string;
    components: {
        severity: number;
        persistence: number;
        cross_signal: number;
        manual_modifier: number;
    };
    drift_score: number;
    confidence: number;
    stability: number;
    explanation: string | null;
    updated_at: string | null;
}

export interface Escalation {
    id: number;
    level: number;
    title: string;
    message: string;
    timestamp: string;
    acknowledged: boolean;
}

export interface DashboardSummary {
    user: User;
    care_score: CareScoreData | null;
    current_metrics: {
        heart_rate: HealthMetric;
        hrv: HealthMetric;
        sleep_duration: HealthMetric;
        activity_level: HealthMetric;
        breathing_rate: HealthMetric;
        bp_systolic: HealthMetric;
        bp_diastolic: HealthMetric;
        blood_sugar: HealthMetric;
        updated_at: string | null;
    } | null;
    escalations: Escalation[];
    score_trend: Array<{
        date: string;
        score: number;
        status: string;
    }>;
}

export interface TrendData {
    date: string;
    heart_rate: number | null;
    hrv: number | null;
    sleep_duration: number | null;
    activity_level: number | null;
    breathing_rate: number | null;
}

export interface Insight {
    type: 'warning' | 'info' | 'success';
    metric: string;
    title: string;
    description: string;
    current: number;
    baseline: number;
    recommendation: string;
}

export interface DriveFile {
    id: string;
    name: string;
    mimeType: string;
    size: number;
    md5Checksum?: string;
}

export interface IngestionJob {
    id: number;
    job_type: string;
    status: string;
    started_at: string;
    completed_at: string | null;
    files_found: number;
    files_processed: number;
    records_imported: number;
    error_message: string | null;
}

// ============================================
// Auth Service
// ============================================

export const authService = {
    /**
     * Login with email/password (creates user if needed for demo)
     */
    async login(email: string, password: string): Promise<{ user: User; apiKey: string }> {
        // For demo, use onboard endpoint which creates user + API key
        const response = await api.post('/auth/onboard', null, {
            params: { email, name: email.split('@')[0] }
        });

        const { user, api_key } = response.data;

        // Store auth data
        localStorage.setItem('pulse_api_key', api_key);
        localStorage.setItem('pulse_user_id', user.id.toString());
        localStorage.setItem('pulse_user', JSON.stringify(user));

        return { user, apiKey: api_key };
    },

    /**
     * Sign up new user
     */
    async signup(email: string, name: string, password: string): Promise<{ user: User; apiKey: string }> {
        const response = await api.post('/auth/onboard', null, {
            params: { email, name }
        });

        const { user, api_key } = response.data;

        localStorage.setItem('pulse_api_key', api_key);
        localStorage.setItem('pulse_user_id', user.id.toString());
        localStorage.setItem('pulse_user', JSON.stringify(user));

        return { user, apiKey: api_key };
    },

    /**
     * Logout user
     */
    logout(): void {
        localStorage.removeItem('pulse_api_key');
        localStorage.removeItem('pulse_user_id');
        localStorage.removeItem('pulse_user');
    },

    /**
     * Get current user from local storage
     */
    getCurrentUser(): User | null {
        const userStr = localStorage.getItem('pulse_user');
        return userStr ? JSON.parse(userStr) : null;
    },

    /**
     * Get current user ID
     */
    getUserId(): number | null {
        const id = localStorage.getItem('pulse_user_id');
        return id ? parseInt(id, 10) : null;
    },

    /**
     * Check if user is authenticated
     */
    isAuthenticated(): boolean {
        return !!localStorage.getItem('pulse_api_key');
    },

    /**
     * Validate current API key
     */
    async validateSession(): Promise<boolean> {
        try {
            const apiKey = localStorage.getItem('pulse_api_key');
            if (!apiKey) return false;

            const response = await api.get('/auth/validate', {
                headers: { 'X-API-Key': apiKey }
            });
            return response.data.valid;
        } catch {
            return false;
        }
    }
};

// ============================================
// Dashboard Service
// ============================================

export const dashboardService = {
    /**
     * Get complete dashboard summary
     */
    async getSummary(userId: number): Promise<DashboardSummary> {
        const response = await api.get(`/dashboard/summary/${userId}`);
        return response.data;
    },

    /**
     * Get health data trends
     */
    async getTrends(userId: number, days: number = 60): Promise<{
        trends: TrendData[];
        baselines: Record<string, number | null>;
    }> {
        const response = await api.get(`/dashboard/trends/${userId}`, {
            params: { days }
        });
        return response.data;
    },

    /**
     * Get CareScore history
     */
    async getCareScoreHistory(userId: number, days: number = 30): Promise<{
        history: Array<{
            id: number;
            timestamp: string;
            date: string;
            score: number;
            status: string;
            components: Record<string, number>;
            drift_score: number;
            confidence: number;
        }>;
    }> {
        const response = await api.get(`/dashboard/carescore-history/${userId}`, {
            params: { days }
        });
        return response.data;
    },

    /**
     * Get AI-generated insights
     */
    async getInsights(userId: number): Promise<{
        insights: Insight[];
        updated_at: string;
    }> {
        const response = await api.get(`/dashboard/insights/${userId}`);
        return response.data;
    },

    /**
     * Get user escalations
     */
    async getEscalations(userId: number, includeAcknowledged: boolean = false): Promise<{
        active_count: number;
        escalations: Escalation[];
    }> {
        const response = await api.get(`/dashboard/escalations/${userId}`, {
            params: { include_acknowledged: includeAcknowledged }
        });
        return response.data;
    },

    /**
     * Acknowledge an escalation
     */
    async acknowledgeEscalation(escalationId: number, action: string = 'dismissed'): Promise<void> {
        await api.post(`/dashboard/escalations/${escalationId}/acknowledge`, null, {
            params: { action }
        });
    }
};

// ============================================
// Health Data Service
// ============================================

export const healthService = {
    /**
     * Submit manual health entry
     */
    async submitManualEntry(data: {
        bp_systolic?: number;
        bp_diastolic?: number;
        blood_sugar?: number;
        symptoms?: string[];
    }): Promise<{ success: boolean; message: string }> {
        const userId = authService.getUserId();
        if (!userId) throw new Error('Not authenticated');

        // Use webhook endpoint for manual entry
        const payload = {
            dataType: 'ManualEntry',
            records: [{
                time: new Date().toISOString(),
                bp_systolic: data.bp_systolic,
                bp_diastolic: data.bp_diastolic,
                blood_sugar: data.blood_sugar,
                symptoms: data.symptoms?.join(',') || ''
            }]
        };

        const response = await api.post('/webhook/ingest-and-analyze', payload);
        return { success: true, message: 'Data logged successfully' };
    }
};

// ============================================
// Google OAuth & Drive Service
// ============================================

export const driveService = {
    /**
     * Get Google OAuth authorization URL
     */
    async getAuthUrl(redirectUrl?: string): Promise<{
        authorization_url: string;
        state: string;
    }> {
        const userId = authService.getUserId();
        const response = await api.get('/oauth/google/authorize-url', {
            params: { user_id: userId, redirect_url: redirectUrl }
        });
        return response.data;
    },

    /**
     * Check OAuth status for user
     */
    async checkOAuthStatus(userId: number): Promise<{
        has_valid_oauth: boolean;
        drive_sync_available: boolean;
    }> {
        const response = await api.get(`/oauth/google/status/${userId}`);
        return response.data;
    },

    /**
     * Revoke Google OAuth access
     */
    async revokeAccess(userId: number): Promise<void> {
        await api.delete(`/oauth/google/revoke/${userId}`);
    },

    /**
     * List files in Google Drive
     */
    async listFiles(userId: number, search?: string): Promise<DriveFile[]> {
        const response = await api.get(`/oauth/drive/files/${userId}`, {
            params: { search }
        });
        return response.data.files;
    },

    /**
     * Find health export files
     */
    async findHealthExports(userId: number): Promise<DriveFile[]> {
        const response = await api.get(`/oauth/drive/health-exports/${userId}`);
        return response.data.exports;
    },

    /**
     * Trigger full Drive sync
     */
    async syncFromDrive(userId: number): Promise<{
        job_id: number;
        status: string;
        files_found: number;
        files_processed: number;
        records_imported: number;
        details: Array<{
            status: string;
            file_id: string;
            file_name: string;
            records_saved: number;
            errors?: string[];
        }>;
    }> {
        const response = await api.post('/oauth/drive/sync', { user_id: userId });
        return response.data;
    },

    /**
     * Get ingestion job history
     */
    async getIngestionJobs(userId: number, limit: number = 10): Promise<IngestionJob[]> {
        const response = await api.get(`/oauth/drive/ingestion-jobs/${userId}`, {
            params: { limit }
        });
        return response.data.jobs;
    },

    /**
     * Get processed files list
     */
    async getProcessedFiles(userId: number, limit: number = 20): Promise<Array<{
        id: number;
        drive_file_id: string;
        file_name: string;
        file_size: number;
        status: string;
        records_imported: number;
        processed_at: string;
    }>> {
        const response = await api.get(`/oauth/drive/processed-files/${userId}`, {
            params: { limit }
        });
        return response.data.files;
    },

    /**
     * Debug: List all files in Drive to see what's available
     */
    async debugDriveFiles(userId: number): Promise<{
        total_files: number;
        zip_files: Array<{ id: string; name: string; mimeType: string; size?: number }>;
        zip_count: number;
        health_search_results: Array<{ id: string; name: string; mimeType: string }>;
        all_files_sample: Array<{ id: string; name: string; mimeType: string }>;
        error?: string;
        fix?: string;
        possible_causes?: string[];
        diagnosis?: string;
        detail?: any;
        token_info?: {
            has_access_token: boolean;
            has_refresh_token: boolean;
            expires_at: string | null;
            scopes: string[];
        };
    }> {
        const response = await api.get(`/oauth/drive/debug/${userId}`);
        return response.data;
    }
};

// ============================================
// Analysis Service
// ============================================

export const analysisService = {
    /**
     * Trigger analysis pipeline
     */
    async triggerAnalysis(userId: number): Promise<{
        care_score: number;
        status: string;
        explanation: string;
    }> {
        const response = await api.post(`/analysis/trigger/${userId}`);
        return response.data;
    },

    /**
     * Get latest analysis results
     */
    async getAnalysis(userId: number): Promise<{
        care_score: CareScoreData;
        drift_details: {
            detected: boolean;
            severity: string;
            affected_metrics: string[];
        };
    }> {
        const response = await api.get(`/analysis/latest/${userId}`);
        return response.data;
    }
};

// ============================================
// Demo Data Service
// ============================================

export const demoService = {
    /**
     * Generate demo data for testing
     */
    async generateDemoData(): Promise<{ success: boolean; message: string }> {
        const response = await api.post('/demo/generate');
        return response.data;
    },

    /**
     * Compute scores for demo user
     */
    async computeDemoScores(): Promise<{
        care_score: number;
        status: string;
        explanation: string;
    }> {
        const response = await api.post('/demo/compute-scores');
        return response.data;
    }
};

// Export the axios instance for custom requests
export { api };
