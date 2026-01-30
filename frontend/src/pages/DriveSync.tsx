/**
 * Drive Sync Page
 * Connect Google Drive and sync health data from Google Fit exports
 */

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import {
    CloudDownload,
    CheckCircle2,
    XCircle,
    RefreshCw,
    FileArchive,
    Clock,
    HardDrive,
    Unlink,
    ExternalLink,
    Loader2,
    Database,
    Bug,
    ChevronDown,
    ChevronUp
} from 'lucide-react';
import { driveService, authService, IngestionJob } from '../lib/api';
import { clsx } from 'clsx';

export const DriveSync = () => {
    const [isConnected, setIsConnected] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [isSyncing, setIsSyncing] = useState(false);
    const [syncResult, setSyncResult] = useState<{
        status: string;
        files_found: number;
        files_processed: number;
        records_imported: number;
    } | null>(null);
    const [ingestionJobs, setIngestionJobs] = useState<IngestionJob[]>([]);
    const [processedFiles, setProcessedFiles] = useState<Array<{
        id: number;
        file_name: string;
        records_imported: number;
        processed_at: string;
        status: string;
    }>>([]);
    const [error, setError] = useState<string | null>(null);

    // Debug state
    const [showDebug, setShowDebug] = useState(false);
    const [debugLoading, setDebugLoading] = useState(false);
    const [debugData, setDebugData] = useState<{
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
    } | null>(null);

    const userId = authService.getUserId();

    // Check OAuth status on mount
    useEffect(() => {
        if (userId) {
            checkOAuthStatus();
            loadSyncHistory();
        }
    }, [userId]);

    // Handle OAuth callback
    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const oauthStatus = params.get('oauth');

        if (oauthStatus === 'success') {
            // Store credentials from OAuth callback
            const newUserId = params.get('user_id');
            const newApiKey = params.get('api_key');

            if (newUserId && newApiKey) {
                // Update auth context with new credentials
                localStorage.setItem('pulse_user_id', newUserId);
                localStorage.setItem('pulse_api_key', newApiKey);
                console.log(`OAuth successful! User ID: ${newUserId}`);
            }

            setIsConnected(true);
            // Clean URL
            window.history.replaceState({}, '', '/sync');

            // Reload status with new credentials
            loadSyncHistory();
        } else if (oauthStatus === 'error') {
            setError(params.get('message') || 'OAuth failed');
            window.history.replaceState({}, '', '/sync');
        }
    }, []);

    const checkOAuthStatus = async () => {
        if (!userId) return;

        try {
            setIsLoading(true);
            const status = await driveService.checkOAuthStatus(userId);
            setIsConnected(status.has_valid_oauth);
        } catch (err) {
            console.error('Failed to check OAuth status:', err);
        } finally {
            setIsLoading(false);
        }
    };

    const loadSyncHistory = async () => {
        if (!userId) return;

        try {
            const [jobs, files] = await Promise.all([
                driveService.getIngestionJobs(userId, 5),
                driveService.getProcessedFiles(userId, 10)
            ]);
            setIngestionJobs(jobs);
            setProcessedFiles(files);
        } catch (err) {
            console.error('Failed to load sync history:', err);
        }
    };

    const handleConnectDrive = async () => {
        try {
            const redirectUrl = `${window.location.origin}/sync`;
            const { authorization_url } = await driveService.getAuthUrl(redirectUrl);
            window.location.href = authorization_url;
        } catch (err) {
            setError('Failed to initiate Google OAuth');
        }
    };

    const handleDisconnect = async () => {
        if (!userId) return;

        try {
            await driveService.revokeAccess(userId);
            setIsConnected(false);
            setSyncResult(null);
        } catch (err) {
            setError('Failed to disconnect Google Drive');
        }
    };

    const handleSync = async () => {
        if (!userId) return;

        try {
            setIsSyncing(true);
            setError(null);
            setSyncResult(null);

            const result = await driveService.syncFromDrive(userId);

            setSyncResult({
                status: result.status,
                files_found: result.files_found,
                files_processed: result.files_processed,
                records_imported: result.records_imported
            });

            // Reload history
            await loadSyncHistory();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Sync failed');
        } finally {
            setIsSyncing(false);
        }
    };

    const handleDebug = async () => {
        if (!userId) return;

        try {
            setDebugLoading(true);
            const data = await driveService.debugDriveFiles(userId);
            setDebugData(data);
        } catch (err: any) {
            console.error('Debug failed:', err);
            setDebugData({
                error: err.response?.data?.detail || 'Failed to fetch Drive files',
                total_files: 0,
                zip_files: [],
                zip_count: 0,
                health_search_results: [],
                all_files_sample: []
            });
        } finally {
            setDebugLoading(false);
        }
    };

    const formatSize = (bytes?: number) => {
        if (!bytes) return 'Unknown';
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <div>
                <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Google Drive Sync</h1>
                <p className="text-gray-500 mt-1">
                    Import your health data from Google Fit exports stored in Drive.
                </p>
            </div>

            {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
                    <XCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                    <p className="text-red-700">{error}</p>
                    <button
                        onClick={() => setError(null)}
                        className="ml-auto text-red-500 hover:text-red-700"
                    >
                        ×
                    </button>
                </div>
            )}

            {/* Connection Status Card */}
            <Card className={clsx(
                "border-l-4",
                isConnected ? "border-l-emerald-500" : "border-l-amber-500"
            )}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className={clsx(
                            "w-12 h-12 rounded-full flex items-center justify-center",
                            isConnected ? "bg-emerald-100" : "bg-gray-100"
                        )}>
                            <HardDrive className={clsx(
                                "w-6 h-6",
                                isConnected ? "text-emerald-600" : "text-gray-400"
                            )} />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900">
                                {isConnected ? 'Google Drive Connected' : 'Connect Google Drive'}
                            </h3>
                            <p className="text-sm text-gray-500">
                                {isConnected
                                    ? 'Your Google Drive is linked. You can sync health data from Google Fit exports.'
                                    : 'Link your Google Drive to import health data from exported files.'
                                }
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        {isConnected ? (
                            <>
                                <Button
                                    variant="outline"
                                    onClick={handleDisconnect}
                                    className="gap-2"
                                >
                                    <Unlink className="w-4 h-4" /> Disconnect
                                </Button>
                                <Button
                                    onClick={handleSync}
                                    disabled={isSyncing}
                                    className="gap-2"
                                >
                                    {isSyncing ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" /> Syncing...
                                        </>
                                    ) : (
                                        <>
                                            <RefreshCw className="w-4 h-4" /> Sync Now
                                        </>
                                    )}
                                </Button>
                            </>
                        ) : (
                            <Button onClick={handleConnectDrive} className="gap-2">
                                <CloudDownload className="w-4 h-4" /> Connect Drive
                            </Button>
                        )}
                    </div>
                </div>
            </Card>

            {/* Sync Result */}
            {syncResult && (
                <Card className={clsx(
                    "border",
                    syncResult.status === 'completed' ? "border-emerald-200 bg-emerald-50/50" : "border-red-200 bg-red-50/50"
                )}>
                    <div className="flex items-start gap-4">
                        {syncResult.status === 'completed' ? (
                            <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0" />
                        ) : (
                            <XCircle className="w-6 h-6 text-red-600 flex-shrink-0" />
                        )}
                        <div className="flex-1">
                            <h4 className={clsx(
                                "font-semibold",
                                syncResult.status === 'completed' ? "text-emerald-800" : "text-red-800"
                            )}>
                                {syncResult.status === 'completed' ? 'Sync Completed Successfully' : 'Sync Failed'}
                            </h4>
                            <div className="mt-2 grid grid-cols-3 gap-4 text-sm">
                                <div>
                                    <span className="text-gray-500">Files Found</span>
                                    <p className="font-semibold text-gray-900">{syncResult.files_found}</p>
                                </div>
                                <div>
                                    <span className="text-gray-500">Files Processed</span>
                                    <p className="font-semibold text-gray-900">{syncResult.files_processed}</p>
                                </div>
                                <div>
                                    <span className="text-gray-500">Records Imported</span>
                                    <p className="font-semibold text-emerald-600">{syncResult.records_imported.toLocaleString()}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </Card>
            )}

            {/* How It Works */}
            {!isConnected && (
                <Card>
                    <CardHeader>
                        <CardTitle>How It Works</CardTitle>
                    </CardHeader>
                    <div className="space-y-4">
                        <div className="flex items-start gap-4">
                            <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-sm font-bold text-gray-600">1</div>
                            <div>
                                <p className="font-medium text-gray-900">Export from Google Fit</p>
                                <p className="text-sm text-gray-500">Open Google Fit → Settings → Export data → Save to Drive</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-4">
                            <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-sm font-bold text-gray-600">2</div>
                            <div>
                                <p className="font-medium text-gray-900">Connect Google Drive</p>
                                <p className="text-sm text-gray-500">Grant Pulse AI read-only access to your Drive</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-4">
                            <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-sm font-bold text-gray-600">3</div>
                            <div>
                                <p className="font-medium text-gray-900">Sync Health Data</p>
                                <p className="text-sm text-gray-500">We'll find and process your health export files automatically</p>
                            </div>
                        </div>
                    </div>
                </Card>
            )}

            {/* Sync History */}
            {ingestionJobs.length > 0 && (
                <Card>
                    <CardHeader className="flex items-center justify-between">
                        <CardTitle>Recent Sync Jobs</CardTitle>
                        <Clock className="w-4 h-4 text-gray-400" />
                    </CardHeader>
                    <div className="space-y-3">
                        {ingestionJobs.map((job) => (
                            <div
                                key={job.id}
                                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                            >
                                <div className="flex items-center gap-3">
                                    <div className={clsx(
                                        "w-2 h-2 rounded-full",
                                        job.status === 'completed' ? "bg-emerald-500" :
                                            job.status === 'failed' ? "bg-red-500" :
                                                job.status === 'processing' ? "bg-amber-500 animate-pulse" :
                                                    "bg-gray-300"
                                    )} />
                                    <div>
                                        <p className="text-sm font-medium text-gray-900">
                                            {job.job_type === 'drive_sync' ? 'Drive Sync' : job.job_type}
                                        </p>
                                        <p className="text-xs text-gray-500">{formatDate(job.started_at)}</p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <p className="text-sm font-medium text-gray-900">
                                        {job.records_imported.toLocaleString()} records
                                    </p>
                                    <p className="text-xs text-gray-500">
                                        {job.files_processed} / {job.files_found} files
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </Card>
            )}

            {/* Processed Files */}
            {processedFiles.length > 0 && (
                <Card>
                    <CardHeader className="flex items-center justify-between">
                        <CardTitle>Processed Files</CardTitle>
                        <FileArchive className="w-4 h-4 text-gray-400" />
                    </CardHeader>
                    <div className="space-y-2">
                        {processedFiles.map((file) => (
                            <div
                                key={file.id}
                                className="flex items-center justify-between p-3 border border-gray-100 rounded-lg hover:bg-gray-50"
                            >
                                <div className="flex items-center gap-3">
                                    <Database className="w-4 h-4 text-gray-400" />
                                    <div>
                                        <p className="text-sm font-medium text-gray-900">{file.file_name}</p>
                                        <p className="text-xs text-gray-500">{formatDate(file.processed_at)}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className="text-sm text-gray-600">
                                        {file.records_imported.toLocaleString()} records
                                    </span>
                                    <span className={clsx(
                                        "px-2 py-0.5 text-xs font-medium rounded-full",
                                        file.status === 'completed' ? "bg-emerald-100 text-emerald-700" :
                                            file.status === 'failed' ? "bg-red-100 text-red-700" :
                                                "bg-gray-100 text-gray-700"
                                    )}>
                                        {file.status}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </Card>
            )}

            {/* Debug Section */}
            {isConnected && (
                <Card className="border-gray-200">
                    <button
                        onClick={() => {
                            setShowDebug(!showDebug);
                            if (!showDebug && !debugData) {
                                handleDebug();
                            }
                        }}
                        className="w-full flex items-center justify-between p-0"
                    >
                        <div className="flex items-center gap-2">
                            <Bug className="w-4 h-4 text-gray-400" />
                            <span className="font-medium text-gray-700">Debug: View All Drive Files</span>
                        </div>
                        {showDebug ? (
                            <ChevronUp className="w-4 h-4 text-gray-400" />
                        ) : (
                            <ChevronDown className="w-4 h-4 text-gray-400" />
                        )}
                    </button>

                    {showDebug && (
                        <div className="mt-4 space-y-4">
                            {debugLoading && (
                                <div className="flex items-center gap-2 text-gray-500">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Loading Drive files...
                                </div>
                            )}

                            {debugData?.error && (
                                <div className="space-y-3">
                                    <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                                        <p className="font-semibold">{debugData.error}</p>
                                        {debugData.diagnosis && (
                                            <p className="mt-2">{debugData.diagnosis}</p>
                                        )}
                                    </div>

                                    {debugData.possible_causes && debugData.possible_causes.length > 0 && (
                                        <div className="p-3 bg-amber-50 rounded-lg text-sm">
                                            <p className="font-semibold text-amber-800 mb-2">Possible Causes:</p>
                                            <ul className="space-y-1 text-amber-700">
                                                {debugData.possible_causes.map((cause, i) => (
                                                    <li key={i}>{cause}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}

                                    {debugData.fix && (
                                        <div className="p-3 bg-blue-50 rounded-lg text-sm">
                                            <p className="font-semibold text-blue-800">How to fix:</p>
                                            <p className="text-blue-700 mt-1">{debugData.fix}</p>
                                            <Button
                                                variant="outline"
                                                onClick={handleDisconnect}
                                                className="mt-3 gap-2"
                                            >
                                                <Unlink className="w-4 h-4" />
                                                Disconnect & Reconnect
                                            </Button>
                                        </div>
                                    )}

                                    {debugData.token_info && (
                                        <div className="p-3 bg-gray-50 rounded-lg text-xs font-mono">
                                            <p className="font-semibold text-gray-700 mb-1">Token Info (Debug):</p>
                                            <p>Has Access Token: {debugData.token_info.has_access_token ? '✓' : '✗'}</p>
                                            <p>Has Refresh Token: {debugData.token_info.has_refresh_token ? '✓' : '✗'}</p>
                                            <p>Expires: {debugData.token_info.expires_at || 'N/A'}</p>
                                            <p>Scopes: {debugData.token_info.scopes?.join(', ') || 'None'}</p>
                                        </div>
                                    )}
                                </div>
                            )}

                            {debugData && !debugData.error && (
                                <div className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div className="p-3 bg-gray-50 rounded-lg">
                                            <p className="text-gray-500">Total Files Visible</p>
                                            <p className="text-xl font-bold text-gray-900">{debugData.total_files}</p>
                                        </div>
                                        <div className="p-3 bg-gray-50 rounded-lg">
                                            <p className="text-gray-500">ZIP Files Found</p>
                                            <p className="text-xl font-bold text-gray-900">{debugData.zip_count}</p>
                                        </div>
                                    </div>

                                    {debugData.zip_files.length > 0 && (
                                        <div>
                                            <h4 className="font-medium text-gray-900 mb-2">ZIP Files in Drive:</h4>
                                            <div className="space-y-2">
                                                {debugData.zip_files.map((file) => (
                                                    <div key={file.id} className="flex items-center justify-between p-2 bg-emerald-50 rounded border border-emerald-200">
                                                        <div className="flex items-center gap-2">
                                                            <FileArchive className="w-4 h-4 text-emerald-600" />
                                                            <span className="font-medium text-emerald-800">{file.name}</span>
                                                        </div>
                                                        <span className="text-xs text-emerald-600">{formatSize(file.size)}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {debugData.health_search_results.length > 0 && (
                                        <div>
                                            <h4 className="font-medium text-gray-900 mb-2">Files matching "Health":</h4>
                                            <div className="space-y-1">
                                                {debugData.health_search_results.map((file) => (
                                                    <div key={file.id} className="text-sm p-2 bg-blue-50 rounded">
                                                        {file.name}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {debugData.all_files_sample.length > 0 && (
                                        <div>
                                            <h4 className="font-medium text-gray-900 mb-2">Recent Files (sample):</h4>
                                            <div className="max-h-48 overflow-y-auto space-y-1">
                                                {debugData.all_files_sample.map((file) => (
                                                    <div key={file.id} className="text-xs p-1.5 bg-gray-50 rounded flex justify-between">
                                                        <span className="truncate">{file.name}</span>
                                                        <span className="text-gray-400 ml-2">{file.mimeType?.split('/').pop()}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    <Button
                                        variant="outline"
                                        onClick={handleDebug}
                                        className="gap-2 text-sm"
                                        disabled={debugLoading}
                                    >
                                        <RefreshCw className={clsx("w-4 h-4", debugLoading && "animate-spin")} />
                                        Refresh Debug Info
                                    </Button>
                                </div>
                            )}
                        </div>
                    )}
                </Card>
            )}

            {/* Privacy Notice */}
            <div className="px-4 py-3 bg-blue-50 border border-blue-100 rounded-lg">
                <p className="text-sm text-blue-800">
                    <strong>Privacy:</strong> Pulse AI only requests read-only access to your Google Drive.
                    We only download and process files matching health export patterns (e.g., "Health Connect.zip").
                    Your data is stored securely and never shared.
                </p>
            </div>
        </div>
    );
};
