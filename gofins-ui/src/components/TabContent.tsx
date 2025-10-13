import AnalysesList from './AnalysesList';
import FavoritesList from './FavoritesList';
import CreateAnalysis from './CreateAnalysis';
import AnalysisView from './AnalysisView';
import SymbolView from './SymbolView';

interface TabContentProps {
    tabType: 'analyses' | 'favorites' | 'analysis' | 'symbol' | 'create';
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
        case 'favorites':
            return <FavoritesList onOpenSymbol={onOpenSymbol} />;
        case 'create':
            return <CreateAnalysis onAnalysisCreated={onOpenAnalysis} onCancel={onCloseTab} />;
        case 'analysis':
            return <AnalysisView data={data} />;
        case 'symbol':
            return <SymbolView data={data} />;
        default:
            return <div>Unknown tab type</div>;
    }
}