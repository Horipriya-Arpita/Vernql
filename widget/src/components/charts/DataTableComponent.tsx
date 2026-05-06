'use client'

import React from 'react'

// Cap visible rows so the table stays compact inside a widget embed.
// Any overflow is summarised in the footer.
const ROW_LIMIT = 10

interface DataTableComponentProps {
  data: Array<Record<string, unknown>>
  columns: string[]
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '–'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'number') return value.toLocaleString()
  return String(value)
}

export default function DataTableComponent({ data, columns }: DataTableComponentProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-20 text-xs text-gray-400 dark:text-gray-500">
        No data available
      </div>
    )
  }

  const visibleRows = data.slice(0, ROW_LIMIT)
  const hiddenCount = data.length - visibleRows.length

  return (
    // Scrollable container — no outer card since SQLResult is the container
    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
      <table className="w-full text-xs">
        <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
          <tr>
            {columns.map((col) => (
              <th
                key={col}
                className="px-3 py-2 text-left font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap"
              >
                {col.replace(/_/g, ' ')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
          {visibleRows.map((row, rowIdx) => (
            <tr
              key={rowIdx}
              className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
            >
              {columns.map((col) => (
                <td
                  key={col}
                  className="px-3 py-2 text-gray-900 dark:text-gray-100 whitespace-nowrap"
                >
                  {formatValue(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      <div className="px-3 py-1.5 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
        {hiddenCount > 0
          ? `Showing ${visibleRows.length} of ${data.length} rows`
          : `${data.length} ${data.length === 1 ? 'row' : 'rows'}`}
      </div>
    </div>
  )
}