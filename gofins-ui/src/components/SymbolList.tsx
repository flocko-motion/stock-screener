import { useEffect, useState, useRef } from 'react';

interface MultiSelectProps {
    options: string[];
    selected: string[];
    onChange: (selected: string[]) => void;
    placeholder: string;
}

function MultiSelect({ options, selected, onChange, placeholder }: MultiSelectProps) {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const toggleOption = (option: string) => {
        if (selected.includes(option)) {
            onChange(selected.filter(s => s !== option));
        } else {
            onChange([...selected, option]);
        }
    };

    const selectAll = () => {
        onChange([...options]);
    };

    const selectNone = () => {
        onChange([]);
    };

    const displayText = selected.length === 0 
        ? placeholder 
        : selected.length === 1 
            ? selected[0] 
            : `${selected.length} selected`;

    return (
        <div ref={dropdownRef} className="relative">
            <button
                type="button"
                onClick={() => setIsOpen(!isOpen)}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 bg-white text-left flex justify-between items-center"
            >
                <span className="truncate">{displayText}</span>
                <span className="ml-1">▼</span>
            </button>
            {isOpen && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded shadow-lg max-h-60 overflow-y-auto">
                    {options.length === 0 ? (
                        <div className="px-2 py-1 text-sm text-gray-500">No options</div>
                    ) : (
                        <>
                            <div className="sticky top-0 bg-gray-50 border-b border-gray-200 px-2 py-1 flex gap-2">
                                <button
                                    type="button"
                                    onClick={selectAll}
                                    className="flex-1 px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 rounded"
                                >
                                    All
                                </button>
                                <button
                                    type="button"
                                    onClick={selectNone}
                                    className="flex-1 px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                                >
                                    None
                                </button>
                            </div>
                            {options.map(option => (
                                <label
                                    key={option}
                                    className="flex items-center px-2 py-1 hover:bg-gray-100 cursor-pointer text-sm"
                                >
                                    <input
                                        type="checkbox"
                                        checked={selected.includes(option)}
                                        onChange={() => toggleOption(option)}
                                        className="mr-2 rounded"
                                    />
                                    <span className="truncate">{option}</span>
                                </label>
                            ))}
                        </>
                    )}
                </div>
            )}
        </div>
    );
}

interface Symbol {
    ticker: string;
    exchange?: string;
    name?: string;
    type?: string;
    sector?: string;
    industry?: string;
    country?: string;
    inception?: string;
    oldestPrice?: string;
    isActivelyTrading?: boolean;
    marketCap?: number;
    isFavorite: boolean;
    userRating?: number;
}

interface SymbolListProps {
    endpoint: string;
    description: string;
    onOpenSymbol?: (symbol: string) => void;
}

// Cache for symbol lists by endpoint
const symbolCache: Record<string, Symbol[]> = {};
// Track ongoing fetches to prevent duplicates
const fetchingCache: Record<string, boolean> = {};

