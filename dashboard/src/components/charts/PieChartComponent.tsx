'use client';

import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface PieChartComponentProps {
  data: Array<{ name: string; value: number }>;
  className?: string;
}

export default function PieChartComponent({
  data,
  className = ''
}: PieChartComponentProps) {
  if (!data || data.length === 0) {
    return (
      <div className={`flex items-center justify-center h-64 bg-gray-50 dark:bg-gray-800 rounded-lg ${className}`}>
        <p className="text-gray-500 dark:text-gray-400">No data available</p>
      </div>
    );
  }

  // Color palette
  const colors = [
    '#3b82f6', // blue
    '#10b981', // green
    '#f59e0b', // amber
    '#ef4444', // red
    '#8b5cf6', // purple
    '#ec4899', // pink
    '#06b6d4', // cyan
    '#f97316', // orange
  ];

  // Calculate percentage for each slice
  const total = data.reduce((sum, item) => sum + item.value, 0);

  // Custom label renderer
  const renderLabel = (entry: any) => {
    const percent = ((entry.value / total) * 100).toFixed(1);
    return `${percent}%`;
  };

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
      <ResponsiveContainer width="100%" height={400}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={renderLabel}
            outerRadius={120}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--tooltip-bg)',
              border: '1px solid var(--tooltip-border)',
              borderRadius: '0.5rem',
              color: 'var(--tooltip-text)'
            }}
            formatter={(value) => {
              const num = typeof value === 'number' ? value : Number(value);
              const percent = ((num / total) * 100).toFixed(1);
              return [num.toLocaleString(), `${percent}%`];
            }}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value, entry: any) => {
              const percent = ((entry.payload.value / total) * 100).toFixed(1);
              return `${value} (${percent}%)`;
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}