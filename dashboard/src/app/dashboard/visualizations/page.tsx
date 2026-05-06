'use client';

import React, { useState } from 'react';
import useSWR from 'swr';
import { apiClient } from '@/lib/api-client';
import { BarChart3, Share2, Eye, Trash2, Sparkles, Calendar } from 'lucide-react';
import { VisualizationRenderer } from '@/components/charts';
import toast from 'react-hot-toast';

export default function VisualizationsPage() {
  const [selectedViz, setSelectedViz] = useState<string | null>(null);

  // Fetch visualizations list
  const { data: vizList, error, mutate } = useSWR(
    'visualizations',
    () => apiClient.listVisualizations()
  );

  // Fetch selected visualization details
  const { data: vizDetails } = useSWR(
    selectedViz ? `visualization-${selectedViz}` : null,
    () => selectedViz ? apiClient.getVisualization(selectedViz) : null
  );

  const handleShare = async (vizId: string, currentIsPublic: boolean) => {
    try {
      await apiClient.updateVisualizationSharing(vizId, !currentIsPublic);
      toast.success(currentIsPublic ? 'Visualization made private' : 'Visualization made public');
      mutate();
    } catch (error: any) {
      toast.error(error.message || 'Failed to update sharing settings');
    }
  };

  const handleDelete = async (vizId: string) => {
    if (!confirm('Are you sure you want to delete this visualization?')) return;

    try {
      await apiClient.deleteVisualization(vizId);
      toast.success('Visualization deleted');
      if (selectedViz === vizId) {
        setSelectedViz(null);
      }
      mutate();
    } catch (error: any) {
      toast.error(error.message || 'Failed to delete visualization');
    }
  };

  const getChartIcon = (chartType: string) => {
    const iconClass = "w-5 h-5";
    switch (chartType) {
      case 'bar':
        return <BarChart3 className={iconClass} />;
      case 'line':
        return <BarChart3 className={iconClass} />;
      case 'pie':
        return <BarChart3 className={iconClass} />;
      default:
        return <BarChart3 className={iconClass} />;
    }
  };

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-800 dark:text-red-200">
            Failed to load visualizations: {error.message}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Visualizations
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          View and manage your query visualizations with AI-powered insights
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Visualizations List */}
        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                All Visualizations
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {vizList?.total || 0} total
              </p>
            </div>

            <div className="divide-y divide-gray-200 dark:divide-gray-700 max-h-[600px] overflow-y-auto">
              {!vizList ? (
                <div className="p-8 text-center">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">Loading...</p>
                </div>
              ) : vizList.results.length === 0 ? (
                <div className="p-8 text-center">
                  <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    No visualizations yet
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    Execute queries and send results to create visualizations
                  </p>
                </div>
              ) : (
                vizList.results.map((viz) => (
                  <div
                    key={viz.id}
                    className={`p-4 cursor-pointer transition-colors ${
                      selectedViz === viz.id
                        ? 'bg-blue-50 dark:bg-blue-900/20'
                        : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                    }`}
                    onClick={() => setSelectedViz(viz.id)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getChartIcon(viz.chart_type)}
                        <span className="text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">
                          {viz.chart_type}
                        </span>
                      </div>
                      {viz.is_public && (
                        <Share2 className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                      )}
                    </div>

                    {viz.ai_insight && (
                      <div className="flex items-start gap-2 mb-2">
                        <Sparkles className="w-4 h-4 text-purple-600 dark:text-purple-400 flex-shrink-0 mt-0.5" />
                        <p className="text-xs text-gray-700 dark:text-gray-300 line-clamp-2">
                          {viz.ai_insight}
                        </p>
                      </div>
                    )}

                    <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                      <span>{viz.row_count} rows</span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {new Date(viz.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Visualization Display */}
        <div className="lg:col-span-2">
          {!selectedViz ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12 text-center">
              <BarChart3 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No visualization selected
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Select a visualization from the list to view it here
              </p>
            </div>
          ) : !vizDetails ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12 text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-4">
                Loading visualization...
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Actions Bar */}
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {vizDetails.chart_type.charAt(0).toUpperCase() + vizDetails.chart_type.slice(1)} Chart
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {vizDetails.row_count} rows × {vizDetails.column_count} columns
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleShare(vizDetails.id, vizDetails.is_public)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        vizDetails.is_public
                          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                          : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                      }`}
                    >
                      <Share2 className="w-4 h-4" />
                      {vizDetails.is_public ? 'Public' : 'Private'}
                    </button>

                    <button
                      onClick={() => window.open(vizDetails.visualization_url, '_blank')}
                      className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 rounded-lg text-sm font-medium hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    >
                      <Eye className="w-4 h-4" />
                      View
                    </button>

                    <button
                      onClick={() => handleDelete(vizDetails.id)}
                      className="flex items-center gap-2 px-4 py-2 bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 rounded-lg text-sm font-medium hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </button>
                  </div>
                </div>
              </div>

              {/* Visualization */}
              <VisualizationRenderer
                visualizationData={vizDetails.visualization_data}
                aiInsight={vizDetails.ai_insight}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}