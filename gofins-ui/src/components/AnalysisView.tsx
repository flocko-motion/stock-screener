import { BeakerIcon, ChartBarIcon } from '@heroicons/react/24/outline';

interface AnalysisViewProps {
    data?: any;
}

export default function AnalysisView({ data: _data }: AnalysisViewProps) {
    return (
        <div className="max-w-7xl mx-auto mt-4">
            <div className="form-card p-8">
                <div className="mb-8">
                    <p className="text-gray-600 font-medium">View analysis results and charts</p>
                </div>

                <div className="text-center py-12">
                    <ChartBarIcon className="icon-fixed text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Analysis in Progress</h3>
                    <p className="text-gray-500">This analysis is currently being processed. Results will appear here when complete.</p>
                </div>
            </div>
        </div>
    );
}
