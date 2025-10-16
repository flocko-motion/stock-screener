import { useState, useEffect } from 'react';
import type { SymbolProfile } from '../services/api';

interface SymbolDetailProps {
    symbol: string;
    analysisId?: string; // If provided, use analysis-specific chart endpoints
    onClose?: () => void; // If provided, ESC will trigger close
}

export default function SymbolDetail({ symbol, analysisId, onClose }: SymbolDetailProps) {
    const [profile, setProfile] = useState<SymbolProfile | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchProfile = async () => {
            setLoading(true);
            setError(null);
            try {
                const url = analysisId
                    ? `http://localhost:8080/api/analysis/${analysisId}/profile/${symbol}`
                    : `http://localhost:8080/api/symbol/${symbol}`;

                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error('Failed to fetch symbol profile');
                }
                const profileData = await response.json();
                setProfile(profileData);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load profile');
            } finally {
                setLoading(false);
            }
        };

        fetchProfile();
    }, [symbol, analysisId]);

    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape' && onClose) {
                onClose();
            } else if (event.key.toLowerCase() === 't') {
                const tradingViewUrl = `https://www.tradingview.com/chart/?symbol=${symbol}`;
                window.open(tradingViewUrl, '_blank', 'noopener,noreferrer');
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => {
            document.removeEventListener('keydown', handleKeyDown);
        };
    }, [symbol, onClose]);

    const chartUrl = analysisId
        ? `http://localhost:8080/api/analysis/${analysisId}/chart/${symbol}`
        : `http://localhost:8080/api/symbol/${symbol}/chart`;

    const histogramUrl = analysisId
        ? `http://localhost:8080/api/analysis/${analysisId}/histogram/${symbol}`
        : `http://localhost:8080/api/symbol/${symbol}/histogram`;

    return (
        <>
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-2xl font-semibold">{symbol}</h2>
                    {profile?.name && (
                        <p className="text-lg text-gray-600 mt-1">{profile.name}</p>
                    )}
                </div>
                <div className="flex items-center gap-4">
                    <a
                        href={`https://www.tradingview.com/chart/?symbol=${symbol}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-4 py-2 text-gray-500 hover:text-gray-700 border rounded"
                    >
                        [T]radingView
                    </a>
                    {onClose && (
                        <button
                            onClick={onClose}
                            className="px-4 py-2 text-gray-500 hover:text-gray-700 border rounded"
                        >
                            [ESC] to close
                        </button>
                    )}
                </div>
            </div>

            {/* Charts */}
            <div className="mb-8">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div>
                        <img
                            src={chartUrl}
                            alt={`Chart for ${symbol}`}
                            className="w-full h-[50vh] object-contain border border-gray-200 rounded"
                        />
                    </div>
                    <div>
                        <img
                            src={histogramUrl}
                            alt={`Histogram for ${symbol}`}
                            className="w-full h-[50vh] object-contain border border-gray-200 rounded"
                        />
                    </div>
                </div>
            </div>

            {/* Profile Information */}
            {loading ? (
                <div className="text-center py-8">
                    <p className="text-gray-500">Loading profile...</p>
                </div>
            ) : error ? (
                <div className="text-center py-8">
                    <p className="text-red-600">Error: {error}</p>
                </div>
            ) : profile ? (
                <div className="p-6 bg-gray-50 rounded-lg">
                    <h3 className="text-lg font-semibold mb-4">Company Information</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
                        <div>
                            <span className="font-medium text-gray-600">Sector:</span>
                            <span className="ml-2">{profile.sector || 'N/A'}</span>
                        </div>
                        <div>
                            <span className="font-medium text-gray-600">Industry:</span>
                            <span className="ml-2">{profile.industry || 'N/A'}</span>
                        </div>
                        <div>
                            <span className="font-medium text-gray-600">Country:</span>
                            <span className="ml-2">{profile.country || 'N/A'}</span>
                        </div>
                        <div>
                            <span className="font-medium text-gray-600">Exchange:</span>
                            <span className="ml-2">{profile.exchange || 'N/A'}</span>
                        </div>
                        <div>
                            <span className="font-medium text-gray-600">Currency:</span>
                            <span className="ml-2">{profile.currency || 'N/A'}</span>
                        </div>
                        <div>
                            <span className="font-medium text-gray-600">Market Cap:</span>
                            <span className="ml-2">{profile.marketCap ? `$${(profile.marketCap / 1000000000).toFixed(1)}B` : 'N/A'}</span>
                        </div>
                        <div>
                            <span className="font-medium text-gray-600">Founded:</span>
                            <span className="ml-2">{profile.inception ? new Date(profile.inception).getFullYear() : 'N/A'}</span>
                        </div>
                        <div>
                            <span className="font-medium text-gray-600">Price:</span>
                            <span className="ml-2">{profile.oldestPrice ? new Date(profile.oldestPrice).getFullYear() : 'N/A'}</span>
                        </div>
                        <div className="md:col-span-2 lg:col-span-3">
                            <span className="font-medium text-gray-600">Website:</span>
                            {profile.website ? (
                                <a href={profile.website} target="_blank" rel="noopener noreferrer" className="ml-2 text-blue-600 hover:underline">
                                    {String(profile.website).replace('https://', '').replace('http://', '').replace('www.', '')}
                                </a>
                            ) : (
                                <span className="ml-2">N/A</span>
                            )}
                        </div>
                    </div>
                    {profile.description && (
                        <div className="mt-4">
                            <span className="font-medium text-gray-600">Description:</span>
                            <p className="mt-2 text-gray-700">{profile.description}</p>
                        </div>
                    )}
                </div>
            ) : null}
        </>
    );
}
