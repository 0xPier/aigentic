"""Reporting Agent for dashboard and report generation."""

import matplotlib.pyplot as plt
import pandas as pd
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

from src.agents.base import LLMAgent, AgentContext, AgentResult


class ReportingAgent(LLMAgent):
    """Agent specialized in creating reports and dashboards."""
    
    def __init__(self):
        super().__init__(
            name="reporting",
            description="Generates dashboards, reports, and data visualizations",
            capabilities=[
                "dashboard_creation",
                "report_generation",
                "data_visualization",
                "kpi_tracking",
                "analytics_reporting"
            ]
        )
    
    def get_required_integrations(self) -> List[str]:
        """Reporting agent doesn't require specific integrations."""
        return []
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute reporting task."""
        start_time = datetime.utcnow()
        
        try:
            # Parse reporting requirements
            report_spec = await self._parse_reporting_requirements(context.query)
            
            # Generate report data
            report_data = await self._generate_report_data(report_spec, context)
            
            # Create visualizations
            visualizations = await self._create_visualizations(report_data, report_spec)
            
            # Generate report document
            report_file = await self._generate_report_document(report_data, visualizations, report_spec)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            output_files = visualizations.copy()
            if report_file:
                output_files.append(report_file)
            
            result = AgentResult(
                success=True,
                data={
                    "report_spec": report_spec,
                    "report_data": report_data,
                    "visualizations": visualizations,
                    "report_type": report_spec.get("type", "standard"),
                    "metrics_count": len(report_data.get("metrics", []))
                },
                message="Report generated successfully",
                execution_time=execution_time,
                output_files=output_files
            )
            
            # Save to memory
            self.save_memory(
                memory_type="reporting",
                content={
                    "report_type": report_spec.get("type", "standard"),
                    "metrics": list(report_data.get("metrics", {}).keys()),
                    "visualizations_created": len(visualizations)
                },
                context_tags=["reporting", "analytics"],
                relevance_score=0.8
            )
            
            self.log_execution(context, result)
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AgentResult(
                success=False,
                data={},
                message=f"Report generation failed: {str(e)}",
                execution_time=execution_time,
                error=str(e)
            )
            
            self.log_execution(context, result)
            return result
    
    async def _parse_reporting_requirements(self, query: str) -> Dict[str, Any]:
        """Parse reporting requirements from query."""
        system_prompt = """
        You are a reporting expert. Parse the requirements and determine:
        1. Type of report (dashboard, analytics, performance, financial, etc.)
        2. Key metrics and KPIs to include
        3. Time period for analysis
        4. Data sources needed
        5. Visualization types preferred
        6. Target audience
        
        Respond in JSON format:
        {
            "type": "performance_report",
            "metrics": ["revenue", "conversion_rate", "customer_satisfaction"],
            "time_period": "last_30_days",
            "data_sources": ["sales_data", "customer_data"],
            "visualizations": ["line_chart", "bar_chart", "pie_chart"],
            "audience": "management"
        }
        """
        
        prompt = f"Parse reporting requirements for: {query}"
        
        try:
            response = await self.call_llm(prompt, system_prompt, temperature=0.3)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Reporting parsing failed: {e}")
            return {
                "type": "standard_report",
                "metrics": ["performance", "usage", "satisfaction"],
                "time_period": "last_30_days",
                "data_sources": ["system_data"],
                "visualizations": ["bar_chart", "line_chart"],
                "audience": "general"
            }
    
    async def _generate_report_data(self, spec: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Generate or collect data for the report."""
        # Check if previous results contain data
        data_sources = {}
        if context.previous_results:
            for result_key, result_data in context.previous_results.items():
                if result_data.get("success") and "data" in result_data:
                    data_sources[result_key] = result_data["data"]
        
        # Generate mock data for demonstration
        metrics = {}
        for metric in spec.get("metrics", []):
            metrics[metric] = self._generate_metric_data(metric, spec.get("time_period", "last_30_days"))
        
        return {
            "metrics": metrics,
            "data_sources": data_sources,
            "time_period": spec.get("time_period", "last_30_days"),
            "generated_at": datetime.utcnow().isoformat(),
            "summary": await self._generate_data_summary(metrics)
        }
    
    def _generate_metric_data(self, metric: str, time_period: str) -> Dict[str, Any]:
        """Generate real metric data from database."""
        from src.database.connection import mongodb
        import asyncio
        
        async def get_real_metrics():
            db = mongodb.database
            end_date = datetime.now()
            
            # Calculate date range based on time_period
            if time_period == "last_30_days":
                start_date = end_date - timedelta(days=30)
                dates = pd.date_range(start=start_date, end=end_date, freq='D')
            elif time_period == "last_12_months":
                start_date = end_date - timedelta(days=365)
                dates = pd.date_range(start=start_date, end=end_date, freq='M')
            else:
                start_date = end_date - timedelta(days=7)
                dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Query database for real metrics based on metric type
            if metric in ["revenue", "sales"]:
                # Query financial data from database
                pipeline = [
                    {"$match": {"date": {"$gte": start_date, "$lte": end_date}, "type": metric}},
                    {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}}, "value": {"$sum": "$amount"}}},
                    {"$sort": {"_id": 1}}
                ]
                cursor = db.financial_metrics.aggregate(pipeline)
                results = await cursor.to_list(length=None)
            elif metric in ["conversion_rate", "satisfaction"]:
                # Query performance metrics
                pipeline = [
                    {"$match": {"date": {"$gte": start_date, "$lte": end_date}, "metric": metric}},
                    {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}}, "value": {"$avg": "$value"}}},
                    {"$sort": {"_id": 1}}
                ]
                cursor = db.performance_metrics.aggregate(pipeline)
                results = await cursor.to_list(length=None)
            else:
                # Query general metrics
                pipeline = [
                    {"$match": {"date": {"$gte": start_date, "$lte": end_date}, "metric": metric}},
                    {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}}, "value": {"$sum": "$value"}}},
                    {"$sort": {"_id": 1}}
                ]
                cursor = db.general_metrics.aggregate(pipeline)
                results = await cursor.to_list(length=None)
            
            # Convert results to lists
            if results:
                values = [r["value"] for r in results]
                result_dates = [r["_id"] for r in results]
            else:
                # If no data in database, return empty structure
                values = [0] * len(dates)
                result_dates = dates.strftime('%Y-%m-%d').tolist()
            
            return {
                "dates": result_dates,
                "values": values,
                "current_value": float(values[-1]) if values else 0.0,
                "previous_value": float(values[-2]) if len(values) > 1 else 0.0,
                "trend": "up" if len(values) > 1 and values[-1] > values[0] else "down",
                "change_percent": float((values[-1] - values[0]) / values[0] * 100) if values and values[0] != 0 else 0.0
            }
        
        # Run async function in sync context
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(get_real_metrics())
        except RuntimeError:
            # If no event loop, create one
            return asyncio.run(get_real_metrics())
    
    async def _generate_data_summary(self, metrics: Dict[str, Any]) -> str:
        """Generate a summary of the report data."""
        system_prompt = """
        You are a data analyst. Create a concise summary of the metrics data highlighting:
        1. Key trends and patterns
        2. Notable changes or anomalies
        3. Overall performance assessment
        4. Key insights for decision making
        
        Keep it professional and actionable.
        """
        
        metrics_summary = {}
        for metric_name, metric_data in metrics.items():
            metrics_summary[metric_name] = {
                "current_value": metric_data.get("current_value"),
                "trend": metric_data.get("trend"),
                "change_percent": metric_data.get("change_percent")
            }
        
        prompt = f"""
        Metrics data summary:
        {json.dumps(metrics_summary, indent=2)}
        
        Provide a concise analysis summary.
        """
        
        try:
            return await self.call_llm(prompt, system_prompt, temperature=0.3)
        except Exception as e:
            self.logger.error(f"Summary generation failed: {e}")
            return "Report data analysis completed. Key metrics show mixed performance with opportunities for improvement."
    
    async def _create_visualizations(self, report_data: Dict[str, Any], spec: Dict[str, Any]) -> List[str]:
        """Create visualizations for the report."""
        visualizations = []
        
        try:
            # Create uploads directory
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create visualizations for each metric
            for metric_name, metric_data in report_data.get("metrics", {}).items():
                viz_file = await self._create_metric_visualization(
                    metric_name, metric_data, timestamp
                )
                if viz_file:
                    visualizations.append(viz_file)
            
            # Create summary dashboard
            dashboard_file = await self._create_dashboard(report_data, timestamp)
            if dashboard_file:
                visualizations.append(dashboard_file)
            
        except Exception as e:
            self.logger.error(f"Visualization creation failed: {e}")
        
        return visualizations
    
    async def _create_metric_visualization(self, metric_name: str, metric_data: Dict[str, Any], timestamp: str) -> str:
        """Create visualization for a single metric."""
        try:
            dates = pd.to_datetime(metric_data.get("dates", []))
            values = metric_data.get("values", [])
            
            plt.figure(figsize=(12, 6))
            plt.plot(dates, values, marker='o', linewidth=2, markersize=4)
            plt.title(f'{metric_name.replace("_", " ").title()} Over Time', fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel(metric_name.replace("_", " ").title(), fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            filename = f"metric_{metric_name}_{timestamp}.png"
            filepath = os.path.join("uploads", filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"Metric visualization failed for {metric_name}: {e}")
            return None
    
    async def _create_dashboard(self, report_data: Dict[str, Any], timestamp: str) -> str:
        """Create a summary dashboard with multiple metrics."""
        try:
            metrics = report_data.get("metrics", {})
            if not metrics:
                return None
            
            # Create subplots
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Performance Dashboard', fontsize=20, fontweight='bold')
            
            metric_items = list(metrics.items())
            
            for i, (metric_name, metric_data) in enumerate(metric_items[:4]):
                row = i // 2
                col = i % 2
                ax = axes[row, col]
                
                dates = pd.to_datetime(metric_data.get("dates", []))
                values = metric_data.get("values", [])
                
                ax.plot(dates, values, marker='o', linewidth=2)
                ax.set_title(metric_name.replace("_", " ").title(), fontweight='bold')
                ax.grid(True, alpha=0.3)
                ax.tick_params(axis='x', rotation=45)
            
            # Hide empty subplots
            for i in range(len(metric_items), 4):
                row = i // 2
                col = i % 2
                axes[row, col].set_visible(False)
            
            plt.tight_layout()
            
            filename = f"dashboard_{timestamp}.png"
            filepath = os.path.join("uploads", filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"Dashboard creation failed: {e}")
            return None
    
    async def _generate_report_document(self, report_data: Dict[str, Any], visualizations: List[str], spec: Dict[str, Any]) -> str:
        """Generate a comprehensive report document."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"report_{timestamp}.md"
            filepath = os.path.join("uploads", filename)
            
            # Create markdown report
            report_content = f"""# {spec.get('type', 'Report').replace('_', ' ').title()}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Time Period:** {spec.get('time_period', 'N/A')}
**Audience:** {spec.get('audience', 'General')}

## Executive Summary

{report_data.get('summary', 'Report analysis completed successfully.')}

## Key Metrics

"""
            
            # Add metrics details
            for metric_name, metric_data in report_data.get("metrics", {}).items():
                current_value = metric_data.get("current_value", 0)
                change_percent = metric_data.get("change_percent", 0)
                trend = metric_data.get("trend", "stable")
                
                report_content += f"""### {metric_name.replace('_', ' ').title()}

- **Current Value:** {current_value:.2f}
- **Change:** {change_percent:+.1f}%
- **Trend:** {trend.title()}

"""
            
            # Add visualizations section
            if visualizations:
                report_content += "\n## Visualizations\n\n"
                for viz_file in visualizations:
                    viz_name = os.path.basename(viz_file).replace('.png', '').replace('_', ' ').title()
                    report_content += f"- {viz_name}: `{viz_file}`\n"
            
            # Add recommendations
            report_content += f"""
## Recommendations

Based on the analysis, consider the following actions:

1. **Monitor Key Trends:** Focus on metrics showing significant changes
2. **Address Declining Areas:** Investigate metrics with downward trends
3. **Leverage Strong Performance:** Build on areas showing positive growth
4. **Regular Review:** Schedule periodic reviews to track progress

## Next Steps

1. Review findings with stakeholders
2. Implement recommended actions
3. Schedule follow-up analysis
4. Monitor key performance indicators

---
*Report generated by AI Consultancy Platform*
"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"Report document generation failed: {e}")
            return None
