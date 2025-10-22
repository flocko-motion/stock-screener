import SymbolList from './SymbolList';

interface FavoritesViewProps {
    onOpenSymbol?: (symbol: string) => void;
}

export default function FavoritesView({ onOpenSymbol }: FavoritesViewProps) {
    return (
        <SymbolList 
            endpoint="/api/symbols/active"
            description="Your favorite stocks"
            onOpenSymbol={onOpenSymbol}
            defaultFavoritesOnly={true}
        />
    );
}
