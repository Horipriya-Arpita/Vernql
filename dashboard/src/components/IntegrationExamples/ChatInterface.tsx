'use client'

import { useState } from 'react'
import { Send, Loader2, TrendingUp, BarChart3, Table, PieChart } from 'lucide-react'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  visualization?: any
  timestamp: Date
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: 'Hi! Ask me anything about your data. For example: "Show me top 10 customers" or "What were sales last month?"',
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      // Call your API route that integrates with Vernql
      const response = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input })
      })

      const data = await response.json()

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.visualization?.ai_insight || 'Here are your results:',
        visualization: data.visualization,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error processing your request.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const getChartIcon = (chartType: string) => {
    switch (chartType) {
      case 'bar': return <BarChart3 className="w-4 h-4" />
      case 'line': return <TrendingUp className="w-4 h-4" />
      case 'pie': return <PieChart className="w-4 h-4" />
      case 'table': return <Table className="w-4 h-4" />
      default: return <BarChart3 className="w-4 h-4" />
    }
  }

  return (
    <div className="flex flex-col h-[600px] bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="bg-blue-600 text-white px-6 py-4 rounded-t-lg">
        <h2 className="text-xl font-semibold">Ask Your Data</h2>
        <p className="text-sm text-blue-100">Powered by Vernql</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-3 ${
                message.type === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="text-sm">{message.content}</p>

              {/* Visualization */}
              {message.visualization && (
                <div className="mt-3 bg-white rounded-lg p-4">
                  {/* Chart Type Badge */}
                  <div className="flex items-center gap-2 mb-3">
                    {getChartIcon(message.visualization.chart_type)}
                    <span className="text-xs font-medium text-gray-600 uppercase">
                      {message.visualization.chart_type} Chart
                    </span>
                  </div>

                  {/* Metric Display */}
                  {message.visualization.chart_type === 'metric' && (
                    <div className="text-center py-4">
                      <div className="text-4xl font-bold text-blue-600">
                        {message.visualization.visualization_data.value}
                      </div>
                      <div className="text-sm text-gray-600 mt-2">
                        {message.visualization.visualization_data.label}
                      </div>
                    </div>
                  )}

                  {/* Table Display */}
                  {message.visualization.chart_type === 'table' && (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200 text-sm">
                        <thead className="bg-gray-50">
                          <tr>
                            {message.visualization.visualization_data.columns.map((col: string) => (
                              <th
                                key={col}
                                className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase"
                              >
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {message.visualization.visualization_data.data.slice(0, 5).map((row: any, idx: number) => (
                            <tr key={idx}>
                              {message.visualization.visualization_data.columns.map((col: string) => (
                                <td key={col} className="px-3 py-2 whitespace-nowrap text-gray-900">
                                  {row[col]}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {message.visualization.row_count > 5 && (
                        <p className="text-xs text-gray-500 mt-2 text-center">
                          Showing 5 of {message.visualization.row_count} rows
                        </p>
                      )}
                    </div>
                  )}

                  {/* Bar/Pie/Line Charts - Simple representation */}
                  {['bar', 'pie', 'line'].includes(message.visualization.chart_type) && (
                    <div className="text-center py-8 text-gray-500">
                      <p className="text-sm">
                        {message.visualization.chart_type.charAt(0).toUpperCase() +
                         message.visualization.chart_type.slice(1)} chart data ready
                      </p>
                      <p className="text-xs mt-1">
                        {message.visualization.row_count} data points
                      </p>
                    </div>
                  )}

                  {/* AI Insight */}
                  {message.visualization.ai_insight && (
                    <div className="mt-3 bg-blue-50 border-l-4 border-blue-400 p-3">
                      <p className="text-sm text-blue-900">
                        💡 <strong>Insight:</strong> {message.visualization.ai_insight}
                      </p>
                    </div>
                  )}
                </div>
              )}

              <p className="text-xs mt-1 opacity-70">
                {message.timestamp.toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </p>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-3">
              <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question about your data..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>

        {/* Example questions */}
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="text-xs text-gray-500">Try:</span>
          {[
            'Show me top 10 customers',
            'Total sales last month',
            'Active users count'
          ].map((example) => (
            <button
              key={example}
              onClick={() => setInput(example)}
              className="text-xs text-blue-600 hover:text-blue-800 hover:underline"
              disabled={loading}
            >
              "{example}"
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
