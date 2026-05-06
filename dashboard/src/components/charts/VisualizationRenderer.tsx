'use client';

import React from 'react';
import MetricCard from './MetricCard';
import BarChartComponent from './BarChartComponent';
import LineChartComponent from './LineChartComponent';
import PieChartComponent from './PieChartComponent';
import DataTableComponent from './DataTableComponent';
import { Sparkles } from 'lucide-react';

interface VisualizationData {
  type: 'metric' | 'bar' | 'line' | 'pie' | 'table';
  data: any;
  value?: number | string;
  label?: string;
  columns?: string[];
}

interface VisualizationRendererProps {
  visualizationData: VisualizationData;
  aiInsight?: string | null;
  className?: string;
}

export default function VisualizationRenderer({
  visualizationData,
  aiInsight,
  className = ''
}: VisualizationRendererProps) {
  const renderChart = () => {
    switch (visualizationData.type) {
      case 'metric':
        return (
          <MetricCard
            value={visualizationData.value ?? 0}
            label={visualizationData.label ?? 'Metric'}
          />
        );

      case 'bar':
        return <BarChartComponent data={visualizationData.data} />;

      case 'line':
        return <LineChartComponent data={visualizationData.data} />;

      case 'pie':
        return <PieChartComponent data={visualizationData.data} />;

      case 'table':
        return (
          <DataTableComponent
            data={visualizationData.data}
            columns={visualizationData.columns ?? Object.keys(visualizationData.data[0] ?? {})}
          />
        );

      default:
        return (
          <div className="flex items-center justify-center h-64 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <p className="text-gray-500 dark:text-gray-400">
              Unknown visualization type: {visualizationData.type}
            </p>
          </div>
        );
    }
  };

  return (
    <div className={className}>
      {/* AI Insight Banner */}
      {aiInsight && (
        <div className="mb-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">
                AI Insight
              </p>
              <p className="text-sm text-blue-800 dark:text-blue-200">
                {aiInsight}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Chart */}
      {renderChart()}
    </div>
  );
}