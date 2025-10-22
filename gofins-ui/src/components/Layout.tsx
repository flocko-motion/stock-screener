import { useState, useEffect } from 'react';
import {
    ChartBarIcon,
    PlusIcon,
    BeakerIcon,
    XMarkIcon,
    BuildingLibraryIcon,
    FunnelIcon,
    DocumentChartBarIcon,
    ExclamationTriangleIcon,
    DocumentTextIcon,
    StarIcon,
    UserIcon
} from '@heroicons/react/24/outline';
import TabContent from './TabContent';

interface Tab {
    id: string;
    type: 'analyses' | 'stocks' | 'analysis' | 'symbol' | 'create' | 'errors' | 'notes' | 'favorites';
    title: string;
    data?: any;
    isPermanent?: boolean;
}

interface User {
    id: string;
    name: string;
    createdAt: string;
    isAdmin: boolean;
}

export default function Layout() {
    const [allTabs] = useState<Tab[]>([
        { id: 'favorites', type: 'favorites', title: 'Favorites', isPermanent: true },
        { id: 'notes', type: 'notes', title: 'Notes', isPermanent: true },
        { id: 'stocks', type: 'stocks', title: 'Stocks', isPermanent: true },
        { id: 'analyses', type: 'analyses', title: 'Analyses', isPermanent: true },
        { id: 'errors', type: 'errors', title: 'Errors', isPermanent: true }
    ]);
    const [tabs, setTabs] = useState<Tab[]>([]);
    const [activeTabId, setActiveTabId] = useState<string>('stocks');
    const [previousTabId, setPreviousTabId] = useState<string>('stocks');
    const [user, setUser] = useState<User | null>(null);

    // Fetch current user on mount
    useEffect(() => {
        fetch('http://localhost:8080/api/user')
            .then(res => res.json())
            .then(data => setUser(data))
            .catch(err => console.error('Failed to fetch user:', err));
    }, []);

    // Filter tabs based on user permissions
    useEffect(() => {
        if (!user) return;
        
        // Show errors tab only to admin
        const visibleTabs = allTabs.filter(tab => {
            if (tab.type === 'errors') {
                return user.isAdmin;
            }
            return true;
        });
        
        setTabs(visibleTabs);
    }, [user, allTabs]);

    const getTabIcon = (type: Tab['type']) => {
        switch (type) {
            case 'analyses': return FunnelIcon;
            case 'stocks': return BuildingLibraryIcon;
            case 'analysis': return BeakerIcon;
            case 'symbol': return DocumentChartBarIcon;
            case 'create': return PlusIcon;
            case 'errors': return ExclamationTriangleIcon;
            case 'notes': return DocumentTextIcon;
            case 'favorites': return StarIcon;
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
            setPreviousTabId(activeTabId);
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
        setPreviousTabId(activeTabId);
        setActiveTabId(createTabId);
    };

    const closeTab = (tabId: string) => {
        console.log('closeTab called:', tabId, 'currentActive:', activeTabId, 'previous:', previousTabId);

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
                // Try to go back to previous tab if it still exists
                const targetTab = newTabs.find(t => t.id === previousTabId) ? previousTabId : newTabs[newTabs.length - 1].id;
                console.log('Closing active tab, switching to:', targetTab);
                setActiveTabId(targetTab);
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
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">
                            FINS
                        </h1>
                        <p className="text-sm text-gray-600 font-medium">Financial Information & Notes System</p>
                    </div>
                    {user && (
                        <div className="flex items-center gap-2 px-4 py-2 bg-gray-50 rounded-lg border border-gray-200">
                            <UserIcon className="w-5 h-5 text-gray-600" />
                            <span className="text-sm font-medium text-gray-900">{user.name}</span>
                            {user.isAdmin && (
                                <span className="px-2 py-0.5 text-xs font-semibold bg-blue-100 text-blue-800 rounded">
                                    ADMIN
                                </span>
                            )}
                        </div>
                    )}
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
                                onClick={() => {
                                    setPreviousTabId(activeTabId);
                                    setActiveTabId(tab.id);
                                }}
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
