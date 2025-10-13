import { useState } from 'react';
import {
    ChartBarIcon,
    PlusIcon,
    HeartIcon,
    BeakerIcon,
    XMarkIcon
} from '@heroicons/react/24/outline';
import TabContent from './TabContent';

interface Tab {
    id: string;
    type: 'analyses' | 'favorites' | 'analysis' | 'symbol' | 'create';
    title: string;
    data?: any;
    isPermanent?: boolean;
}

export default function Layout() {
    const [tabs, setTabs] = useState<Tab[]>([
        { id: 'analyses', type: 'analyses', title: 'Analyses', isPermanent: true },
        { id: 'favorites', type: 'favorites', title: 'Favorites', isPermanent: true }
    ]);
    const [activeTabId, setActiveTabId] = useState<string>('analyses');

    const getTabIcon = (type: Tab['type']) => {
        switch (type) {
            case 'analyses': return ChartBarIcon;
            case 'favorites': return HeartIcon;
            case 'analysis': return BeakerIcon;
            case 'symbol': return ChartBarIcon;
            case 'create': return PlusIcon;
            default: return ChartBarIcon;
        }
    };

    const openAnalysis = (analysisId: string, analysisName: string) => {
        const existingTab = tabs.find(tab => tab.id === analysisId);
        if (existingTab) {
            setActiveTabId(analysisId);
        } else {
            const newTab: Tab = {
                id: analysisId,
                type: 'analysis',
                title: analysisName,
                data: { analysisId }
            };
            setTabs([...tabs, newTab]);
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
        const tabToClose = tabs.find(tab => tab.id === tabId);
        if (tabToClose?.isPermanent) return; // Don't close permanent tabs

        const newTabs = tabs.filter(tab => tab.id !== tabId);
        setTabs(newTabs);
        if (activeTabId === tabId && newTabs.length > 0) {
            setActiveTabId(newTabs[newTabs.length - 1].id);
        }
    };

    const activeTab = tabs.find(tab => tab.id === activeTabId);

    return (
        <div className="flex flex-col h-screen bg-gray-50 p-4">
            {/* Header */}
            <div className="bg-white border-b border-gray-300 shadow-md rounded-t-lg">
                <div className="flex items-center px-8 py-6">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">
                            <span className="text-blue-600">F</span>INS
                        </h1>
                        <p className="text-sm text-gray-600 font-medium">Financial Information & Notes System</p>
                    </div>
                </div>
            </div>

            {/* Tab Navigation */}
            <div className="bg-white border-b border-gray-200 px-6 pt-3">
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
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            closeTab(tab.id);
                                        }}
                                        className="tab-close-button"
                                    >
                                        <XMarkIcon className="w-3 h-3" />
                                    </button>
                                )}
                            </button>
                        );
                    })}
                </nav>
            </div>

            {/* Main Content */}
            <div className="flex-1 p-6 overflow-auto bg-gray-50 rounded-b-lg">
                {activeTab && (
                    <TabContent
                        tabType={activeTab.type}
                        data={activeTab.data}
                        onOpenAnalysis={openAnalysis}
                        onOpenSymbol={openSymbol}
                        onOpenCreate={openCreateTab}
                    />
                )}
            </div>
        </div>
    );
}