export default function SymbolList({ endpoint, description, onOpenSymbol }: SymbolListProps) {
    const [symbols, setSymbols] = useState<Symbol[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    // Load filters from sessionStorage or use defaults
    const getStoredFilters = () => {
        const stored = sessionStorage.getItem('symbolListFilters');
        return stored ? JSON.parse(stored) : {};
    };
    
    const filters = getStoredFilters();
    const [searchTerm, setSearchTerm] = useState(filters.searchTerm || '');
    const [currentPage, setCurrentPage] = useState(1);
    const [exchangeFilter, setExchangeFilter] = useState<string[]>(filters.exchangeFilter || []);
    const [countryFilter, setCountryFilter] = useState<string[]>(filters.countryFilter || []);
    const [sectorFilter, setSectorFilter] = useState<string[]>(filters.sectorFilter || []);
    const [mcapMin, setMcapMin] = useState(filters.mcapMin || '');
    const [mcapMax, setMcapMax] = useState(filters.mcapMax || '');
    const [inceptionMin, setInceptionMin] = useState(filters.inceptionMin || '');
    const [inceptionMax, setInceptionMax] = useState(filters.inceptionMax || '');
    const [oldestPriceMin, setOldestPriceMin] = useState(filters.oldestPriceMin || '');
    const [oldestPriceMax, setOldestPriceMax] = useState(filters.oldestPriceMax || '');
    const [favoritesOnly, setFavoritesOnly] = useState(filters.favoritesOnly || false);
    const [ratingMin, setRatingMin] = useState(filters.ratingMin || '');
    const [ratingMax, setRatingMax] = useState(filters.ratingMax || '');
    const [ratedOnly, setRatedOnly] = useState(filters.ratedOnly || false);
    const [sortColumn, setSortColumn] = useState<keyof Symbol>(filters.sortColumn || 'ticker');
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>(filters.sortDirection || 'asc');
    const itemsPerPage = 100;
    
    // Save filters to sessionStorage whenever they change
    useEffect(() => {
        sessionStorage.setItem('symbolListFilters', JSON.stringify({
            searchTerm, exchangeFilter, countryFilter, sectorFilter,
            mcapMin, mcapMax, inceptionMin, inceptionMax,
            oldestPriceMin, oldestPriceMax, favoritesOnly,
            ratingMin, ratingMax, ratedOnly, sortColumn, sortDirection
        }));
    }, [searchTerm, exchangeFilter, countryFilter, sectorFilter, mcapMin, mcapMax, 
        inceptionMin, inceptionMax, oldestPriceMin, oldestPriceMax, favoritesOnly,
        ratingMin, ratingMax, ratedOnly, sortColumn, sortDirection]);

    const toggleFavorite = async (ticker: string, e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            const response = await fetch(`http://localhost:8080/api/favorites/${ticker}`, { method: 'POST' });
            const data = await response.json();
            setSymbols(prev => prev.map(s => s.ticker === ticker ? { ...s, isFavorite: data.isFavorite } : s));
            if (symbolCache[endpoint]) {
                symbolCache[endpoint] = symbolCache[endpoint].map(s => s.ticker === ticker ? { ...s, isFavorite: data.isFavorite } : s);
            }
        } catch (err) {
            console.error('Failed to toggle favorite:', err);
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

    const fetchSymbols = async () => {
        // Mark as fetching
        fetchingCache[endpoint] = true;
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(`http://localhost:8080${endpoint}`);
            if (!response.ok) {
                throw new Error('Failed to fetch symbols');
            }

            const data = await response.json();
            const fetchedSymbols = data.symbols || [];

            // Cache the results
            symbolCache[endpoint] = fetchedSymbols;
            // Create new array reference to force re-render
            setSymbols([...fetchedSymbols]);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
            // Clear fetching flag
            delete fetchingCache[endpoint];
        }
    };

    useEffect(() => {
        // Check if cache was invalidated (e.g., rating was added/deleted)
        const invalidated = sessionStorage.getItem('symbolCacheInvalidated');
        if (invalidated) {
            console.log('Cache invalidated, clearing...');
            delete symbolCache[endpoint];
            sessionStorage.removeItem('symbolCacheInvalidated');
        }
        
        // Check cache first
        if (symbolCache[endpoint]) {
            setSymbols(symbolCache[endpoint]);
            setLoading(false);
        } else if (!fetchingCache[endpoint]) {
            fetchSymbols();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [endpoint]);

    useEffect(() => {
        // Listen for rating changes and refresh data
        const handleRatingsChanged = async () => {
            console.log('ratingsChanged event received, refreshing symbols...');
            delete symbolCache[endpoint];
            delete fetchingCache[endpoint];
            await fetchSymbols();
            console.log('Symbols refreshed, new count:', symbols.length);
        };
        
        window.addEventListener('ratingsChanged', handleRatingsChanged);
        return () => window.removeEventListener('ratingsChanged', handleRatingsChanged);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [endpoint]);

    const formatYear = (dateStr: string | undefined) => {
        if (!dateStr) return 'N/A';
        return new Date(dateStr).getFullYear().toString();
    };

    const formatMarketCap = (marketCap: number | undefined) => {
        if (!marketCap) return 'N/A';
        
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

    // Filter symbols based on all criteria
    const matchedSymbols = symbols.filter(symbol => {
        // Text search
        if (searchTerm) {
            const search = searchTerm.toLowerCase();
            const matches = symbol.ticker.toLowerCase().includes(search) ||
                symbol.name?.toLowerCase().includes(search) ||
                symbol.sector?.toLowerCase().includes(search) ||
                symbol.country?.toLowerCase().includes(search);
            if (!matches) return false;
        }

        // Exchange filter
        if (exchangeFilter.length > 0 && (!symbol.exchange || !exchangeFilter.includes(symbol.exchange))) return false;

        // Country filter
        if (countryFilter.length > 0 && (!symbol.country || !countryFilter.includes(symbol.country))) return false;

        // Sector filter
        if (sectorFilter.length > 0 && (!symbol.sector || !sectorFilter.includes(symbol.sector))) return false;

        // Market cap filters
        if (mcapMin && (!symbol.marketCap || symbol.marketCap < parseFloat(mcapMin) * 1e9)) return false;
        if (mcapMax && (!symbol.marketCap || symbol.marketCap > parseFloat(mcapMax) * 1e9)) return false;

        // Inception year filters
        if (inceptionMin && symbol.inception) {
            const year = new Date(symbol.inception).getFullYear();
            if (year < parseInt(inceptionMin)) return false;
        }
        if (inceptionMax && symbol.inception) {
            const year = new Date(symbol.inception).getFullYear();
            if (year > parseInt(inceptionMax)) return false;
        }

        // Oldest price year filters
        if (oldestPriceMin && symbol.oldestPrice) {
            const year = new Date(symbol.oldestPrice).getFullYear();
            if (year < parseInt(oldestPriceMin)) return false;
        }
        if (oldestPriceMax && symbol.oldestPrice) {
            const year = new Date(symbol.oldestPrice).getFullYear();
            if (year > parseInt(oldestPriceMax)) return false;
        }

        if (favoritesOnly && !symbol.isFavorite) return false;
        
        // Rating filters with ratedOnly logic
        if (ratedOnly) {
            // Strict mode: only show rated items that match the filters
            if (symbol.userRating == null) return false;
            if (ratingMin && symbol.userRating < parseInt(ratingMin)) return false;
            if (ratingMax && symbol.userRating > parseInt(ratingMax)) return false;
        } else {
            // Lenient mode: treat non-rated as rating=0
            const effectiveRating = symbol.userRating ?? 0;
            if (ratingMin && effectiveRating < parseInt(ratingMin)) return false;
            if (ratingMax && effectiveRating > parseInt(ratingMax)) return false;
        }

        return true;
    });

    // Sort the filtered results
    const sortedSymbols = [...matchedSymbols].sort((a, b) => {
        const aVal = a[sortColumn];
        const bVal = b[sortColumn];
        
        // Handle null/undefined
        if (aVal == null && bVal == null) return 0;
        if (aVal == null) return 1;
        if (bVal == null) return -1;
        
        // Compare values
        let comparison = 0;
        if (typeof aVal === 'string' && typeof bVal === 'string') {
            comparison = aVal.localeCompare(bVal);
        } else if (typeof aVal === 'number' && typeof bVal === 'number') {
            comparison = aVal - bVal;
        } else {
            comparison = String(aVal).localeCompare(String(bVal));
        }
        
        return sortDirection === 'asc' ? comparison : -comparison;
    });

    // Paginate the sorted results
    const totalPages = Math.ceil(sortedSymbols.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedSymbols = sortedSymbols.slice(startIndex, endIndex);

    // Handle column header click for sorting
    const handleSort = (column: keyof Symbol) => {
        if (sortColumn === column) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            setSortColumn(column);
            setSortDirection('asc');
        }
    };

    // Reset to page 1 when search changes
    useEffect(() => {
        setCurrentPage(1);
    }, [searchTerm]);

    if (loading) {
        return (
            <div className="max-w-7xl mx-auto">
                <div className="form-card">
                    <p className="text-gray-600 text-center py-8">Loading...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="max-w-7xl mx-auto">
                <div className="form-card">
                    <p className="text-red-600 text-center py-8">Error: {error}</p>
                </div>
            </div>
        );
    }

    // Get unique exchanges, countries and sectors for dropdowns
    const exchanges = Array.from(new Set(symbols.map(s => s.exchange).filter((e): e is string => !!e))).sort();
    const countries = Array.from(new Set(symbols.map(s => s.country).filter((c): c is string => !!c))).sort();
    const sectors = Array.from(new Set(symbols.map(s => s.sector).filter((s): s is string => !!s))).sort();

    return (
        <div className="max-w-7xl mx-auto">
            <div className="mb-4">
                <p className="text-gray-600 text-sm mb-3">{description}</p>
                
                {/* Filters */}
                <div className="grid grid-cols-4 gap-2 mb-2">
                    <input
                        type="text"
                        placeholder="Ticker or company name..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
                    />
                    <MultiSelect
                        options={exchanges}
                        selected={exchangeFilter}
                        onChange={setExchangeFilter}
                        placeholder="All Exchanges"
                    />
                    <MultiSelect
                        options={countries}
                        selected={countryFilter}
                        onChange={setCountryFilter}
                        placeholder="All Countries"
                    />
                    <MultiSelect
                        options={sectors}
                        selected={sectorFilter}
                        onChange={setSectorFilter}
                        placeholder="All Sectors"
                    />
                </div>

                <div className="grid grid-cols-6 gap-2">
                    <select value={mcapMin} onChange={(e) => setMcapMin(e.target.value)} className="px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500">
                        <option value="">MCap Min</option>
                        <option value="0">$0</option>
                        <option value="0.001">$1M</option>
                        <option value="0.01">$10M</option>
                        <option value="0.1">$100M</option>
                        <option value="1">$1B</option>
                        <option value="10">$10B</option>
                        <option value="100">$100B</option>
                        <option value="1000">$1T</option>
                    </select>
                    <select value={mcapMax} onChange={(e) => setMcapMax(e.target.value)} className="px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500">
                        <option value="">MCap Max</option>
                        <option value="0.001">$1M</option>
                        <option value="0.01">$10M</option>
                        <option value="0.1">$100M</option>
                        <option value="1">$1B</option>
                        <option value="10">$10B</option>
                        <option value="100">$100B</option>
                        <option value="1000">$1T</option>
                    </select>
                    <select value={inceptionMin} onChange={(e) => setInceptionMin(e.target.value)} className="px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500">
                        <option value="">Inception Min</option>
                        {Array.from({ length: 2025 - 1900 + 1 }, (_, i) => 1900 + i).reverse().map(year => (
                            <option key={year} value={year}>{year}</option>
                        ))}
                    </select>
                    <select value={inceptionMax} onChange={(e) => setInceptionMax(e.target.value)} className="px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500">
                        <option value="">Inception Max</option>
                        {Array.from({ length: 2025 - 1900 + 1 }, (_, i) => 1900 + i).reverse().map(year => (
                            <option key={year} value={year}>{year}</option>
                        ))}
                    </select>
                    <select value={oldestPriceMin} onChange={(e) => setOldestPriceMin(e.target.value)} className="px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500">
                        <option value="">Oldest Price Min</option>
                        {Array.from({ length: 2025 - 1900 + 1 }, (_, i) => 1900 + i).reverse().map(year => (
                            <option key={year} value={year}>{year}</option>
                        ))}
                    </select>
                    <select value={oldestPriceMax} onChange={(e) => setOldestPriceMax(e.target.value)} className="px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500">
                        <option value="">Oldest Price Max</option>
                        {Array.from({ length: 2025 - 1900 + 1 }, (_, i) => 1900 + i).reverse().map(year => (
                            <option key={year} value={year}>{year}</option>
                        ))}
                    </select>
                </div>
                <div className="grid grid-cols-4 gap-2 mt-2">
                    <select value={ratingMin} onChange={(e) => setRatingMin(e.target.value)} className="px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500">
                        <option value="">Rating Min</option>
                        {[-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5].map(r => (
                            <option key={r} value={r}>{r > 0 ? `+${r}` : r}</option>
                        ))}
                    </select>
                    <select value={ratingMax} onChange={(e) => setRatingMax(e.target.value)} className="px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500">
                        <option value="">Rating Max</option>
                        {[-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5].map(r => (
                            <option key={r} value={r}>{r > 0 ? `+${r}` : r}</option>
                        ))}
                    </select>
                    <label className="flex items-center gap-2 text-sm px-2 py-1 border border-gray-300 rounded bg-white">
                        <input type="checkbox" checked={ratedOnly} onChange={(e) => setRatedOnly(e.target.checked)} className="rounded" />
                        <span>📊 Rated only</span>
                    </label>
                    <label className="flex items-center gap-2 text-sm px-2 py-1 border border-gray-300 rounded bg-white">
                        <input type="checkbox" checked={favoritesOnly} onChange={(e) => setFavoritesOnly(e.target.checked)} className="rounded" />
                        <span>⭐ Favorites only</span>
                    </label>
                    <button
                        onClick={() => {
                            setSearchTerm('');
                            setExchangeFilter([]);
                            setCountryFilter([]);
                            setSectorFilter([]);
                            setMcapMin('');
                            setMcapMax('');
                            setInceptionMin('');
                            setInceptionMax('');
                            setOldestPriceMin('');
                            setOldestPriceMax('');
                            setFavoritesOnly(false);
                            setRatingMin('');
                            setRatingMax('');
                            setRatedOnly(false);
                        }}
                        className="px-2 py-1 text-sm border border-gray-300 rounded bg-white hover:bg-gray-50"
                    >
                        Reset Filters
                    </button>
                </div>
            </div>

            <div className="form-card">
                {/* Pagination - Top */}
                <div className="px-4 py-2 flex items-center justify-between border-b border-gray-200 bg-gray-50">
                    <div className="text-xs text-gray-700">
                        Page {currentPage} of {totalPages} ({startIndex + 1}-{Math.min(endIndex, sortedSymbols.length)} of {sortedSymbols.length.toLocaleString()})
                    </div>
                    <div className="flex gap-1">
                        <button onClick={() => setCurrentPage(1)} disabled={currentPage === 1} className="px-2 py-1 text-xs border rounded disabled:opacity-50">First</button>
                        <button onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1} className="px-2 py-1 text-xs border rounded disabled:opacity-50">Prev</button>
                        <button onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages} className="px-2 py-1 text-xs border rounded disabled:opacity-50">Next</button>
                        <button onClick={() => setCurrentPage(totalPages)} disabled={currentPage === totalPages} className="px-2 py-1 text-xs border rounded disabled:opacity-50">Last</button>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 text-xs">
                        <thead className="bg-gray-50">
                            <tr>
                                <th onClick={() => handleSort('isFavorite')} className="px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase w-8 cursor-pointer hover:bg-gray-100">☆ {sortColumn === 'isFavorite' && (sortDirection === 'asc' ? '↑' : '↓')}</th>
                                <th onClick={() => handleSort('userRating')} className="px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase w-12 cursor-pointer hover:bg-gray-100">Rating {sortColumn === 'userRating' && (sortDirection === 'asc' ? '↑' : '↓')}</th>
                                <th onClick={() => handleSort('ticker')} className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase w-24 cursor-pointer hover:bg-gray-100">Symbol {sortColumn === 'ticker' && (sortDirection === 'asc' ? '↑' : '↓')}</th>
                                <th onClick={() => handleSort('exchange')} className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase w-16 cursor-pointer hover:bg-gray-100">Exch {sortColumn === 'exchange' && (sortDirection === 'asc' ? '↑' : '↓')}</th>
                                <th onClick={() => handleSort('name')} className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase max-w-xs cursor-pointer hover:bg-gray-100">Company {sortColumn === 'name' && (sortDirection === 'asc' ? '↑' : '↓')}</th>
                                <th onClick={() => handleSort('country')} className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase w-12 cursor-pointer hover:bg-gray-100">Ctry {sortColumn === 'country' && (sortDirection === 'asc' ? '↑' : '↓')}</th>
                                <th onClick={() => handleSort('sector')} className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase w-32 cursor-pointer hover:bg-gray-100">Sector {sortColumn === 'sector' && (sortDirection === 'asc' ? '↑' : '↓')}</th>
                                <th onClick={() => handleSort('inception')} className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase w-16 cursor-pointer hover:bg-gray-100">Incept {sortColumn === 'inception' && (sortDirection === 'asc' ? '↑' : '↓')}</th>
                                <th onClick={() => handleSort('oldestPrice')} className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase w-16 cursor-pointer hover:bg-gray-100">Price {sortColumn === 'oldestPrice' && (sortDirection === 'asc' ? '↑' : '↓')}</th>
                                <th onClick={() => handleSort('marketCap')} className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase w-16 cursor-pointer hover:bg-gray-100">MCap {sortColumn === 'marketCap' && (sortDirection === 'asc' ? '↑' : '↓')}</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {paginatedSymbols.map((symbol) => (
                                <tr
                                    key={symbol.ticker}
                                    className="hover:bg-gray-50 transition-colors cursor-pointer"
                                    onClick={() => onOpenSymbol?.(symbol.ticker)}
                                >
                                    <td className="px-2 py-1 text-center" onClick={(e) => toggleFavorite(symbol.ticker, e)}>
                                        <span className={`cursor-pointer text-xl hover:scale-125 inline-block transition-transform ${symbol.isFavorite === true ? 'text-yellow-500' : 'text-gray-300'}`}>
                                            {symbol.isFavorite === true ? '★' : '☆'}
                                        </span>
                                    </td>
                                    <td className="px-2 py-1 text-center">
                                        {symbol.userRating != null ? (
                                            <span className={`font-mono ${getRatingColor(symbol.userRating)}`}>{symbol.userRating > 0 ? '+' : ''}{symbol.userRating}</span>
                                        ) : (
                                            <span className="text-gray-300">-</span>
                                        )}
                                    </td>
                                    <td className="px-2 py-1 whitespace-nowrap font-bold text-gray-900">{symbol.ticker}</td>
                                    <td className="px-2 py-1 whitespace-nowrap text-gray-500">{symbol.exchange || '-'}</td>
                                    <td className="px-2 py-1 text-gray-900 truncate max-w-xs" title={symbol.name || ''}>{symbol.name || '-'}</td>
                                    <td className="px-2 py-1 whitespace-nowrap text-gray-500">{symbol.country || '-'}</td>
                                    <td className="px-2 py-1 text-gray-500 truncate max-w-[8rem]" title={symbol.sector || ''}>{symbol.sector || '-'}</td>
                                    <td className="px-2 py-1 whitespace-nowrap text-gray-500">{formatYear(symbol.inception)}</td>
                                    <td className="px-2 py-1 whitespace-nowrap text-gray-500">{formatYear(symbol.oldestPrice)}</td>
                                    <td className="px-2 py-1 whitespace-nowrap text-gray-500 font-mono">{formatMarketCap(symbol.marketCap)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Pagination - Bottom */}
                <div className="px-4 py-2 flex items-center justify-between border-t border-gray-200 bg-gray-50">
                    <div className="text-xs text-gray-700">
                        Page {currentPage} of {totalPages} ({startIndex + 1}-{Math.min(endIndex, sortedSymbols.length)} of {sortedSymbols.length.toLocaleString()})
                    </div>
                    <div className="flex gap-1">
                        <button onClick={() => setCurrentPage(1)} disabled={currentPage === 1} className="px-2 py-1 text-xs border rounded disabled:opacity-50">First</button>
                        <button onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1} className="px-2 py-1 text-xs border rounded disabled:opacity-50">Prev</button>
                        <button onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages} className="px-2 py-1 text-xs border rounded disabled:opacity-50">Next</button>
                        <button onClick={() => setCurrentPage(totalPages)} disabled={currentPage === totalPages} className="px-2 py-1 text-xs border rounded disabled:opacity-50">Last</button>
                    </div>
                </div>
            </div>
        </div>
    );
}
