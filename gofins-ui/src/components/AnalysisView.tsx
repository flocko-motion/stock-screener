import { ChartBarIcon } from '@heroicons/react/24/outline';
import { useState, useEffect } from 'react';
import { analysisApi } from '../services/api';
import type { AnalysisPackage, AnalysisResult } from '../services/api';

// Utility function to safely format numbers with fallback
const MaybeNumberToFixed = (value: number | null | undefined, decimals: number = 2, fallback: string = 'N/A'): string => {
    if (value == null || value === undefined) {
        return fallback;
    }
    return value.toFixed(decimals);
};

interface AnalysisViewProps {
    data?: { id: string };
}

type SortField = 'symbol' | 'inception' | 'mean' | 'stddev';
type SortDirection = 'asc' | 'desc';

export default function AnalysisView({ data }: AnalysisViewProps) {
    const [analysis, setAnalysis] = useState<AnalysisPackage | null>(null);
    const [results, setResults] = useState<AnalysisResult[]>([]);
    const [filteredResults, setFilteredResults] = useState<AnalysisResult[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [sortField, setSortField] = useState<SortField>('mean');
    const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
    const [filters, setFilters] = useState({
        inceptionFrom: '',
        inceptionTo: '',
        meanMin: '',
        meanMax: '',
        stddevMin: '',
        stddevMax: ''
    });
    const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
    const [showModal, setShowModal] = useState(false);

    useEffect(() => {
        if (!data?.id) {
            setLoading(false);
            return;
        }

        let interval: number | null = null;

        const fetchResults = async () => {
            try {
                console.log('[AnalysisView] Fetching results for:', data.id);
                const results = await analysisApi.getResults(data.id);
                console.log('[AnalysisView] Received results:', results);
                if (results.length > 0) {
                    console.log('[AnalysisView] First result structure:', results[0]);
                    console.log('[AnalysisView] All symbols:', results.map(r => r.symbol));
                    console.log('[AnalysisView] Unique symbols:', [...new Set(results.map(r => r.symbol))]);
                }
                setResults(results);
                setFilteredResults(results);
            } catch (err) {
                console.error('[AnalysisView] Error fetching results:', err);
                setError(err instanceof Error ? err.message : 'Failed to load results');
            }
        }

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
                    if (result.Status === 'ready') {
                        fetchResults();
                    }
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
                        <span>Status:<br /><span className={`font-semibold ${analysis.Status === 'ready' ? 'text-green-600' :
                            analysis.Status === 'processing' ? 'text-blue-600' :
                                'text-red-600'
                            }`}>{analysis.Status}</span></span>
                        <span>Symbols:<br />{analysis.SymbolCount}</span>
                        <span>Market Cap Min:<br />{analysis.McapMin}</span>
                        <span>Inception Max:<br />{analysis.InceptionMax?.substring(0, 10)}</span>
                        <span>Time From/To:<br />{analysis.TimeFrom.substring(0, 10)} to {analysis.TimeTo.substring(0, 10)}</span>
                        <span>Interval:<br />{analysis.Interval}</span>
                        <span>Hist Min/Max/Bins:<br />{analysis.HistMin}/{analysis.HistMax}/{analysis.HistBins}</span>
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
                    <div>
                        {results.length > 0 ? (
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Inception</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 lowercase tracking-wider">μ</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 lowercase tracking-wider">σ</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 lowercase tracking-wider">min(μ)</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 lowercase tracking-wider">max(μ)</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Chart</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Histogram</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-200">
                                        {results.map((result, index) => (
                                            <tr key={`${result.symbol}-${index}`} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                    {result.symbol}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                    {result.inception ? new Date(result.inception).toLocaleDateString() : 'N/A'}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                    {MaybeNumberToFixed(result.mean)}%
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                    {MaybeNumberToFixed(result.stddev)}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                    {MaybeNumberToFixed(result.min)}%
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                    {MaybeNumberToFixed(result.max)}%
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                    <img
                                                        src={`http://localhost:8080/api/analysis/${data?.id}/chart/${result.symbol}`}
                                                        alt={`Chart for ${result.symbol}`}
                                                        className="w-24 h-16 object-contain border border-gray-200 rounded"
                                                        onError={(e) => {
                                                            e.currentTarget.style.display = 'none';
                                                        }}
                                                    />
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                    <img
                                                        src={`http://localhost:8080/api/analysis/${data?.id}/histogram/${result.symbol}`}
                                                        alt={`Histogram for ${result.symbol}`}
                                                        className="w-24 h-16 object-contain border border-gray-200 rounded"
                                                        onError={(e) => {
                                                            e.currentTarget.style.display = 'none';
                                                        }}
                                                    />
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="text-center py-12">
                                <p className="text-gray-500">No results found for this analysis.</p>
                            </div>
                        )}
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
