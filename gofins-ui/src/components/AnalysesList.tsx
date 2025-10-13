import { useState, useEffect } from 'react';
import { BeakerIcon, PlusIcon } from '@heroicons/react/24/outline';
import { analysisApi } from '../services/api';
import type { AnalysisPackage } from '../services/api';

interface AnalysesListProps {
    onOpenAnalysis?: (id: string, name: string) => void;
    onOpenCreate?: () => void;
}

export default function AnalysesList({ onOpenAnalysis, onOpenCreate }: AnalysesListProps) {
    const [analyses, setAnalyses] = useState<AnalysisPackage[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchAnalyses = async () => {
            try {
                setLoading(true);
                const data = await analysisApi.list();
                setAnalyses(data || []); // Handle null response
                setError(null);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load analyses');
            } finally {
                setLoading(false);
            }
        };

        fetchAnalyses();
    }, []);

    if (loading) {
        return (
            <div className="max-w-7xl mx-auto mt-4">
                <div className="text-center py-12">
                    <p className="text-gray-500">Loading analyses...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="max-w-7xl mx-auto mt-4">
                <div className="text-center py-12">
                    <p className="text-red-500">{error}</p>
                    <p className="text-sm text-gray-500 mt-2">Make sure the API server is running on port 8080</p>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto">
            <div className="mb-6 flex items-center justify-between">
                <p className="text-gray-600 text-sm">Browse and manage your stock screening analyses</p>
                <button
                    onClick={onOpenCreate}
                    className="form-button-primary flex items-center gap-2"
                >
                    <PlusIcon className="icon-fixed" style={{ width: '16px', height: '16px' }} />
                    <span>New Analysis</span>
                </button>
            </div>

            {analyses.length === 0 ? (
                <div className="form-card p-12 text-center">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No analyses yet</h3>
                    <p className="text-gray-500 mb-4">Create your first analysis to get started</p>
                </div>
            ) : (
                <div className="form-card">
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Analysis Name
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Status
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Symbols
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Created
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Actions
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {analyses.map((analysis) => (
                                    <tr key={analysis.ID} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                <span className="text-sm font-medium text-gray-900">{analysis.Name}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${analysis.Status === 'ready'
                                                ? 'bg-green-100 text-green-800'
                                                : analysis.Status === 'processing'
                                                    ? 'bg-yellow-100 text-yellow-800'
                                                    : 'bg-red-100 text-red-800'
                                                }`}>
                                                {analysis.Status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {analysis.SymbolCount}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {new Date(analysis.CreatedAt).toLocaleDateString()}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                            <button
                                                onClick={() => onOpenAnalysis?.(analysis.ID, analysis.Name)}
                                                className="text-blue-600 hover:text-blue-900"
                                            >
                                                View
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}
