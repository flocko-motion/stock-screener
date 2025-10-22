import { useState, useEffect, useRef } from 'react';
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

interface PriceData {
    Date: string;
    Open: number;
    High: number;
    Low: number;
    Avg: number;
    Close: number;
    YoY: number | null;
    SymbolTicker: string;
}

export default function SymbolDetail({ symbol, analysisId, onClose }: SymbolDetailProps) {
    const [profile, setProfile] = useState<SymbolProfile | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [rating, setRating] = useState<number | null>(null);
    const [notes, setNotes] = useState<string>('');
    const [ratingHistory, setRatingHistory] = useState<UserRating[]>([]);
    const [submitting, setSubmitting] = useState(false);
    const [monthlyPrices, setMonthlyPrices] = useState<PriceData[]>([]);
    const [pricesLoading, setPricesLoading] = useState(false);
    const [pricesExpanded, setPricesExpanded] = useState(false);
    const [pricesFetched, setPricesFetched] = useState(false);
    const [weeklyPrices, setWeeklyPrices] = useState<PriceData[]>([]);
    const [weeklyLoading, setWeeklyLoading] = useState(false);
    const [weeklyExpanded, setWeeklyExpanded] = useState(false);
    const [weeklyFetched, setWeeklyFetched] = useState(false);
    const [fullscreenImage, setFullscreenImage] = useState<string | null>(null);
    const [isFavorite, setIsFavorite] = useState(false);
    const ratingSectionRef = useRef<HTMLDivElement>(null);
    const chartSectionRef = useRef<HTMLDivElement>(null);
    const pricesSectionRef = useRef<HTMLDivElement>(null);
    const weeklySectionRef = useRef<HTMLDivElement>(null);

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
                setIsFavorite(profileData.isFavorite || false);
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

    const toggleFavorite = async () => {
        try {
            const response = await fetch(`http://localhost:8080/api/favorites/${symbol}`, { method: 'POST' });
            const data = await response.json();
            setIsFavorite(data.isFavorite);
        } catch (err) {
            console.error('Failed to toggle favorite:', err);
        }
    };

    const fetchMonthlyPrices = async () => {
        if (pricesFetched) return; // Already fetched
        setPricesLoading(true);
        try {
            const response = await fetch(`http://localhost:8080/api/prices/monthly/${symbol}`);
            if (response.ok) {
                const data = await response.json();
                setMonthlyPrices(data.prices || []);
                setPricesFetched(true);
            }
        } catch (err) {
            console.error('Failed to fetch monthly prices:', err);
        } finally {
            setPricesLoading(false);
        }
    };

    const fetchWeeklyPrices = async () => {
        if (weeklyFetched) return;
        setWeeklyLoading(true);
        try {
            const response = await fetch(`http://localhost:8080/api/prices/weekly/${symbol}`);
            if (response.ok) {
                const data = await response.json();
                setWeeklyPrices(data.prices || []);
                setWeeklyFetched(true);
            }
        } catch (err) {
            console.error('Failed to fetch weekly prices:', err);
        } finally {
            setWeeklyLoading(false);
        }
    };

    const togglePrices = () => {
        const newExpanded = !pricesExpanded;
        setPricesExpanded(newExpanded);
        if (newExpanded) {
            if (!pricesFetched) {
                fetchMonthlyPrices();
            }
            // Scroll to the section after a brief delay to allow expansion
            setTimeout(() => {
                pricesSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        }
    };

    const toggleWeekly = () => {
        const newExpanded = !weeklyExpanded;
        setWeeklyExpanded(newExpanded);
        if (newExpanded) {
            if (!weeklyFetched) {
                fetchWeeklyPrices();
            }
            setTimeout(() => {
                weeklySectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        }
    };

    // Reset prices state when symbol changes
    useEffect(() => {
        setPricesExpanded(false);
        setPricesFetched(false);
        setMonthlyPrices([]);
        setWeeklyExpanded(false);
        setWeeklyFetched(false);
        setWeeklyPrices([]);
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
                // Clear symbol list cache to force refresh when user returns to stocks tab
                sessionStorage.setItem('symbolCacheInvalidated', Date.now().toString());
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
                // Clear symbol list cache to force refresh when user returns to stocks tab
                sessionStorage.setItem('symbolCacheInvalidated', Date.now().toString());
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

    const formatMarketCap = (marketCap: number): string => {
        const absValue = Math.abs(marketCap);
        if (absValue >= 1e12) {
            return `$${(marketCap / 1e12).toFixed(1)}T`;
        } else if (absValue >= 1e9) {
            return `$${(marketCap / 1e9).toFixed(1)}B`;
        } else if (absValue >= 1e6) {
            return `$${(marketCap / 1e6).toFixed(1)}M`;
        } else if (absValue >= 1e3) {
            return `$${(marketCap / 1e3).toFixed(1)}K`;
        }
        return `$${marketCap}`;
    };

    const formatPrice = (price: number): string => {
        const absValue = Math.abs(price);
        if (absValue === 0) return '0.00';

        // Use log10 to determine decimal places
        // For prices >= 100: 2 decimals
        // For prices >= 10: 3 decimals
        // For prices >= 1: 4 decimals
        // For prices < 1: 5+ decimals
        const log = Math.log10(absValue);
        let decimals: number;

        // if (log >= 2) {
        //     decimals = 0; // >= 100
        // } else if (log >= 1) {
        //     decimals = 1; // >= 10
        // } else if (log >= 0) {
        //     decimals = 2; // >= 1
        // } else {
        //     // For very small numbers, add more decimals
        //     decimals = Math.ceil(Math.abs(log));
        // }
        decimals = Math.min(10, Math.max(0, 3 - Math.ceil(Math.abs(log))));
        return price.toFixed(decimals);
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
                return;
            }

            if (event.key.toLowerCase() === 'r') {
                event.preventDefault();
                ratingSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                return;
            }

            if (event.key.toLowerCase() === 'c') {
                event.preventDefault();
                if (fullscreenImage === chartUrl) {
                    setFullscreenImage(null);
                } else {
                    setFullscreenImage(chartUrl);
                }
                return;
            }

            if (event.key.toLowerCase() === 'h') {
                event.preventDefault();
                if (fullscreenImage === histogramUrl) {
                    setFullscreenImage(null);
                } else {
                    setFullscreenImage(histogramUrl);
                }
                return;
            }

            if (event.key.toLowerCase() === 'm') {
                event.preventDefault();
                togglePrices();
                return;
            }

            if (event.key.toLowerCase() === 'w') {
                event.preventDefault();
                toggleWeekly();
                return;
            }

            if (event.key.toLowerCase() === 'f') {
                event.preventDefault();
                toggleFavorite();
                return;
            }

            if (event.key === 'Enter') {
                event.preventDefault();
                handleSubmitRating();
                return;
            }

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
                        <span
                            onClick={toggleFavorite}
                            className={`cursor-pointer text-3xl hover:scale-125 inline-block transition-transform ${isFavorite ? 'text-yellow-500' : 'text-gray-300'}`}
                        >
                            {isFavorite ? '★' : '☆'}
                        </span>
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
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => {
                            chartSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                            setTimeout(() => setFullscreenImage(chartUrl), 300);
                        }}
                        className="px-2 py-1 text-xs text-gray-400 hover:text-gray-600 border border-gray-300 rounded"
                    >
                        [C]hart
                    </button>
                    <button
                        onClick={() => {
                            chartSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                            setTimeout(() => setFullscreenImage(histogramUrl), 300);
                        }}
                        className="px-2 py-1 text-xs text-gray-400 hover:text-gray-600 border border-gray-300 rounded"
                    >
                        [H]istogram
                    </button>
                    <button
                        onClick={togglePrices}
                        className="px-2 py-1 text-xs text-gray-400 hover:text-gray-600 border border-gray-300 rounded"
                    >
                        [M]onthly
                    </button>
                    <button
                        onClick={toggleWeekly}
                        className="px-2 py-1 text-xs text-gray-400 hover:text-gray-600 border border-gray-300 rounded"
                    >
                        [W]eekly
                    </button>
                    <button
                        onClick={() => ratingSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
                        className="px-2 py-1 text-xs text-gray-400 hover:text-gray-600 border border-gray-300 rounded"
                    >
                        [R]atings
                    </button>
                    <a
                        href={`https://www.tradingview.com/chart/?symbol=${symbol}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-2 py-1 text-xs text-gray-400 hover:text-gray-600 border border-gray-300 rounded"
                    >
                        [T]radingView
                    </a>
                    {onClose && (
                        <button
                            onClick={onClose}
                            className="px-2 py-1 text-xs text-gray-400 hover:text-gray-600 border border-gray-300 rounded"
                        >
                            [ESC] close
                        </button>
                    )}
                </div>
            </div>

            {/* Charts */}
            <div ref={chartSectionRef} className="mb-8">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div>
                        <img
                            src={chartUrl}
                            alt={`Chart for ${symbol}`}
                            className="w-full h-[50vh] object-contain border border-gray-200 rounded cursor-pointer hover:opacity-90"
                            onClick={() => setFullscreenImage(chartUrl)}
                        />
                    </div>
                    <div>
                        <img
                            src={histogramUrl}
                            alt={`Histogram for ${symbol}`}
                            className="w-full h-[50vh] object-contain border border-gray-200 rounded cursor-pointer hover:opacity-90"
                            onClick={() => setFullscreenImage(histogramUrl)}
                        />
                    </div>
                </div>
            </div>

            {/* Fullscreen Image Modal */}
            {fullscreenImage && (
                <div
                    className="fixed inset-0 bg-black z-50 flex items-center justify-center"
                    onClick={() => setFullscreenImage(null)}
                >
                    <img
                        src={fullscreenImage}
                        alt="Fullscreen view"
                        className="w-full h-full object-contain"
                        onClick={(e) => e.stopPropagation()}
                    />
                    <button
                        className="absolute top-2 right-2 text-white text-3xl font-bold hover:text-gray-400 px-3 py-1"
                        onClick={() => setFullscreenImage(null)}
                    >
                        ×
                    </button>
                </div>
            )}

            {/* Monthly Prices Table - Collapsible */}
            <div ref={pricesSectionRef} className="mb-8">
                <button
                    onClick={togglePrices}
                    className="flex items-center gap-2 text-lg font-semibold mb-4 hover:text-gray-700"
                >
                    <span>{pricesExpanded ? '▼' : '▶'}</span>
                    <span>Monthly Prices</span>
                </button>
                {pricesExpanded && (
                    <div>
                        {pricesLoading ? (
                            <div className="text-center py-4">
                                <p className="text-gray-500">Loading prices...</p>
                            </div>
                        ) : monthlyPrices.length > 0 ? (
                            <div className="overflow-x-auto">
                                <table className="min-w-full border border-gray-200 text-sm">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-4 py-2 text-left font-medium text-gray-600 border-b">Date</th>
                                            <th className="px-4 py-2 text-right font-medium text-gray-600 border-b">Open</th>
                                            <th className="px-4 py-2 text-right font-medium text-gray-600 border-b">High</th>
                                            <th className="px-4 py-2 text-right font-medium text-gray-600 border-b">Low</th>
                                            <th className="px-4 py-2 text-right font-medium text-gray-600 border-b">Close</th>
                                            <th className="px-4 py-2 text-right font-medium text-gray-600 border-b">Avg</th>
                                            <th className="px-4 py-2 text-right font-medium text-gray-600 border-b">YoY %</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {monthlyPrices.map((price, idx) => (
                                            <tr key={idx} className="hover:bg-gray-50">
                                                <td className="px-4 py-2 border-b">
                                                    {new Date(price.Date).toLocaleDateString('en-US', { year: 'numeric', month: 'short' })}
                                                </td>
                                                <td className="px-4 py-2 text-right border-b">{formatPrice(price.Open)}</td>
                                                <td className="px-4 py-2 text-right border-b">{formatPrice(price.High)}</td>
                                                <td className="px-4 py-2 text-right border-b">{formatPrice(price.Low)}</td>
                                                <td className="px-4 py-2 text-right border-b font-medium">{formatPrice(price.Close)}</td>
                                                <td className="px-4 py-2 text-right border-b">{formatPrice(price.Avg)}</td>
                                                <td className={`px-4 py-2 text-right border-b ${price.YoY === null ? 'text-gray-400' :
                                                    price.YoY > 0 ? 'text-green-600' :
                                                        price.YoY < 0 ? 'text-red-600' : 'text-gray-600'
                                                    }`}>
                                                    {price.YoY === null ? 'N/A' : `${price.YoY > 0 ? '+' : ''}${price.YoY.toFixed(1)}%`}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <p className="text-gray-500">No monthly price data available</p>
                        )}
                    </div>
                )}
            </div>

            {/* Weekly Prices Table - Collapsible */}
            <div ref={weeklySectionRef} className="mb-8">
                <button
                    onClick={toggleWeekly}
                    className="flex items-center gap-2 text-lg font-semibold mb-4 hover:text-gray-700"
                >
                    <span>{weeklyExpanded ? '▼' : '▶'}</span>
                    <span>Weekly Prices</span>
                </button>
                {weeklyExpanded && (
                    <div>
                        {weeklyLoading ? (
                            <div className="text-center py-4">
                                <p className="text-gray-500">Loading prices...</p>
                            </div>
                        ) : weeklyPrices.length > 0 ? (
                            <div className="overflow-x-auto">
                                <table className="min-w-full border border-gray-200 text-sm">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-4 py-2 text-left font-medium text-gray-600 border-b">Date</th>
                                            <th className="px-4 py-2 text-right font-medium text-gray-600 border-b">Open</th>
                                            <th className="px-4 py-2 text-right font-medium text-gray-600 border-b">High</th>
                                            <th className="px-4 py-2 text-right font-medium text-gray-600 border-b">Low</th>
                                            <th className="px-4 py-2 text-right font-medium text-gray-600 border-b">Close</th>
                                            <th className="px-4 py-2 text-right font-medium text-gray-600 border-b">Avg</th>
                                            <th className="px-4 py-2 text-right font-medium text-gray-600 border-b">YoY %</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {weeklyPrices.map((price, idx) => (
                                            <tr key={idx} className="hover:bg-gray-50">
                                                <td className="px-4 py-2 border-b">
                                                    {new Date(price.Date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
                                                </td>
                                                <td className="px-4 py-2 text-right border-b">{formatPrice(price.Open)}</td>
                                                <td className="px-4 py-2 text-right border-b">{formatPrice(price.High)}</td>
                                                <td className="px-4 py-2 text-right border-b">{formatPrice(price.Low)}</td>
                                                <td className="px-4 py-2 text-right border-b font-medium">{formatPrice(price.Close)}</td>
                                                <td className="px-4 py-2 text-right border-b">{formatPrice(price.Avg)}</td>
                                                <td className={`px-4 py-2 text-right border-b ${price.YoY === null ? 'text-gray-400' :
                                                    price.YoY > 0 ? 'text-green-600' :
                                                        price.YoY < 0 ? 'text-red-600' : 'text-gray-600'
                                                    }`}>
                                                    {price.YoY === null ? 'N/A' : `${price.YoY > 0 ? '+' : ''}${price.YoY.toFixed(1)}%`}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <p className="text-gray-500">No weekly price data available</p>
                        )}
                    </div>
                )}
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
                        <div className="md:col-span-2 lg:col-span-3">
                            <span className="font-medium text-gray-600">Sector:</span>
                            <span className="ml-2">{profile.sector || 'N/A'}</span>
                            <span className="mx-3 text-gray-400">|</span>
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
                            <span className="ml-2">{profile.marketCap ? formatMarketCap(profile.marketCap) : 'N/A'}</span>
                        </div>
                        <div>
                            <span className="font-medium text-gray-600">Founded:</span>
                            <span className="ml-2">{profile.inception ? new Date(profile.inception).getFullYear() : 'N/A'}</span>
                        </div>
                        <div>
                            <span className="font-medium text-gray-600">History:</span>
                            <span className="ml-2">{profile.oldestPrice ? new Date(profile.oldestPrice).getFullYear() : 'N/A'}</span>
                        </div>
                        <div className="md:col-span-2 lg:col-span-3">
                            <span className="font-medium text-gray-600">Price:</span>
                            <span className="ml-2 font-mono">{profile.currentPriceUsd != null ? `$${profile.currentPriceUsd.toFixed(2)}` : 'N/A'}</span>
                            <span className="mx-3 text-gray-400">|</span>
                            <span className="font-medium text-gray-600">ATH(12):</span>
                            <span className="ml-2 font-mono">{profile.ath12m != null ? `$${profile.ath12m.toFixed(2)}` : 'N/A'}</span>
                            <span className="mx-3 text-gray-400">|</span>
                            <span className="font-medium text-gray-600">ΔATH:</span>
                            <span className="ml-2 font-mono">
                                {profile.currentPriceUsd != null && profile.ath12m != null && profile.ath12m > 0 ? (
                                    <span className={((profile.currentPriceUsd / profile.ath12m - 1) * 100) >= -10 ? 'text-green-600' : ((profile.currentPriceUsd / profile.ath12m - 1) * 100) >= -30 ? 'text-yellow-600' : 'text-red-600'}>
                                        {((profile.currentPriceUsd / profile.ath12m - 1) * 100).toFixed(1)}%
                                    </span>
                                ) : 'N/A'}
                            </span>
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
                    <div ref={ratingSectionRef} className="mt-6 pt-6 border-t border-gray-300">
                        <div className="flex items-baseline gap-3 mb-3">
                            <h4 className="text-md font-semibold">Rate This Stock</h4>
                            <span className="text-xs text-gray-500">(Keys: R to scroll here, 1-5, Shift+1-5 for negative, 0 for neutral, Enter to submit)</span>
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
