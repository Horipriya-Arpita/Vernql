'use client';

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface LineChartComponentProps {
  data: Array<Record<string, any>>;
  className?: string;
}

export default function LineChartComponent({
  data,
  className = ''
}: LineChartComponentProps) {
  if (!data || data.length === 0) {
    return (
      <div className={`flex items-center justify-center h-64 bg-gray-50 dark:bg-gray-800 rounded-lg ${className}`}>
        <p className="text-gray-500 dark:text-gray-400">No data available</p>
      </div>
    );
  }

  // Extract column names from first row
  const columns = Object.keys(data[0]);

  // Identify x-axis (first column, usually temporal)
  const xAxisKey = columns[0];

  // Identify y-axis keys (remaining numeric columns)
  const yAxisKeys = columns.slice(1).filter(col => {
    const value = data[0][col];
    return typeof value === 'number';
  });

  // Color palette for multiple lines
  const colors = [
    '#3b82f6', // blue
    '#10b981', // green
    '#f59e0b', // amber
    '#ef4444', // red
    '#8b5cf6', // purple
    '#ec4899', // pink
  ];

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
          <XAxis
            dataKey={xAxisKey}
            className="text-sm"
            stroke="currentColor"
            tick={{ fill: 'currentColor' }}
          />
          <YAxis
            className="text-sm"
            stroke="currentColor"
            tick={{ fill: 'currentColor' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--tooltip-bg)',
              border: '1px solid var(--tooltip-border)',
              borderRadius: '0.5rem',
              color: 'var(--tooltip-text)'
            }}
          />
          {yAxisKeys.length > 1 && <Legend />}
          {yAxisKeys.map((key, index) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={colors[index % colors.length]}
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}