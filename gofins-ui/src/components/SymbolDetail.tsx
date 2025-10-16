import { useState, useEffect } from 'react';
import type { SymbolProfile } from '../services/api';

interface SymbolDetailProps {
    symbol: string;
    analysisId?: string; // If provided, use analysis-specific chart endpoints
    onClose?: () => void; // If provided, ESC will trigger close
}

interface UserRating {
    id: number;
    ticker: string;
    rating: number;
    notes?: string;
    createdAt: string;
}

export default function SymbolDetail({ symbol, analysisId, onClose }: SymbolDetailProps) {
    const [profile, setProfile] = useState<SymbolProfile | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [rating, setRating] = useState<number | null>(null);
    const [notes, setNotes] = useState<string>('');
    const [ratingHistory, setRatingHistory] = useState<UserRating[]>([]);
    const [submitting, setSubmitting] = useState(false);

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
        const fetchRatingHistory = async () => {
            try {
                const response = await fetch(`http://localhost:8080/api/ratings/${symbol}/history`);
                if (response.ok) {
                    const data = await response.json();
                    setRatingHistory(data || []);
                }
            } catch (err) {
                console.error('Failed to fetch rating history:', err);
            }
        };
        fetchRatingHistory();
    }, [symbol]);

    const handleDeleteRating = async (ratingId: number) => {
        if (!confirm('Delete this rating?')) return;
        
        try {
            const response = await fetch(`http://localhost:8080/api/ratings/${ratingId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                // Refresh rating history
                const historyResponse = await fetch(`http://localhost:8080/api/ratings/${symbol}/history`);
                if (historyResponse.ok) {
                    const data = await historyResponse.json();
                    setRatingHistory(data || []);
                }
                // Clear symbol list cache to force refresh
                window.dispatchEvent(new CustomEvent('ratingsChanged'));
            } else {
                alert('Failed to delete rating');
            }
        } catch (err) {
            alert('Error deleting rating');
        }
    };

    const handleSubmitRating = async () => {
        if (rating === null) {
            alert('Please select a rating');
            return;
        }
        setSubmitting(true);
        try {
            const response = await fetch(`http://localhost:8080/api/ratings/${symbol}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rating, notes: notes || undefined })
            });
            if (response.ok) {
                // Refresh rating history
                const historyResponse = await fetch(`http://localhost:8080/api/ratings/${symbol}/history`);
                if (historyResponse.ok) {
                    const data = await historyResponse.json();
                    setRatingHistory(data || []);
                }
                // Reset form and blur textarea
                setRating(null);
                setNotes('');
                const textarea = document.querySelector('textarea[placeholder*="Optional notes"]') as HTMLTextAreaElement;
                if (textarea) textarea.blur();
                // Clear symbol list cache to force refresh
                window.dispatchEvent(new CustomEvent('ratingsChanged'));
            } else {
                alert('Failed to submit rating');
            }
        } catch (err) {
            alert('Error submitting rating');
        } finally {
            setSubmitting(false);
        }
    };

    const getRatingColor = (rating: number): string => {
        if (rating === 0) return 'text-gray-500';
        if (rating > 0) {
            const intensity = Math.min(rating / 5, 1);
            if (intensity > 0.6) return 'text-green-700 font-bold';
            if (intensity > 0.3) return 'text-green-600';
            return 'text-green-500';
        } else {
            const intensity = Math.min(Math.abs(rating) / 5, 1);
            if (intensity > 0.6) return 'text-red-700 font-bold';
            if (intensity > 0.3) return 'text-red-600';
            return 'text-red-500';
        }
    };

    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            const target = event.target as HTMLElement;
            const isTyping = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT';
            
            // If typing, only allow Enter in textarea to submit, ignore everything else
            if (isTyping) {
                if (event.key === 'Enter' && target.tagName === 'TEXTAREA') {
                    event.preventDefault();
                    handleSubmitRating();
                }
                return; // Ignore all other hotkeys when typing
            }
            
            // Hotkeys only work when NOT typing
            if (event.key === 'Escape' && onClose) {
                onClose();
            } else if (event.key.toLowerCase() === 't') {
                const tradingViewUrl = `https://www.tradingview.com/chart/?symbol=${symbol}`;
                window.open(tradingViewUrl, '_blank', 'noopener,noreferrer');
            } else {
                // Number keys for rating (1-5, Shift+1-5 for negative, 0 for neutral)
                const num = parseInt(event.key);
                if (!isNaN(num) && num >= 0 && num <= 5) {
                    const newRating = event.shiftKey && num > 0 ? -num : num;
                    setRating(newRating);
                    // Auto-focus the notes textarea
                    setTimeout(() => {
                        const textarea = document.querySelector('textarea[placeholder*="Optional notes"]') as HTMLTextAreaElement;
                        if (textarea) textarea.focus();
                    }, 0);
                }
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [symbol, onClose, handleSubmitRating]);

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
                    <div className="flex items-baseline gap-3">
                        <h2 className="text-2xl font-semibold">{symbol}</h2>
                        {ratingHistory.length > 0 && (
                            <span className={`font-mono text-2xl font-bold ${getRatingColor(ratingHistory[0].rating)}`}>
                                {ratingHistory[0].rating > 0 ? '+' : ''}{ratingHistory[0].rating}
                            </span>
                        )}
                    </div>
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

                    {/* Rating Form */}
                    <div className="mt-6 pt-6 border-t border-gray-300">
                        <div className="flex items-baseline gap-3 mb-3">
                            <h4 className="text-md font-semibold">Rate This Stock</h4>
                            <span className="text-xs text-gray-500">(Keys: 1-5, Shift+1-5 for negative, 0 for neutral, Enter to submit)</span>
                        </div>
                        <div className="flex flex-col gap-3">
                            <div className="flex items-center gap-4">
                                <label className="font-medium text-gray-600 w-20">Rating:</label>
                                <select 
                                    value={rating === null ? '' : rating} 
                                    onChange={(e) => setRating(e.target.value === '' ? null : parseInt(e.target.value))}
                                    className="px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="">Select rating...</option>
                                    {[-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5].map(r => (
                                        <option key={r} value={r}>{r > 0 ? `+${r}` : r}</option>
                                    ))}
                                </select>
                                <span className="text-sm text-gray-500">(-5 = avoid, 0 = neutral, +5 = strong buy)</span>
                            </div>
                            <div className="flex items-start gap-4">
                                <label className="font-medium text-gray-600 w-20 pt-2">Notes:</label>
                                <textarea 
                                    value={notes}
                                    onChange={(e) => setNotes(e.target.value)}
                                    placeholder="Optional notes about your rating..."
                                    className="flex-1 px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                    rows={3}
                                />
                            </div>
                            <div className="flex justify-end">
                                <button 
                                    onClick={handleSubmitRating}
                                    disabled={submitting || rating === null}
                                    className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                                >
                                    {submitting ? 'Submitting...' : 'Submit Rating'}
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Rating History */}
                    {ratingHistory.length > 0 && (
                        <div className="mt-6 pt-6 border-t border-gray-300">
                            <h4 className="text-md font-semibold mb-3">Rating History</h4>
                            <div className="space-y-3">
                                {ratingHistory.map((r) => (
                                    <div key={r.id} className="p-3 bg-white border border-gray-200 rounded relative">
                                        <button
                                            onClick={() => handleDeleteRating(r.id)}
                                            className="absolute top-2 right-2 text-gray-400 hover:text-red-600 text-sm font-bold"
                                            title="Delete rating"
                                        >
                                            ×
                                        </button>
                                        <div className="flex items-center gap-3 mb-1">
                                            <span className={`font-mono text-lg font-bold ${getRatingColor(r.rating)}`}>
                                                {r.rating > 0 ? '+' : ''}{r.rating}
                                            </span>
                                            <span className="text-xs text-gray-500">
                                                {new Date(r.createdAt).toLocaleString()}
                                            </span>
                                        </div>
                                        {r.notes && (
                                            <p className="text-sm text-gray-700 mt-2">{r.notes}</p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            ) : null}
        </>
    );
}
