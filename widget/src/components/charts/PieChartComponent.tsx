'use client'

import React from 'react'
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface PieChartComponentProps {
  data: Array<{ name: string; value: number }>
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316']

export default function PieChartComponent({ data }: PieChartComponentProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-xs text-gray-400 dark:text-gray-500">
        No data available
      </div>
    )
  }

  const total = data.reduce((sum, item) => sum + item.value, 0)

  const renderLabel = (entry: { value: number }) => {
    const pct = ((entry.value / total) * 100).toFixed(0)
    return `${pct}%`
  }

  return (
    // outerRadius 80 instead of 120 to fit a compact embed height of 240px
    <ResponsiveContainer width="100%" height={240}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="45%"
          labelLine={false}
          label={renderLabel}
          outerRadius={80}
          dataKey="value"
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ fontSize: 11, borderRadius: '6px', border: '1px solid #e5e7eb' }}
          formatter={(value: number) => [value.toLocaleString(), `${((value / total) * 100).toFixed(1)}%`]}
        />
        <Legend
          verticalAlign="bottom"
          height={28}
          wrapperStyle={{ fontSize: 10 }}
          formatter={(value, entry: { payload?: { value: number } }) => {
            const pct = entry.payload ? ((entry.payload.value / total) * 100).toFixed(1) : '0'
            return `${value} (${pct}%)`
          }}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}