import { useState, useEffect } from 'react';
import { analysisApi } from '../services/api';
import type { AnalysisPackage } from '../services/api';

interface AnalysesListProps {
    onOpenAnalysis?: (id: string, name: string) => void;
    onOpenCreate?: () => void;
}

// Track if we're currently fetching to prevent duplicates
let isFetching = false;

export default function AnalysesList({ onOpenAnalysis, onOpenCreate }: AnalysesListProps) {
    const [analyses, setAnalyses] = useState<AnalysisPackage[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [renamingId, setRenamingId] = useState<string | null>(null);
    const [newName, setNewName] = useState('');

    const fetchAnalyses = async () => {
        if (isFetching) return;
        
        try {
            isFetching = true;
            setLoading(true);
            const data = await analysisApi.list();
            setAnalyses(data || []); // Handle null response
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load analyses');
        } finally {
            setLoading(false);
            isFetching = false;
        }
    };

    useEffect(() => {
        fetchAnalyses();
    }, []);

    const handleDelete = async (id: string, name: string) => {
        if (!window.confirm(`Are you sure you want to delete the analysis "${name}"?`)) {
            return;
        }

        try {
            await analysisApi.delete(id);
            // Refresh the list after deletion
            await fetchAnalyses();
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Failed to delete analysis');
        }
    };

    const handleRenameClick = (id: string, currentName: string) => {
        setRenamingId(id);
        setNewName(currentName);
    };

    const handleRenameSubmit = async () => {
        if (!renamingId || !newName.trim()) {
            return;
        }

        try {
            await analysisApi.update(renamingId, newName.trim());
            setRenamingId(null);
            setNewName('');
            // Refresh the list after rename
            await fetchAnalyses();
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Failed to rename analysis');
        }
    };

    const handleRenameCancel = () => {
        setRenamingId(null);
        setNewName('');
    };

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
                    className="px-4 py-2 text-sm border border-gray-300 rounded bg-white hover:bg-gray-50 flex items-center gap-2"
                >
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
                                                className="px-3 py-1 text-xs border border-gray-300 rounded bg-white hover:bg-gray-50 mr-2"
                                            >
                                                View
                                            </button>
                                            <button
                                                onClick={() => handleRenameClick(analysis.ID, analysis.Name)}
                                                className="px-3 py-1 text-xs border border-gray-300 rounded bg-white hover:bg-gray-50 mr-2"
                                            >
                                                Rename
                                            </button>
                                            <button
                                                onClick={() => handleDelete(analysis.ID, analysis.Name)}
                                                className="px-3 py-1 text-xs border border-gray-300 rounded bg-white hover:bg-gray-50 text-red-600"
                                            >
                                                Delete
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Rename Dialog */}
            {renamingId && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
                        <h3 className="text-lg font-medium text-gray-900 mb-4">Rename Analysis</h3>
                        <input
                            type="text"
                            value={newName}
                            onChange={(e) => setNewName(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                    handleRenameSubmit();
                                } else if (e.key === 'Escape') {
                                    handleRenameCancel();
                                }
                            }}
                            className="form-input w-full mb-4"
                            placeholder="Enter new name"
                            autoFocus
                        />
                        <div className="flex justify-end gap-2">
                            <button
                                onClick={handleRenameCancel}
                                className="px-4 py-2 text-sm border border-gray-300 rounded bg-white hover:bg-gray-50"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleRenameSubmit}
                                className="px-4 py-2 text-sm border border-gray-300 rounded bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                disabled={!newName.trim()}
                            >
                                Rename
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
