import { useState, useEffect } from 'react';
import { DocumentTextIcon } from '@heroicons/react/24/outline';

interface Note {
    id: number;
    ticker: string;
    rating: number;
    notes: string;
    createdAt: string;
}

interface NotesViewProps {
    onOpenSymbol?: (symbol: string) => void;
}

export default function NotesView({ onOpenSymbol }: NotesViewProps) {
    const [notes, setNotes] = useState<Note[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [favorites, setFavorites] = useState<Set<string>>(new Set());

    const fetchNotes = async () => {
        try {
            const response = await fetch('http://localhost:8080/api/notes');
            if (!response.ok) throw new Error('Failed to fetch notes');
            const data = await response.json();
            setNotes(data || []);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    const fetchFavorites = async () => {
        try {
            const response = await fetch('http://localhost:8080/api/favorites');
            if (response.ok) {
                const data = await response.json();
                setFavorites(new Set(data || []));
            }
        } catch (err) {
            console.error('Failed to fetch favorites:', err);
        }
    };

    const toggleFavorite = async (ticker: string) => {
        try {
            const response = await fetch(`http://localhost:8080/api/favorites/${ticker}`, {
                method: 'POST'
            });
            if (response.ok) {
                const data = await response.json();
                setFavorites(prev => {
                    const newSet = new Set(prev);
                    if (data.isFavorite) {
                        newSet.add(ticker);
                    } else {
                        newSet.delete(ticker);
                    }
                    return newSet;
                });
            }
        } catch (err) {
            console.error('Failed to toggle favorite:', err);
        }
    };

    useEffect(() => {
        fetchNotes();
        fetchFavorites();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Group notes by ticker
    const groupedNotes = notes.reduce((acc, note) => {
        if (!acc[note.ticker]) {
            acc[note.ticker] = [];
        }
        acc[note.ticker].push(note);
        return acc;
    }, {} as Record<string, Note[]>);

    // Sort tickers by most recent note (newest first)
    const sortedTickers = Object.keys(groupedNotes).sort((a, b) => {
        const aLatest = groupedNotes[a][0].createdAt;
        const bLatest = groupedNotes[b][0].createdAt;
        return new Date(bLatest).getTime() - new Date(aLatest).getTime();
    });

    // Sort notes within each ticker chronologically (oldest first) to show opinion evolution
    Object.keys(groupedNotes).forEach(ticker => {
        groupedNotes[ticker].sort((a, b) => 
            new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
        );
    });

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-gray-500">Loading notes...</div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-3 mb-6">
                <DocumentTextIcon className="w-6 h-6 text-blue-500" />
                <h2 className="text-2xl font-bold text-gray-900">Recent Notes</h2>
                <span className="text-sm text-gray-500">
                    ({sortedTickers.length} {sortedTickers.length === 1 ? 'stock' : 'stocks'}, {notes.length} {notes.length === 1 ? 'note' : 'notes'})
                </span>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                    {error}
                </div>
            )}

            {notes.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                    <DocumentTextIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                    <p className="text-lg">No notes found</p>
                    <p className="text-sm">Add notes to your stock ratings to see them here</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {sortedTickers.map((ticker) => {
                        const tickerNotes = groupedNotes[ticker];
                        const latestNote = tickerNotes[tickerNotes.length - 1]; // Last note is latest (oldest→newest sort)
                        
                        // Determine border color based on rating
                        const getBorderColor = (rating: number) => {
                            if (rating >= 4) return 'border-t-green-500';
                            if (rating >= 2) return 'border-t-green-400';
                            if (rating >= 1) return 'border-t-green-300';
                            if (rating === 0) return 'border-t-gray-400';
                            if (rating >= -1) return 'border-t-red-300';
                            if (rating >= -3) return 'border-t-red-400';
                            return 'border-t-red-500';
                        };
                        
                        return (
                            <div
                                key={ticker}
                                className={`border border-gray-200 border-t-4 ${getBorderColor(latestNote.rating)} bg-white rounded-lg p-4 hover:shadow-md transition`}
                            >
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex items-center gap-3">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); toggleFavorite(ticker); }}
                                            className={`cursor-pointer text-xl hover:scale-125 inline-block transition-transform ${favorites.has(ticker) ? 'text-yellow-500' : 'text-gray-300'}`}
                                            title={favorites.has(ticker) ? 'Remove from favorites' : 'Add to favorites'}
                                        >
                                            {favorites.has(ticker) ? '★' : '☆'}
                                        </button>
                                        <button
                                            onClick={() => onOpenSymbol?.(ticker)}
                                            className="text-xl font-bold text-blue-600 hover:text-blue-800 hover:underline"
                                        >
                                            {ticker}
                                        </button>
                                        <div className="flex flex-col">
                                            <div className="flex items-center gap-2">
                                                <span className="text-xs text-gray-500">Latest:</span>
                                                <span className={`text-sm font-bold ${latestNote.rating >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                    {latestNote.rating > 0 ? '+' : ''}{latestNote.rating}
                                                </span>
                                            </div>
                                            {tickerNotes.length > 1 && (
                                                <span className="text-xs text-gray-400">
                                                    {tickerNotes.length} updates over time →
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    <span className="text-xs text-gray-500">
                                        {new Date(latestNote.createdAt).toISOString().split('T')[0]}
                                    </span>
                                </div>
                                
                                <div className="space-y-3 pl-4 border-l-4 border-gray-200">
                                    {tickerNotes.map((note, index) => {
                                        const prevNote = index > 0 ? tickerNotes[index - 1] : null;
                                        const ratingChanged = prevNote && prevNote.rating !== note.rating;
                                        const ratingIncreased = prevNote && note.rating > prevNote.rating;
                                        
                                        return (
                                            <div key={note.id} className="relative">
                                                <div className="flex items-start justify-between mb-1">
                                                    <div className="flex items-center gap-2">
                                                        <span className={`text-sm font-bold ${note.rating >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                            {note.rating > 0 ? '+' : ''}{note.rating}
                                                        </span>
                                                        {ratingChanged && (
                                                            <span className={`text-lg font-bold ${ratingIncreased ? 'text-green-600' : 'text-red-600'}`}>
                                                                {ratingIncreased ? '↑' : '↓'}
                                                            </span>
                                                        )}
                                                    </div>
                                                    <span className="text-xs text-gray-400">
                                                        {new Date(note.createdAt).toISOString().replace('T', ' ').slice(0, 19)}
                                                    </span>
                                                </div>
                                                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                                                    {note.notes}
                                                </p>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
