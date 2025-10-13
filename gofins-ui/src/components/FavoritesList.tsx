import { PlusIcon } from '@heroicons/react/24/outline';

interface FavoritesListProps {
    onOpenSymbol?: (symbol: string) => void;
}

export default function FavoritesList({ onOpenSymbol }: FavoritesListProps) {
    const favorites = [
        { symbol: 'AAPL', name: 'Apple Inc.', sector: 'Technology', cagr: 23.5, beta: 1.2, sigma: 18.3 },
        { symbol: 'MSFT', name: 'Microsoft Corporation', sector: 'Technology', cagr: 28.1, beta: 0.9, sigma: 16.7 },
        { symbol: 'NVDA', name: 'NVIDIA Corporation', sector: 'Technology', cagr: 45.2, beta: 1.8, sigma: 35.2 },
        { symbol: 'GOOGL', name: 'Alphabet Inc.', sector: 'Technology', cagr: 19.8, beta: 1.1, sigma: 20.1 },
    ];

    const handleNewList = () => {
        // TODO: Implement create new favorites list
        console.log('Create new favorites list');
    };

    return (
        <div className="max-w-7xl mx-auto">
            <div className="mb-6 flex items-center justify-between">
                <p className="text-gray-600 text-sm">Your saved stock picks and watchlist</p>
                <button
                    onClick={handleNewList}
                    className="form-button-primary flex items-center gap-2"
                >
                    <PlusIcon className="icon-fixed" style={{ width: '16px', height: '16px' }} />
                    <span>New List</span>
                </button>
            </div>

            <div className="form-card">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Symbol
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Company
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Sector
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    CAGR (%)
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    β (Beta)
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    σ (Sigma)
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {favorites.map((stock) => (
                                <tr key={stock.symbol} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center">
                                            <span className="text-sm font-bold text-gray-900">{stock.symbol}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                        {stock.name}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {stock.sector}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-mono">
                                        {stock.cagr.toFixed(1)}%
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-mono">
                                        {stock.beta.toFixed(2)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-mono">
                                        {stock.sigma.toFixed(1)}%
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                        <button
                                            onClick={() => onOpenSymbol?.(stock.symbol)}
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
        </div>
    );
}
