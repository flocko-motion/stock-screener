import { ChartBarIcon } from '@heroicons/react/24/outline';

interface SymbolViewProps {
    data?: any;
}

export default function SymbolView({ data: _data }: SymbolViewProps) {
    return (
        <div className="max-w-7xl mx-auto">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="mb-6">
                    <p className="text-gray-600 font-medium">Detailed analysis for this symbol will be displayed here</p>
                </div>

                <div className="text-center py-12">
                    <ChartBarIcon className="icon-fixed text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Symbol Details</h3>
                    <p className="text-gray-500">Detailed analysis for this symbol will be displayed here.</p>
                </div>
            </div>
        </div>
    );
}
