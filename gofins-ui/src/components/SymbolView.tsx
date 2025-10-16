import SymbolDetail from './SymbolDetail';

interface SymbolViewProps {
    data?: { symbol: string };
    onCloseTab?: () => void;
}

export default function SymbolView({ data, onCloseTab }: SymbolViewProps) {
    const symbol = data?.symbol;

    if (!symbol) {
        return (
            <div className="max-w-7xl mx-auto">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <p className="text-gray-600">No symbol selected</p>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <SymbolDetail symbol={symbol} onClose={onCloseTab} />
            </div>
        </div>
    );
}
