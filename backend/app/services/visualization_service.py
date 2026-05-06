"""
Visualization Service
Handles chart type auto-detection and AI insights generation
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
import structlog

logger = structlog.get_logger()


class ChartType:
    """Available chart types"""
    METRIC = "metric"
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    TABLE = "table"


class VisualizationService:
    """
    Service for auto-detecting appropriate chart types and generating visualizations
    """

    @staticmethod
    def detect_chart_type(results: List[Dict[str, Any]]) -> str:
        """
        Auto-detect the best chart type based on result structure

        Logic:
        - Single row, single column with numeric value → METRIC
        - Single column with categories + one numeric column → PIE
        - Date/time column + numeric columns → LINE
        - Category column + numeric columns → BAR
        - Everything else → TABLE

        Args:
            results: List of result rows (dicts)

        Returns:
            Chart type string (metric, bar, line, pie, table)
        """
        if not results:
            return ChartType.TABLE

        # Get column info from first row
        first_row = results[0]
        column_names = list(first_row.keys())
        column_count = len(column_names)
        row_count = len(results)

        logger.info(
            "Detecting chart type",
            row_count=row_count,
            column_count=column_count,
            columns=column_names
        )

        # Single metric (1 row, 1 column, numeric)
        if row_count == 1 and column_count == 1:
            value = list(first_row.values())[0]
            if isinstance(value, (int, float)):
                logger.info("Detected chart type: METRIC")
                return ChartType.METRIC

        # Analyze column types
        column_types = VisualizationService._analyze_column_types(results)
        numeric_columns = [col for col, typ in column_types.items() if typ == "numeric"]
        categorical_columns = [col for col, typ in column_types.items() if typ == "categorical"]
        temporal_columns = [col for col, typ in column_types.items() if typ == "temporal"]

        logger.info(
            "Column analysis",
            numeric=numeric_columns,
            categorical=categorical_columns,
            temporal=temporal_columns
        )

        # Pie chart: 1 categorical + 1 numeric, reasonable row count
        if (len(categorical_columns) == 1 and
            len(numeric_columns) == 1 and
            2 <= row_count <= 10):
            logger.info("Detected chart type: PIE")
            return ChartType.PIE

        # Line chart: temporal column + numeric columns
        if temporal_columns and numeric_columns:
            logger.info("Detected chart type: LINE")
            return ChartType.LINE

        # Bar chart: categorical column + numeric columns
        if categorical_columns and numeric_columns:
            logger.info("Detected chart type: BAR")
            return ChartType.BAR

        # Default to table
        logger.info("Detected chart type: TABLE (default)")
        return ChartType.TABLE

    @staticmethod
    def _analyze_column_types(results: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Analyze column types from result data

        Returns:
            Dict mapping column name to type (numeric, categorical, temporal)
        """
        if not results:
            return {}

        first_row = results[0]
        column_types = {}

        for column_name in first_row.keys():
            # Sample first few non-null values
            sample_values = []
            for row in results[:10]:  # Sample first 10 rows
                value = row.get(column_name)
                if value is not None:
                    sample_values.append(value)

            if not sample_values:
                column_types[column_name] = "categorical"
                continue

            # Check if temporal
            if VisualizationService._is_temporal(sample_values):
                column_types[column_name] = "temporal"
            # Check if numeric
            elif VisualizationService._is_numeric(sample_values):
                column_types[column_name] = "numeric"
            # Default to categorical
            else:
                column_types[column_name] = "categorical"

        return column_types

    @staticmethod
    def _is_numeric(values: List[Any]) -> bool:
        """Check if values are numeric"""
        numeric_count = sum(1 for v in values if isinstance(v, (int, float)) and not isinstance(v, bool))
        return numeric_count / len(values) >= 0.8  # 80% threshold

    @staticmethod
    def _is_temporal(values: List[Any]) -> bool:
        """Check if values are temporal (date/datetime)"""
        temporal_count = sum(1 for v in values if isinstance(v, (datetime, date)))
        if temporal_count / len(values) >= 0.8:
            return True

        # Check for date-like strings
        if all(isinstance(v, str) for v in values):
            date_keywords = ['date', 'time', 'year', 'month', 'day']
            # This is a simple heuristic - could be enhanced
            return any(keyword in str(values[0]).lower() for keyword in date_keywords)

        return False

    @staticmethod
    async def generate_ai_insight(
        query: str,
        results: List[Dict[str, Any]],
        chart_type: str,
        ai_client
    ) -> Optional[str]:
        """
        Generate AI insight about the query results

        Args:
            query: Original natural language query
            results: Query results
            chart_type: Detected chart type
            ai_client: AI client for generating insights

        Returns:
            One-line insight string or None if generation fails
        """
        try:
            # Prepare summary of results
            row_count = len(results)

            if row_count == 0:
                return "No results found for this query."

            # Create a concise summary for the AI
            if row_count == 1 and len(results[0]) == 1:
                value = list(results[0].values())[0]
                summary = f"Single value: {value}"
            else:
                # Include first few rows as sample
                sample_rows = results[:3]
                summary = f"{row_count} rows returned. Sample: {sample_rows}"

            # Generate insight
            prompt = f"""Given this query: "{query}"
And these results: {summary}

Generate a single, concise sentence (max 100 characters) that summarizes the key insight from this data.
Focus on the business meaning, not the technical details.
Examples:
- "Sales increased 23% compared to last month"
- "Top 5 customers account for 67% of revenue"
- "Average order value is $145.32"

Insight:"""

            insight = await ai_client.generate_insight(prompt)

            logger.info("Generated AI insight", insight=insight)
            return insight

        except Exception as e:
            logger.error("Failed to generate AI insight", error=str(e))
            return None

    @staticmethod
    def prepare_visualization_data(
        results: List[Dict[str, Any]],
        chart_type: str
    ) -> Dict[str, Any]:
        """
        Prepare data structure optimized for frontend visualization

        Args:
            results: Query results
            chart_type: Chart type

        Returns:
            Prepared data structure for visualization
        """
        if chart_type == ChartType.METRIC:
            # Single value
            value = list(results[0].values())[0] if results else 0
            label = list(results[0].keys())[0] if results else "Value"
            return {
                "type": "metric",
                "value": value,
                "label": label
            }

        elif chart_type == ChartType.PIE:
            # Category + value pairs
            if results:
                category_col = list(results[0].keys())[0]
                value_col = list(results[0].keys())[1]

                return {
                    "type": "pie",
                    "data": [
                        {
                            "name": str(row[category_col]),
                            "value": float(row[value_col]) if row[value_col] else 0
                        }
                        for row in results
                    ]
                }
            return {"type": "pie", "data": []}

        elif chart_type in [ChartType.LINE, ChartType.BAR]:
            # X-axis + Y-axis data
            return {
                "type": chart_type,
                "data": results  # Pass through - frontend will handle
            }

        else:  # TABLE
            return {
                "type": "table",
                "data": results,
                "columns": list(results[0].keys()) if results else []
            }