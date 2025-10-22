import { useState, useEffect } from 'react';
import { ExclamationTriangleIcon, TrashIcon } from '@heroicons/react/24/outline';

interface ErrorEntry {
    id: number;
    timestamp: string;
    source: string;
    errorType: string;
    message: string;
    details?: string;
}

export default function ErrorsView() {
    const [errors, setErrors] = useState<ErrorEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchErrors = async () => {
        try {
            const response = await fetch('http://localhost:8080/api/errors');
            if (!response.ok) throw new Error('Failed to fetch errors');
            const data = await response.json();
            setErrors(data || []);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    const clearErrors = async () => {
        if (!confirm('Clear all errors from the database?')) return;
        
        try {
            const response = await fetch('http://localhost:8080/api/errors', {
                method: 'DELETE'
            });
            if (!response.ok) throw new Error('Failed to clear errors');
            const result = await response.json();
            alert(`Cleared ${result.deleted} errors`);
            fetchErrors();
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Failed to clear errors');
        }
    };

    useEffect(() => {
        fetchErrors();
        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchErrors, 30000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-gray-500">Loading errors...</div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <ExclamationTriangleIcon className="w-6 h-6 text-red-500" />
                    <h2 className="text-2xl font-bold text-gray-900">System Errors</h2>
                    <span className="text-sm text-gray-500">
                        ({errors.length} {errors.length === 1 ? 'error' : 'errors'})
                    </span>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={fetchErrors}
                        className="px-4 py-2 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition"
                    >
                        Refresh
                    </button>
                    {errors.length > 0 && (
                        <button
                            onClick={clearErrors}
                            className="px-4 py-2 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition flex items-center gap-2"
                        >
                            <TrashIcon className="w-4 h-4" />
                            Clear All
                        </button>
                    )}
                </div>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                    {error}
                </div>
            )}

            {errors.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                    <ExclamationTriangleIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                    <p className="text-lg">No errors found</p>
                    <p className="text-sm">System is running smoothly!</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {errors.map((err) => (
                        <div
                            key={err.id}
                            className="border border-red-200 bg-red-50 rounded-lg p-4 hover:shadow-md transition"
                        >
                            <div className="flex items-start justify-between mb-2">
                                <div className="flex items-center gap-2">
                                    <span className="px-2 py-1 text-xs font-semibold bg-red-600 text-white rounded">
                                        {err.errorType}
                                    </span>
                                    <span className="text-sm font-medium text-gray-700">
                                        {err.source}
                                    </span>
                                </div>
                                <span className="text-xs text-gray-500">
                                    {new Date(err.timestamp).toLocaleString()}
                                </span>
                            </div>
                            <p className="text-sm text-gray-800 mb-2">{err.message}</p>
                            {err.details && (
                                <details className="text-xs text-gray-600">
                                    <summary className="cursor-pointer hover:text-gray-800">
                                        Details
                                    </summary>
                                    <pre className="mt-2 p-2 bg-white rounded border border-gray-200 overflow-x-auto">
                                        {err.details}
                                    </pre>
                                </details>
                            )}
                        </div>
                    ))}
                </div>
            )}

            <div className="mt-4 text-xs text-gray-500 text-center">
                Auto-refreshes every 30 seconds
            </div>
        </div>
    );
}
