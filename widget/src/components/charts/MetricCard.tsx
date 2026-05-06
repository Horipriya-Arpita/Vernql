'use client'

import React from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface MetricCardProps {
  value: number | string
  label: string
  format?: 'number' | 'currency' | 'percentage'
  trend?: { value: number; direction: 'up' | 'down' }
}

export default function MetricCard({ value, label, format = 'number', trend }: MetricCardProps) {
  const formatValue = (val: number | string): string => {
    if (typeof val === 'string') return val
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 2,
        }).format(val)
      case 'percentage':
        return `${val.toFixed(1)}%`
      default:
        return new Intl.NumberFormat('en-US').format(val)
    }
  }

  return (
    // No outer card border — SQLResult provides the container
    <div className="flex items-center justify-between py-3 px-1">
      <div>
        <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1 uppercase tracking-wide">
          {label}
        </p>
        <p className="text-2xl font-bold text-gray-900 dark:text-white">
          {formatValue(value)}
        </p>
      </div>

      {trend && (
        <div className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${
          trend.direction === 'up'
            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
            : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
        }`}>
          {trend.direction === 'up'
            ? <TrendingUp className="w-3 h-3" />
            : <TrendingDown className="w-3 h-3" />}
          {Math.abs(trend.value)}%
        </div>
      )}
    </div>
  )
}