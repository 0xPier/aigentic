"""Analysis Agent for data processing and insights generation."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from typing import Dict, Any, List
from datetime import datetime
import json

from src.agents.base import LLMAgent, AgentContext, AgentResult


class AnalysisAgent(LLMAgent):
    """Agent specialized in data analysis and insights generation."""
    
    def __init__(self):
        super().__init__(
            name="analysis",
            description="Processes data, generates insights, and creates statistical analysis",
            capabilities=[
                "data_processing",
                "statistical_analysis",
                "trend_analysis",
                "data_visualization",
                "insights_generation"
            ]
        )
    
    def get_required_integrations(self) -> List[str]:
        """Analysis agent doesn't require specific integrations."""
        return []
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute data analysis task."""
        start_time = datetime.utcnow()
        
        try:
            # Parse analysis requirements
            analysis_spec = await self._parse_analysis_requirements(context.query)
            
            # Get data (from previous results or generate sample data)
            data = self._get_analysis_data(context)
            
            # Perform analysis
            analysis_results = await self._perform_analysis(data, analysis_spec)
            
            # Generate visualizations
            visualizations = await self._create_visualizations(data, analysis_results)
            
            # Generate insights
            insights = await self._generate_insights(analysis_results, context.query)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AgentResult(
                success=True,
                data={
                    "analysis_spec": analysis_spec,
                    "data_summary": self._summarize_data(data),
                    "analysis_results": analysis_results,
                    "insights": insights,
                    "visualizations": visualizations
                },
                message="Data analysis completed successfully",
                execution_time=execution_time,
                output_files=visualizations
            )
            
            # Save analysis to memory
            self.save_memory(
                memory_type="analysis",
                content={
                    "query": context.query,
                    "data_points": len(data) if isinstance(data, list) else "N/A",
                    "key_insights": insights.get("key_findings", [])
                },
                context_tags=["analysis", "data"],
                relevance_score=0.9
            )
            
            self.log_execution(context, result)
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AgentResult(
                success=False,
                data={},
                message=f"Analysis failed: {str(e)}",
                execution_time=execution_time,
                error=str(e)
            )
            
            self.log_execution(context, result)
            return result
    
    async def _parse_analysis_requirements(self, query: str) -> Dict[str, Any]:
        """Parse what type of analysis is needed."""
        system_prompt = """
        You are a data analysis expert. Parse the analysis requirements and determine:
        1. Type of analysis needed (descriptive, predictive, comparative, etc.)
        2. Key metrics to calculate
        3. Visualizations to create
        4. Statistical tests to perform
        
        Respond in JSON format:
        {
            "analysis_type": "descriptive",
            "metrics": ["mean", "median", "std"],
            "visualizations": ["histogram", "scatter_plot"],
            "statistical_tests": ["correlation", "t_test"]
        }
        """
        
        prompt = f"Parse analysis requirements for: {query}"
        
        try:
            response = await self.call_llm(prompt, system_prompt, temperature=0.3)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Analysis parsing failed: {e}")
            return {
                "analysis_type": "descriptive",
                "metrics": ["mean", "median", "count"],
                "visualizations": ["histogram"],
                "statistical_tests": ["basic_stats"]
            }
    
    def _get_analysis_data(self, context: AgentContext) -> Any:
        """Get data for analysis from context or generate sample data."""
        # Check if previous results contain data
        if context.previous_results:
            for result in context.previous_results.values():
                if result.get("success") and "data" in result:
                    return result["data"]
        
        # Generate sample data for demonstration
        np.random.seed(42)
        sample_data = {
            "values": np.random.normal(100, 15, 1000).tolist(),
            "categories": np.random.choice(['A', 'B', 'C'], 1000).tolist(),
            "dates": pd.date_range('2024-01-01', periods=1000, freq='D').strftime('%Y-%m-%d').tolist()
        }
        
        return sample_data
    
    async def _perform_analysis(self, data: Any, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Perform the actual data analysis."""
        results = {}
        
        try:
            if isinstance(data, dict) and "values" in data:
                values = np.array(data["values"])
                
                # Basic statistics
                results["basic_stats"] = {
                    "count": len(values),
                    "mean": float(np.mean(values)),
                    "median": float(np.median(values)),
                    "std": float(np.std(values)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "q25": float(np.percentile(values, 25)),
                    "q75": float(np.percentile(values, 75))
                }
                
                # Distribution analysis
                results["distribution"] = {
                    "skewness": float(self._calculate_skewness(values)),
                    "kurtosis": float(self._calculate_kurtosis(values)),
                    "is_normal": self._test_normality(values)
                }
                
                # Trend analysis if dates are available
                if "dates" in data:
                    results["trend_analysis"] = self._analyze_trends(values, data["dates"])
                
                # Category analysis if categories are available
                if "categories" in data:
                    results["category_analysis"] = self._analyze_categories(values, data["categories"])
            
        except Exception as e:
            self.logger.error(f"Analysis calculation failed: {e}")
            results["error"] = str(e)
        
        return results
    
    def _calculate_skewness(self, values: np.ndarray) -> float:
        """Calculate skewness of the distribution."""
        mean = np.mean(values)
        std = np.std(values)
        return np.mean(((values - mean) / std) ** 3)
    
    def _calculate_kurtosis(self, values: np.ndarray) -> float:
        """Calculate kurtosis of the distribution."""
        mean = np.mean(values)
        std = np.std(values)
        return np.mean(((values - mean) / std) ** 4) - 3
    
    def _test_normality(self, values: np.ndarray) -> bool:
        """Simple normality test based on skewness and kurtosis."""
        skewness = abs(self._calculate_skewness(values))
        kurtosis = abs(self._calculate_kurtosis(values))
        return skewness < 0.5 and kurtosis < 0.5
    
    def _analyze_trends(self, values: np.ndarray, dates: List[str]) -> Dict[str, Any]:
        """Analyze trends over time."""
        try:
            # Simple linear trend
            x = np.arange(len(values))
            slope, intercept = np.polyfit(x, values, 1)
            
            return {
                "trend_slope": float(slope),
                "trend_direction": "increasing" if slope > 0 else "decreasing",
                "trend_strength": abs(float(slope))
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _analyze_categories(self, values: np.ndarray, categories: List[str]) -> Dict[str, Any]:
        """Analyze data by categories."""
        try:
            df = pd.DataFrame({"values": values, "categories": categories})
            category_stats = df.groupby("categories")["values"].agg([
                "count", "mean", "median", "std"
            ]).to_dict("index")
            
            return {
                "category_stats": {k: {stat: float(v) for stat, v in stats.items()} 
                                 for k, stats in category_stats.items()}
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _create_visualizations(self, data: Any, analysis_results: Dict[str, Any]) -> List[str]:
        """Create data visualizations."""
        output_files = []
        
        try:
            # Create uploads directory
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            
            if isinstance(data, dict) and "values" in data:
                values = data["values"]
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                # Histogram
                plt.figure(figsize=(10, 6))
                plt.hist(values, bins=30, alpha=0.7, edgecolor='black')
                plt.title('Data Distribution')
                plt.xlabel('Values')
                plt.ylabel('Frequency')
                hist_file = os.path.join(upload_dir, f"histogram_{timestamp}.png")
                plt.savefig(hist_file, dpi=300, bbox_inches='tight')
                plt.close()
                output_files.append(hist_file)
                
                # Box plot
                plt.figure(figsize=(8, 6))
                plt.boxplot(values)
                plt.title('Data Box Plot')
                plt.ylabel('Values')
                box_file = os.path.join(upload_dir, f"boxplot_{timestamp}.png")
                plt.savefig(box_file, dpi=300, bbox_inches='tight')
                plt.close()
                output_files.append(box_file)
                
                # Category analysis if available
                if "categories" in data:
                    df = pd.DataFrame({"values": values, "categories": data["categories"]})
                    plt.figure(figsize=(10, 6))
                    df.boxplot(column='values', by='categories')
                    plt.title('Values by Category')
                    cat_file = os.path.join(upload_dir, f"category_analysis_{timestamp}.png")
                    plt.savefig(cat_file, dpi=300, bbox_inches='tight')
                    plt.close()
                    output_files.append(cat_file)
                
        except Exception as e:
            self.logger.error(f"Visualization creation failed: {e}")
        
        return output_files
    
    async def _generate_insights(self, analysis_results: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """Generate insights from analysis results."""
        system_prompt = """
        You are a data insights expert. Based on the analysis results, provide:
        1. Key findings (3-5 main insights)
        2. Actionable recommendations
        3. Potential concerns or limitations
        4. Next steps for further analysis
        
        Respond in JSON format:
        {
            "key_findings": ["finding1", "finding2"],
            "recommendations": ["rec1", "rec2"],
            "concerns": ["concern1", "concern2"],
            "next_steps": ["step1", "step2"]
        }
        """
        
        prompt = f"""
        Original Query: {original_query}
        
        Analysis Results:
        {json.dumps(analysis_results, indent=2)}
        
        Generate insights and recommendations.
        """
        
        try:
            response = await self.call_llm(prompt, system_prompt, temperature=0.3)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Insights generation failed: {e}")
            return {
                "key_findings": ["Analysis completed successfully"],
                "recommendations": ["Review the statistical results"],
                "concerns": ["Data quality should be verified"],
                "next_steps": ["Consider additional analysis"]
            }
    
    def _summarize_data(self, data: Any) -> Dict[str, Any]:
        """Create a summary of the input data."""
        if isinstance(data, dict):
            summary = {}
            for key, value in data.items():
                if isinstance(value, list):
                    summary[key] = {
                        "type": "list",
                        "length": len(value),
                        "sample": value[:5] if len(value) > 5 else value
                    }
                else:
                    summary[key] = {"type": type(value).__name__, "value": str(value)[:100]}
            return summary
        else:
            return {"type": type(data).__name__, "summary": str(data)[:200]}
