import { useState } from 'react';
import {
    ChartBarIcon,
    PlusIcon,
    HeartIcon,
    BeakerIcon,
    XMarkIcon,
    BuildingLibraryIcon,
    FunnelIcon,
    DocumentChartBarIcon
} from '@heroicons/react/24/outline';
import TabContent from './TabContent';

interface Tab {
    id: string;
    type: 'analyses' | 'favorites' | 'stocks' | 'analysis' | 'symbol' | 'create';
    title: string;
    data?: any;
    isPermanent?: boolean;
}

export default function Layout() {
    const [tabs, setTabs] = useState<Tab[]>([
        { id: 'analyses', type: 'analyses', title: 'Analyses', isPermanent: true },
        { id: 'stocks', type: 'stocks', title: 'Stocks', isPermanent: true },
        { id: 'favorites', type: 'favorites', title: 'Favorites', isPermanent: true }
    ]);
    const [activeTabId, setActiveTabId] = useState<string>('analyses');

    const getTabIcon = (type: Tab['type']) => {
        switch (type) {
            case 'analyses': return FunnelIcon;
            case 'stocks': return BuildingLibraryIcon;
            case 'favorites': return HeartIcon;
            case 'analysis': return BeakerIcon;
            case 'symbol': return DocumentChartBarIcon;
            case 'create': return PlusIcon;
            default: return ChartBarIcon;
        }
    };

    const openAnalysis = (analysisId: string, analysisName: string) => {
        console.log('openAnalysis called:', analysisId, analysisName);
        const existingTab = tabs.find(tab => tab.id === analysisId);
        if (existingTab) {
            console.log('Existing tab found, switching to it');
            setActiveTabId(analysisId);
        } else {
            console.log('Creating new analysis tab');
            const newTab: Tab = {
                id: analysisId,
                type: 'analysis',
                title: analysisName,
                data: { id: analysisId }
            };
            setTabs(prev => [...prev, newTab]);
            // Set active tab after adding to array
            setActiveTabId(analysisId);
        }
    };

    const openSymbol = (symbol: string) => {
        const symbolTabId = `symbol-${symbol}`;
        const existingTab = tabs.find(tab => tab.id === symbolTabId);
        if (existingTab) {
            setActiveTabId(symbolTabId);
        } else {
            const newTab: Tab = {
                id: symbolTabId,
                type: 'symbol',
                title: symbol,
                data: { symbol }
            };
            setTabs([...tabs, newTab]);
            setActiveTabId(symbolTabId);
        }
    };

    const openCreateTab = () => {
        const createTabId = `create-${Date.now()}`;
        const newTab: Tab = {
            id: createTabId,
            type: 'create',
            title: 'Create Analysis'
        };
        setTabs([...tabs, newTab]);
        setActiveTabId(createTabId);
    };

    const closeTab = (tabId: string) => {
        console.log('closeTab called:', tabId, 'currentActive:', activeTabId);

        setTabs(currentTabs => {
            const tabToClose = currentTabs.find(tab => tab.id === tabId);
            if (tabToClose?.isPermanent) {
                console.log('Cannot close permanent tab');
                return currentTabs;
            }

            const newTabs = currentTabs.filter(tab => tab.id !== tabId);
            console.log('Tabs after close:', newTabs.map(t => t.id));

            // Only change active tab if we're closing the currently active tab
            if (activeTabId === tabId && newTabs.length > 0) {
                const newActiveTab = newTabs[newTabs.length - 1].id;
                console.log('Closing active tab, switching to:', newActiveTab);
                setActiveTabId(newActiveTab);
            } else {
                console.log('Not closing active tab, keeping current active tab:', activeTabId);
            }

            return newTabs;
        });
    };

    const activeTab = tabs.find(tab => tab.id === activeTabId);

    return (
        <div className="flex flex-col h-screen bg-gray-50 p-4">
            {/* Header */}
            <div className="bg-white border-b border-gray-300 shadow-md rounded-t-lg">
                <div className="flex items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">
                            FINS
                        </h1>
                        <p className="text-sm text-gray-600 font-medium">Financial Information & Notes System</p>
                    </div>
                </div>
            </div>

            {/* Tab Navigation */}
            <div className="bg-white border-b border-gray-200 px-6">
                <nav className="flex gap-2">
                    {tabs.map((tab) => {
                        const Icon = getTabIcon(tab.type);
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTabId(tab.id)}
                                className={`tab-button ${activeTabId === tab.id ? 'active' : ''}`}
                            >
                                <Icon className="w-4 h-4 flex-shrink-0" />
                                <span>{tab.title}</span>
                                {!tab.isPermanent && (
                                    <span
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            closeTab(tab.id);
                                        }}
                                        className="tab-close-button"
                                    >
                                        <XMarkIcon className="w-3 h-3" />
                                    </span>
                                )}
                            </button>
                        );
                    })}
                </nav>
            </div>

            {/* Main Content */}
            <div className="flex-1 mt-4 overflow-auto bg-gray-50">
                {activeTab && (
                    <TabContent
                        tabType={activeTab.type}
                        data={activeTab.data}
                        onOpenAnalysis={openAnalysis}
                        onOpenSymbol={openSymbol}
                        onOpenCreate={openCreateTab}
                        onCloseTab={() => closeTab(activeTab.id)}
                    />
                )}
            </div>
        </div>
    );
}
