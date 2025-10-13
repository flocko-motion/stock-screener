import { useState } from 'react';
import { analysisApi } from '../services/api';
import type { CreateAnalysisRequest } from '../services/api';

interface CreateAnalysisProps {
    onAnalysisCreated?: (id: string, name: string) => void;
    onCancel?: () => void;
}

export default function CreateAnalysis({ onAnalysisCreated, onCancel }: CreateAnalysisProps) {
    const [name, setName] = useState('');
    const [interval, setInterval] = useState('weekly');
    const [timeFrom, setTimeFrom] = useState('2009');
    const [timeTo, setTimeTo] = useState('');
    const [mcapMin, setMcapMin] = useState('100000000');
    const [inceptionMax, setInceptionMax] = useState('');
    const [histMin, setHistMin] = useState('-80');
    const [histMax, setHistMax] = useState('80');
    const [histBins, setHistBins] = useState('100');
    const [error, setError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!name.trim()) {
            setError('Analysis name is required');
            return;
        }

        setIsSubmitting(true);
        setError('');

        try {
            const request: CreateAnalysisRequest = {
                name: name.trim(),
                interval,
                time_from: timeFrom || undefined,
                time_to: timeTo || undefined,
                hist_bins: histBins ? parseInt(histBins) : undefined,
                hist_min: histMin ? parseFloat(histMin) : undefined,
                hist_max: histMax ? parseFloat(histMax) : undefined,
                mcap_min: mcapMin || undefined,
                inception_max: inceptionMax || undefined,
            };

            const result = await analysisApi.create(request);
            console.log('Analysis created:', result);

            // Open the new analysis tab first
            if (onAnalysisCreated) {
                console.log('Opening analysis tab:', result.package_id, name.trim());
                onAnalysisCreated(result.package_id, name.trim());

                // Close the create tab after React has processed the state updates
                if (onCancel) {
                    requestAnimationFrame(() => {
                        requestAnimationFrame(() => {
                            onCancel();
                        });
                    });
                }
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create analysis');
            setIsSubmitting(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto mt-4">
            <div className="form-card p-8">
                <div className="mb-8">
                    <p className="text-gray-600 font-medium">Configure and start a new stock screening analysis</p>
                </div>

                <form className="space-y-8" onSubmit={handleSubmit}>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div className="md:col-span-2">
                            <label className="block text-sm font-semibold text-gray-700 mb-3">
                                Analysis Name <span className="text-red-500">*</span>
                            </label>
                            <input
                                type="text"
                                className={`form-input w-full ${error ? 'border-red-500' : ''}`}
                                placeholder="e.g., Tech Stocks Q4 2024"
                                value={name}
                                onChange={(e) => {
                                    setName(e.target.value);
                                    if (error) setError('');
                                }}
                            />
                            {error && (
                                <p className="mt-2 text-sm text-red-600">{error}</p>
                            )}
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">
                                Start Date (YYYY/YYYY-MM/YYYY-MM-DD)
                            </label>
                            <input
                                type="text"
                                className="form-input w-full"
                                placeholder="2009"
                                value={timeFrom}
                                onChange={(e) => setTimeFrom(e.target.value)}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">
                                End Date (YYYY/YYYY-MM/YYYY-MM-DD)
                            </label>
                            <input
                                type="text"
                                className="form-input w-full"
                                placeholder="Leave empty for first of current month"
                                value={timeTo}
                                onChange={(e) => setTimeTo(e.target.value)}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">
                                Min Market Cap
                            </label>
                            <select
                                className="form-input w-full"
                                value={mcapMin}
                                onChange={(e) => setMcapMin(e.target.value)}
                            >
                                <option value="0">$0</option>
                                <option value="1000000">$1M</option>
                                <option value="10000000">$10M</option>
                                <option value="100000000">$100M</option>
                                <option value="1000000000">$1B</option>
                                <option value="10000000000">$10B</option>
                                <option value="100000000000">$100B</option>
                                <option value="1000000000000">$1T</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">
                                Max Inception Date (YYYY/YYYY-MM/YYYY-MM-DD)
                            </label>
                            <input
                                type="text"
                                className="form-input w-full"
                                placeholder="Leave empty for no filter"
                                value={inceptionMax}
                                onChange={(e) => setInceptionMax(e.target.value)}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">
                                Time Period
                            </label>
                            <select
                                className="form-input w-full"
                                value={interval}
                                onChange={(e) => setInterval(e.target.value)}
                            >
                                <option value="weekly">Weekly</option>
                                <option value="daily">Daily</option>
                                <option value="monthly">Monthly</option>
                            </select>
                        </div>


                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">
                                Histogram Min, Max, Bins
                            </label>
                            <div className="flex space-x-3">
                                <input
                                    type="number"
                                    className="form-input flex-1 min-w-0"
                                    placeholder="Min %"
                                    value={histMin}
                                    onChange={(e) => setHistMin(e.target.value)}
                                />
                                <input
                                    type="number"
                                    className="form-input flex-1 min-w-0"
                                    placeholder="Max %"
                                    value={histMax}
                                    onChange={(e) => setHistMax(e.target.value)}
                                />
                                <input
                                    type="number"
                                    className="form-input flex-1 min-w-0"
                                    placeholder="Bins"
                                    value={histBins}
                                    onChange={(e) => setHistBins(e.target.value)}
                                />
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
                        <button
                            type="button"
                            className="form-button-secondary"
                            disabled={isSubmitting}
                            onClick={onCancel}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="form-button-primary"
                            disabled={isSubmitting}
                        >
                            {isSubmitting ? 'Creating...' : 'Create'}
                        </button>
                    </div>
                </form>
            </div >
        </div >
    );
}
