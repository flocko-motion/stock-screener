import { ChartBarIcon } from '@heroicons/react/24/outline';
import { useState, useEffect } from 'react';
import { analysisApi } from '../services/api';
import type { AnalysisPackage, AnalysisResult } from '../services/api';
import SymbolDetail from './SymbolDetail';

// Utility function to safely format numbers with fallback
const MaybeNumberToFixed = (value: number | null | undefined, decimals: number = 2, fallback: string = 'N/A'): string => {
    if (value == null || value === undefined) {
        return fallback;
    }
    return value.toFixed(decimals);
};

// Calculate composite score: higher mean is better, lower stddev is better
// scoreWeight: 0 = only stddev matters, 1 = only mean matters, 0.5 = equal weight
const calculateScore = (mean: number, stddev: number, scoreWeight: number): number => {
    // Normalize: higher score is better
    // Mean component: higher is better (use as-is)
    // StdDev component: lower is better (invert by using negative)
    const meanComponent = mean * scoreWeight;
    const stddevComponent = -stddev * (1 - scoreWeight);
    return meanComponent + stddevComponent;
};

// Sorting function
const sortResults = (results: AnalysisResult[], field: SortField, direction: SortDirection, scoreWeight: number): AnalysisResult[] => {
    return [...results].sort((a, b) => {
        let aVal: any, bVal: any;

        switch (field) {
            case 'symbol':
                aVal = a.symbol;
                bVal = b.symbol;
                break;
            case 'inception':
                aVal = a.inception ? new Date(a.inception).getTime() : 0;
                bVal = b.inception ? new Date(b.inception).getTime() : 0;
                break;
            case 'mean':
                aVal = a.mean;
                bVal = b.mean;
                break;
            case 'stddev':
                aVal = a.stddev;
                bVal = b.stddev;
                break;
            case 'score':
                aVal = calculateScore(a.mean, a.stddev, scoreWeight);
                bVal = calculateScore(b.mean, b.stddev, scoreWeight);
                break;
            default:
                return 0;
        }

        if (aVal < bVal) return direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return direction === 'asc' ? 1 : -1;
        return 0;
    });
};

// Filtering function
const filterResults = (results: AnalysisResult[], filters: any): AnalysisResult[] => {
    return results.filter(result => {
        // Inception date filter
        if (filters.inceptionFrom && result.inception) {
            const inceptionDate = new Date(result.inception);
            const fromDate = new Date(filters.inceptionFrom);
            if (inceptionDate < fromDate) return false;
        }
        if (filters.inceptionTo && result.inception) {
            const inceptionDate = new Date(result.inception);
            const toDate = new Date(filters.inceptionTo);
            if (inceptionDate > toDate) return false;
        }

        // Mean filter
        if (filters.meanMin && result.mean < parseFloat(filters.meanMin)) return false;
        if (filters.meanMax && result.mean > parseFloat(filters.meanMax)) return false;

        // StdDev filter
        if (filters.stddevMin && result.stddev < parseFloat(filters.stddevMin)) return false;
        if (filters.stddevMax && result.stddev > parseFloat(filters.stddevMax)) return false;

        return true;
    });
};

interface AnalysisViewProps {
    data?: { id: string };
}

type SortField = 'symbol' | 'inception' | 'mean' | 'stddev' | 'score';
type SortDirection = 'asc' | 'desc';

