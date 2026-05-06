'use client'

import React from 'react'
import { Sparkles } from 'lucide-react'
import MetricCard from './MetricCard'
import BarChartComponent from './BarChartComponent'
import LineChartComponent from './LineChartComponent'
import PieChartComponent from './PieChartComponent'
import DataTableComponent from './DataTableComponent'
import type { VisualizationData } from '@/lib/types'

interface VisualizationRendererProps {
  visualizationData: VisualizationData
  aiInsight?: string | null
}

export default function VisualizationRenderer({
  visualizationData,
  aiInsight,
}: VisualizationRendererProps) {
  const renderChart = () => {
    switch (visualizationData.type) {
      case 'metric':
        return (
          <MetricCard
            value={visualizationData.value}
            label={visualizationData.label}
          />
        )
      case 'bar':
        return <BarChartComponent data={visualizationData.data} />
      case 'line':
        return <LineChartComponent data={visualizationData.data} />
      case 'pie':
        return <PieChartComponent data={visualizationData.data} />
      case 'table':
        return (
          <DataTableComponent
            data={visualizationData.data}
            columns={visualizationData.columns ?? Object.keys(visualizationData.data[0] ?? {})}
          />
        )
    }
  }

  return (
    <div className="space-y-2 pt-1">
      {/* AI Insight — compact banner suited for the widget's narrow width */}
      {aiInsight && (
        <div className="flex items-start gap-2 rounded-lg bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border border-blue-200 dark:border-blue-800 px-3 py-2">
          <Sparkles className="h-3.5 w-3.5 flex-shrink-0 text-blue-500 dark:text-blue-400 mt-0.5" />
          <p className="text-xs text-blue-800 dark:text-blue-200 leading-relaxed">
            {aiInsight}
          </p>
        </div>
      )}

      {/* Chart / table */}
      {renderChart()}
    </div>
  )
}