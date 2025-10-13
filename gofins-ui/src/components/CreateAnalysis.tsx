import { PlusIcon } from '@heroicons/react/24/outline';

export default function CreateAnalysis() {
    return (
        <div className="max-w-4xl mx-auto mt-4">
            <div className="form-card p-8">
                <div className="mb-8">
                    <p className="text-gray-600 font-medium">Configure and start a new stock screening analysis</p>
                </div>

                <form className="space-y-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">
                                Analysis Name
                            </label>
                            <input
                                type="text"
                                className="form-input w-full"
                                placeholder="e.g., Tech Stocks Q4 2024"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">
                                Time Period
                            </label>
                            <select className="form-input w-full">
                                <option value="weekly">Weekly</option>
                                <option value="daily">Daily</option>
                                <option value="monthly">Monthly</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">
                                Start Date
                            </label>
                            <input
                                type="text"
                                className="form-input w-full"
                                placeholder="2009"
                                defaultValue="2009"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">
                                End Date
                            </label>
                            <input
                                type="text"
                                className="form-input w-full"
                                placeholder="2024-12-01"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">
                                Min Market Cap
                            </label>
                            <select className="form-input w-full">
                                <option value="100000000">$100M</option>
                                <option value="1000000000">$1B</option>
                                <option value="10000000000">$10B</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">
                                Histogram Range
                            </label>
                            <div className="flex space-x-3">
                                <input
                                    type="number"
                                    className="form-input flex-1"
                                    placeholder="Min %"
                                    defaultValue="-80"
                                />
                                <input
                                    type="number"
                                    className="form-input flex-1"
                                    placeholder="Max %"
                                    defaultValue="80"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
                        <button
                            type="button"
                            className="form-button-secondary"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="form-button-primary"
                        >
                            Create Analysis
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
