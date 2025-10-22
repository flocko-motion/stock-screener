import AnalysesList from './AnalysesList';
import CreateAnalysis from './CreateAnalysis';
import AnalysisView from './AnalysisView';
import SymbolView from './SymbolView';
import SymbolList from './SymbolList';
import ErrorsView from './ErrorsView';
import NotesView from './NotesView';
import FavoritesView from './FavoritesView';

interface TabContentProps {
    tabType: 'analyses' | 'stocks' | 'analysis' | 'symbol' | 'create' | 'errors' | 'notes' | 'favorites';
    data?: any;
    onOpenAnalysis?: (id: string, name: string) => void;
    onOpenSymbol?: (symbol: string) => void;
    onOpenCreate?: () => void;
    onCloseTab?: () => void;
}

export default function TabContent({ tabType, data, onOpenAnalysis, onOpenSymbol, onOpenCreate, onCloseTab }: TabContentProps) {
    switch (tabType) {
        case 'analyses':
            return <AnalysesList onOpenAnalysis={onOpenAnalysis} onOpenCreate={onOpenCreate} />;
        case 'stocks':
            return (
                <SymbolList 
                    endpoint="/api/symbols/active"
                    description="All actively trading stocks in the database"
                    onOpenSymbol={onOpenSymbol}
                />
            );
        case 'create':
            return <CreateAnalysis onAnalysisCreated={onOpenAnalysis} onCancel={onCloseTab} />;
        case 'analysis':
            return <AnalysisView data={data} />;
        case 'symbol':
            return <SymbolView data={data} onCloseTab={onCloseTab} />;
        case 'errors':
            return <ErrorsView />;
        case 'notes':
            return <NotesView onOpenSymbol={onOpenSymbol} />;
        case 'favorites':
            return <FavoritesView onOpenSymbol={onOpenSymbol} />;
        default:
            return <div>Unknown tab type</div>;
    }
}