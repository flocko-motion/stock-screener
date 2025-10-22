const API_BASE_URL = 'http://localhost:8080/api';

export interface AnalysisPackage {
    ID: string;
    Name: string;
    CreatedAt: string;
    Interval: string;
    TimeFrom: string;
    TimeTo: string;
    HistBins: number;
    HistMin: number;
    HistMax: number;
    McapMin?: number;
    InceptionMax?: string;
    SymbolCount: number;
    Status: string;
}

export interface AnalysisResult {
    symbol: string;
    mean: number;
    stddev: number;
    min: number;
    max: number;
    inception?: string;
}

export interface SymbolProfile {
    ticker: string;
    exchange?: string;
    name?: string;
    type?: string;
    currency?: string;
    sector?: string;
    industry?: string;
    country?: string;
    description?: string;
    website?: string;
    isin?: string;
    inception?: string;
    oldestPrice?: string;
    isActivelyTrading?: boolean;
    marketCap?: number;
    ath12m?: number;
    currentPriceUsd?: number;
}

export interface CreateAnalysisRequest {
    name: string;
    interval?: string;
    time_from?: string;
    time_to?: string;
    hist_bins?: number;
    hist_min?: number;
    hist_max?: number;
    mcap_min?: string;
    inception_max?: string;
}

export const analysisApi = {
    // List all analyses
    list: async (): Promise<AnalysisPackage[]> => {
        const response = await fetch(`${API_BASE_URL}/analyses`);
        if (!response.ok) {
            throw new Error('Failed to fetch analyses');
        }
        return response.json();
    },

    // Get single analysis
    get: async (id: string): Promise<AnalysisPackage> => {
        const response = await fetch(`${API_BASE_URL}/analysis/${id}`);
        if (!response.ok) {
            throw new Error('Failed to fetch analysis');
        }
        return response.json();
    },

    // Create new analysis
    create: async (data: CreateAnalysisRequest): Promise<{ package_id: string; status: string }> => {
        const response = await fetch(`${API_BASE_URL}/analyses`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        if (!response.ok) {
            throw new Error('Failed to create analysis');
        }
        return response.json();
    },

    // Update analysis (rename)
    update: async (id: string, name: string): Promise<AnalysisPackage> => {
        const response = await fetch(`${API_BASE_URL}/analysis/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name }),
        });
        if (!response.ok) {
            throw new Error('Failed to update analysis');
        }
        return response.json();
    },

    // Delete analysis
    delete: async (id: string): Promise<void> => {
        const response = await fetch(`${API_BASE_URL}/analysis/${id}`, {
            method: 'DELETE',
        });
        if (!response.ok) {
            throw new Error('Failed to delete analysis');
        }
    },

    // Get analysis results
    getResults: async (id: string): Promise<AnalysisResult[]> => {
        const response = await fetch(`${API_BASE_URL}/analysis/${id}/results`);
        if (!response.ok) {
            throw new Error('Failed to fetch analysis results');
        }
        return response.json();
    },

    // Get symbol profile
    getProfile: async (id: string, ticker: string): Promise<SymbolProfile> => {
        const response = await fetch(`${API_BASE_URL}/analysis/${id}/profile/${ticker}`);
        if (!response.ok) {
            throw new Error('Failed to fetch symbol profile');
        }
        return response.json();
    },
};