export default function AnalysisView({ data }: AnalysisViewProps) {
    const [analysis, setAnalysis] = useState<AnalysisPackage | null>(null);
    const [results, setResults] = useState<AnalysisResult[]>([]);
    const [filteredResults, setFilteredResults] = useState<AnalysisResult[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [sortField, setSortField] = useState<SortField>('score');
    const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
    const [scoreWeight, setScoreWeight] = useState<number>(0.5); // 0 = only σ, 1 = only μ
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

    // Handle sorting and filtering
    useEffect(() => {
        const filtered = filterResults(results, filters);
        const sorted = sortResults(filtered, sortField, sortDirection, scoreWeight);
        setFilteredResults(sorted);
    }, [results, filters, sortField, sortDirection, scoreWeight]);

    const handleSort = (field: SortField) => {
        if (sortField === field) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortDirection('desc');
        }
    };

    const handleFilterChange = (key: string, value: string) => {
        setFilters(prev => ({ ...prev, [key]: value }));
    };

    const handleRowClick = (symbol: string) => {
        setSelectedSymbol(symbol);
        setShowModal(true);
    };

    const closeModal = () => {
        setShowModal(false);
        setSelectedSymbol(null);
    };

    // Handle keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if (!showModal) return;

            if (event.key === 'Escape') {
                closeModal();
            } else if (event.key.toLowerCase() === 't') {
                // Open TradingView
                const tradingViewUrl = `https://www.tradingview.com/chart/?symbol=${selectedSymbol}`;
                window.open(tradingViewUrl, '_blank', 'noopener,noreferrer');
            }
        };

        if (showModal) {
            document.addEventListener('keydown', handleKeyDown);
            return () => {
                document.removeEventListener('keydown', handleKeyDown);
            };
        }
    }, [showModal, selectedSymbol]);

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
                            <div>
                                {/* Filter Controls */}
                                <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                                    <div className="flex flex-wrap items-center gap-6">
                                        <div className="flex items-center gap-2">
                                            <label className="text-xs font-medium text-gray-600 whitespace-nowrap">Inception:</label>
                                            <input
                                                type="number"
                                                min="1900"
                                                max="2030"
                                                value={filters.inceptionFrom ? new Date(filters.inceptionFrom).getFullYear() : ''}
                                                onChange={(e) => handleFilterChange('inceptionFrom', e.target.value ? `${e.target.value}-01-01` : '')}
                                                className="w-16 px-2 py-1 border border-gray-300 rounded text-xs"
                                                placeholder="year"
                                            />
                                            <span className="text-gray-400">to</span>
                                            <input
                                                type="number"
                                                min="1900"
                                                max="2030"
                                                value={filters.inceptionTo ? new Date(filters.inceptionTo).getFullYear() : ''}
                                                onChange={(e) => handleFilterChange('inceptionTo', e.target.value ? `${e.target.value}-12-31` : '')}
                                                className="w-16 px-2 py-1 border border-gray-300 rounded text-xs"
                                                placeholder="year"
                                            />
                                        </div>

                                        <div className="flex items-center gap-2">
                                            <input
                                                type="number"
                                                step="0.1"
                                                value={filters.meanMin}
                                                onChange={(e) => handleFilterChange('meanMin', e.target.value)}
                                                className="w-20 px-2 py-1 border border-gray-300 rounded text-xs"
                                                placeholder="min"
                                            />
                                            <span className="text-gray-600 text-sm">&le; μ &le;</span>
                                            <input
                                                type="number"
                                                step="0.1"
                                                value={filters.meanMax}
                                                onChange={(e) => handleFilterChange('meanMax', e.target.value)}
                                                className="w-20 px-2 py-1 border border-gray-300 rounded text-xs"
                                                placeholder="max"
                                            />
                                        </div>

                                        <div className="flex items-center gap-2">
                                            <input
                                                type="number"
                                                step="0.1"
                                                value={filters.stddevMin}
                                                onChange={(e) => handleFilterChange('stddevMin', e.target.value)}
                                                className="w-20 px-2 py-1 border border-gray-300 rounded text-xs"
                                                placeholder="min"
                                            />
                                            <span className="text-gray-600 text-sm">&le; σ &le;</span>
                                            <input
                                                type="number"
                                                step="0.1"
                                                value={filters.stddevMax}
                                                onChange={(e) => handleFilterChange('stddevMax', e.target.value)}
                                                className="w-20 px-2 py-1 border border-gray-300 rounded text-xs"
                                                placeholder="max"
                                            />
                                        </div>

                                        <div className="flex items-center gap-3 px-3 py-1 bg-white rounded border border-gray-300">
                                            <label className="text-xs font-medium text-gray-600 whitespace-nowrap">Score:</label>
                                            <span className="text-xs text-gray-500">μ</span>
                                            <input
                                                type="range"
                                                min="0"
                                                max="1"
                                                step="0.01"
                                                value={scoreWeight}
                                                onChange={(e) => setScoreWeight(parseFloat(e.target.value))}
                                                className="w-32 h-1"
                                            />
                                            <span className="text-xs text-gray-500">σ</span>
                                            <span className="text-xs font-mono text-gray-700 w-8 text-center">{(scoreWeight * 100).toFixed(0)}%</span>
                                        </div>

                                        <div className="text-xs text-gray-600 ml-auto">
                                            {filteredResults.length} of {results.length} symbols
                                        </div>
                                    </div>
                                </div>

                                <div className="overflow-x-auto">
                                    <table className="min-w-full divide-y divide-gray-200">
                                        <thead className="bg-gray-50">
                                            <tr>
                                                <th
                                                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                                    onClick={() => handleSort('symbol')}
                                                >
                                                    Symbol {sortField === 'symbol' && (sortDirection === 'asc' ? '↑' : '↓')}
                                                </th>
                                                <th
                                                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                                    onClick={() => handleSort('inception')}
                                                >
                                                    Inception {sortField === 'inception' && (sortDirection === 'asc' ? '↑' : '↓')}
                                                </th>
                                                <th
                                                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 lowercase tracking-wider cursor-pointer hover:bg-gray-100"
                                                    onClick={() => handleSort('mean')}
                                                >
                                                    μ {sortField === 'mean' && (sortDirection === 'asc' ? '↑' : '↓')}
                                                </th>
                                                <th
                                                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 lowercase tracking-wider cursor-pointer hover:bg-gray-100"
                                                    onClick={() => handleSort('stddev')}
                                                >
                                                    σ {sortField === 'stddev' && (sortDirection === 'asc' ? '↑' : '↓')}
                                                </th>
                                                <th
                                                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                                    onClick={() => handleSort('score')}
                                                >
                                                    Score {sortField === 'score' && (sortDirection === 'asc' ? '↑' : '↓')}
                                                </th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 lowercase tracking-wider">min(μ)</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 lowercase tracking-wider">max(μ)</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Chart</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Histogram</th>
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y divide-gray-200">
                                            {filteredResults.map((result, index) => (
                                                <tr
                                                    key={`${result.symbol}-${index}`}
                                                    className={`${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'} cursor-pointer hover:bg-blue-50`}
                                                    onClick={() => handleRowClick(result.symbol)}
                                                >
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
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-blue-600">
                                                        {MaybeNumberToFixed(calculateScore(result.mean, result.stddev, scoreWeight), 2)}
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

            {/* Modal */}
            {showModal && selectedSymbol && (
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
                    onClick={closeModal}
                >
                    <div
                        className="bg-white rounded-lg p-6 w-full max-w-[95vw] h-[95vh] overflow-y-auto"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <SymbolDetail 
                            symbol={selectedSymbol} 
                            analysisId={data?.id}
                            onClose={closeModal}
                        />
                    </div>
                </div>
            )}
        </div>
    );
}
