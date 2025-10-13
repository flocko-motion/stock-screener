import { ChartBarIcon } from '@heroicons/react/24/outline';
import { useState, useEffect } from 'react';
import { analysisApi } from '../services/api';
import type { AnalysisPackage } from '../services/api';

interface AnalysisViewProps {
    data?: { id: string };
}

export default function AnalysisView({ data }: AnalysisViewProps) {
    const [analysis, setAnalysis] = useState<AnalysisPackage | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        if (!data?.id) {
            setLoading(false);
            return;
        }

        let interval: number | null = null;

        const fetchAnalysis = async () => {
            try {
                console.log('[AnalysisView] Fetching analysis:', data.id);
                const result = await analysisApi.get(data.id);
                console.log('[AnalysisView] Received analysis:', result);
                setAnalysis(result);
                setError('');

                // Stop polling if status is no longer "processing"
                if (result.Status !== 'processing' && interval) {
                    console.log('[AnalysisView] Status is', result.Status, '- stopping poll');
                    clearInterval(interval);
                    interval = null;
                }
            } catch (err) {
                console.error('[AnalysisView] Error fetching analysis:', err);
                setError(err instanceof Error ? err.message : 'Failed to load analysis');
            } finally {
                setLoading(false);
            }
        };

        // Initial fetch
        fetchAnalysis();

        // Set up polling interval (poll every 2 seconds)
        interval = setInterval(() => {
            console.log('[AnalysisView] Polling...');
            fetchAnalysis();
        }, 2000);

        return () => {
            console.log('[AnalysisView] Cleaning up interval');
            if (interval) {
                clearInterval(interval);
            }
        };
    }, [data?.id]);

    if (loading) {
        return (
            <div className="max-w-7xl mx-auto">
                <div className="form-card p-8">
                    <div className="text-center py-12">
                        <ChartBarIcon className="icon-fixed text-gray-300 mx-auto mb-4" />
                        <p className="text-gray-500">Loading analysis...</p>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="max-w-7xl mx-auto">
                <div className="form-card p-8">
                    <div className="text-center py-12">
                        <p className="text-red-600">{error}</p>
                    </div>
                </div>
            </div>
        );
    }

    if (!analysis) {
        return (
            <div className="max-w-7xl mx-auto">
                <div className="form-card p-8">
                    <div className="text-center py-12">
                        <p className="text-gray-500">Analysis not found</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto">
            <div className="form-card p-8">
                <div className="mb-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">{analysis.Name}</h2>
                    <div className="flex gap-4 text-sm text-gray-600">
                        <span>Status: <span className={`font-semibold ${analysis.Status === 'ready' ? 'text-green-600' :
                            analysis.Status === 'processing' ? 'text-blue-600' :
                                'text-red-600'
                            }`}>{analysis.Status}</span></span>
                        <span>Symbols: {analysis.SymbolCount}</span>
                        <span>Interval: {analysis.Interval}</span>
                    </div>
                </div>

                {analysis.Status === 'processing' ? (
                    <div className="text-center py-12">
                        <ChartBarIcon className="icon-fixed text-gray-300 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">Analysis in Progress</h3>
                        <p className="text-gray-500">This analysis is currently being processed. Results will appear here when complete.</p>
                        <p className="text-sm text-gray-400 mt-2">Auto-refreshing every 2 seconds...</p>
                    </div>
                ) : analysis.Status === 'ready' ? (
                    <div className="text-center py-12">
                        <ChartBarIcon className="icon-fixed text-green-600 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">Analysis Complete</h3>
                        <p className="text-gray-500">Results and charts will be displayed here.</p>
                    </div>
                ) : (
                    <div className="text-center py-12">
                        <ChartBarIcon className="icon-fixed text-red-600 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">Analysis Failed</h3>
                        <p className="text-gray-500">There was an error processing this analysis.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
