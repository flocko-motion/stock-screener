import SymbolList from './SymbolList';

interface FavoritesViewProps {
    onOpenSymbol?: (symbol: string) => void;
}

export default function FavoritesView({ onOpenSymbol }: FavoritesViewProps) {
    return (
        <SymbolList 
            endpoint="/api/symbols/favorites"
            description=""
            onOpenSymbol={onOpenSymbol}
        />
    );
}
