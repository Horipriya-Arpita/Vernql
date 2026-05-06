'use client'

import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface LineChartComponentProps {
  data: Array<Record<string, unknown>>
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

export default function LineChartComponent({ data }: LineChartComponentProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-xs text-gray-400 dark:text-gray-500">
        No data available
      </div>
    )
  }

  const columns = Object.keys(data[0])
  const xAxisKey = columns[0]
  const yAxisKeys = columns.slice(1).filter((col) => typeof data[0][col] === 'number')

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey={xAxisKey}
          tick={{ fontSize: 10, fill: 'currentColor' }}
          stroke="currentColor"
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 10, fill: 'currentColor' }}
          stroke="currentColor"
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            fontSize: 11,
            borderRadius: '6px',
            border: '1px solid #e5e7eb',
          }}
        />
        {yAxisKeys.length > 1 && <Legend wrapperStyle={{ fontSize: 10 }} />}
        {yAxisKeys.map((key, i) => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}