"""
GPT-OSS Integration Module for AI Operating System
Provides unified interface for GPT-OSS models via Hugging Face API
Handles AI decision making, text generation, code completion, and intelligent operations
"""

import asyncio
import json
import os
import aiohttp
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging
from pathlib import Path
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GPTOSSConfig:
    """Configuration for GPT-OSS integration"""
    api_key: str = ""
    base_url: str = "https://api-inference.huggingface.co/models"
    model_name: str = "microsoft/DialoGPT-large"  # Default GPT-OSS model
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    timeout: int = 30
    retry_attempts: int = 3
    
    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.getenv("HF_TOKEN", "")
        self.base_url = os.getenv("HUGGINGFACE_BASE_URL", self.base_url)
        self.model_name = os.getenv("HUGGINGFACE_MODEL_NAME", self.model_name)


@dataclass
class AIResponse:
    """Structured AI response"""
    text: str
    confidence: float
    model: str
    tokens_used: int
    response_time: float
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeAnalysis:
    """Code analysis result"""
    language: str
    complexity: str
    issues: List[str]
    suggestions: List[str]
    documentation: str
    test_cases: List[str]


@dataclass
class TaskPlan:
    """Task execution plan"""
    task_description: str
    steps: List[Dict[str, Any]]
    estimated_time: str
    required_tools: List[str]
    risk_assessment: str
    success_criteria: List[str]


class GPTOSSIntegration:
    """GPT-OSS integration handler for AI decision making"""
    
    def __init__(self, config: Optional[GPTOSSConfig] = None):
        self.config = config or GPTOSSConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.available_models = [
            "microsoft/DialoGPT-large",
            "microsoft/DialoGPT-medium",
            "microsoft/DialoGPT-small",
            "facebook/blenderbot-400M-distill",
            "facebook/blenderbot_small-90M",
            "EleutherAI/gpt-neo-2.7B",
            "EleutherAI/gpt-neo-1.3B",
            "EleutherAI/gpt-neo-125M",
            "bigscience/bloom-560m",
            "bigscience/bloom-1b1",
            "bigscience/bloom-1b7",
            "microsoft/CodeGPT-small-py",
            "microsoft/CodeGPT-medium-py"
        ]
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
    
    async def initialize(self):
        """Initialize the API connection"""
        if not self.config.api_key:
            raise ValueError("Hugging Face API key is required. Set HUGGINGFACE_API_KEY environment variable.")
        
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers
        )
        logger.info("GPT-OSS integration initialized")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("GPT-OSS integration cleaned up")
    
    async def generate_text(self, 
                           prompt: str, 
                           context: Optional[str] = None,
                           max_tokens: Optional[int] = None,
                           temperature: Optional[float] = None) -> AIResponse:
        """Generate text using GPT-OSS model"""
        if not self.client:
            await self.initialize()
        
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})
        
        start_time = datetime.now()
        
        for attempt in range(self.config.retry_attempts):
            try:
                completion = await self.client.chat.completions.create(
                    model=self.config.model_name,
                    messages=messages,
                    max_tokens=max_tokens or self.config.max_tokens,
                    temperature=temperature or self.config.temperature,
                    top_p=self.config.top_p,
                    timeout=self.config.timeout
                )
                
                response_time = (datetime.now() - start_time).total_seconds()
                generated_text = completion.choices[0].message.content.strip()
                tokens_used = completion.usage.total_tokens if completion.usage else 0
                
                return AIResponse(
                    text=generated_text,
                    confidence=0.85,  # Placeholder confidence
                    model=self.config.model_name,
                    tokens_used=tokens_used,
                    response_time=response_time,
                    timestamp=datetime.now().isoformat()
                )
            
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}: {str(e)}")
                if attempt == self.config.retry_attempts - 1:
                    raise
                await asyncio.sleep(5 * (attempt + 1)) # Wait before retrying
                if attempt == self.config.retry_attempts - 1:
                    raise
        
        raise Exception("All retry attempts exhausted")
    
    async def analyze_code(self, code: str, language: str = "python") -> CodeAnalysis:
        """Analyze code using GPT-OSS"""
        prompt = f"""
        Analyze the following {language} code and provide:
        1. Language detection
        2. Complexity assessment
        3. Potential issues
        4. Improvement suggestions
        5. Documentation
        6. Test cases

        Code:
        ```{language}
        {code}
        ```

        Provide your analysis in JSON format with keys: language, complexity, issues, suggestions, documentation, test_cases
        """
        
        response = await self.generate_text(prompt, max_tokens=1000, temperature=0.3)
        
        try:
            # Try to parse JSON response
            analysis_data = json.loads(response.text)
            return CodeAnalysis(**analysis_data)
        except:
            # Fallback to structured parsing
            lines = response.text.split('\n')
            return CodeAnalysis(
                language=language,
                complexity="medium",
                issues=["Unable to parse detailed analysis"],
                suggestions=["Consider adding unit tests"],
                documentation="Code analysis completed",
                test_cases=["Add basic unit tests"]
            )
    
    async def create_task_plan(self, task_description: str) -> TaskPlan:
        """Create a task execution plan using AI"""
        prompt = f"""
        Create a detailed execution plan for the following task:
        {task_description}

        Please provide:
        1. A list of specific steps to complete the task
        2. Estimated time for completion
        3. Required tools or resources
        4. Potential risks and mitigation strategies
        5. Success criteria

        Format the response as JSON with keys: steps, estimated_time, required_tools, risk_assessment, success_criteria
        """
        
        response = await self.generate_text(prompt, max_tokens=800, temperature=0.4)
        
        try:
            plan_data = json.loads(response.text)
            return TaskPlan(
                task_description=task_description,
                steps=plan_data.get("steps", []),
                estimated_time=plan_data.get("estimated_time", "Unknown"),
                required_tools=plan_data.get("required_tools", []),
                risk_assessment=plan_data.get("risk_assessment", "Low"),
                success_criteria=plan_data.get("success_criteria", ["Task completed successfully"])
            )
        except:
            # Fallback plan
            return TaskPlan(
                task_description=task_description,
                steps=[{"step": 1, "action": "Analyze task", "description": "Break down the task into manageable steps"}],
                estimated_time="1-2 hours",
                required_tools=["Basic development tools"],
                risk_assessment="Low",
                success_criteria=["Task requirements met", "Code quality maintained", "Tests passing"]
            )
    
    async def get_code_suggestions(self, 
                                 current_code: str, 
                                 desired_functionality: str,
                                 language: str = "python") -> List[str]:
        """Get code suggestions for implementing functionality"""
        prompt = f"""
        Current {language} code:
        ```{language}
        {current_code}
        ```

        Desired functionality: {desired_functionality}

        Provide 3-5 specific code suggestions to implement this functionality. 
        Focus on practical, working code examples.
        """
        
        response = await self.generate_text(prompt, max_tokens=600, temperature=0.5)
        
        # Parse suggestions from response
        suggestions = []
        lines = response.text.split('\n')
        current_suggestion = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith(('1.', '2.', '3.', '4.', '5.')) or line.startswith(('-', '*')):
                if current_suggestion:
                    suggestions.append(current_suggestion.strip())
                current_suggestion = line
            elif line:
                current_suggestion += " " + line
        
        if current_suggestion:
            suggestions.append(current_suggestion.strip())
        
        return suggestions if suggestions else ["Review the desired functionality and implement step by step"]
    
    async def debug_code(self, error_message: str, code_context: str) -> Dict[str, Any]:
        """Debug code using AI analysis"""
        prompt = f"""
        Debug the following error:
        Error: {error_message}

        Code context:
        ```
        {code_context}
        ```

        Provide:
        1. Likely cause of the error
        2. Specific fix suggestions
        3. Prevention strategies
        4. Related code improvements
        """
        
        response = await self.generate_text(prompt, max_tokens=500, temperature=0.3)
        
        return {
            "error_analysis": response.text,
            "suggested_fix": "Check the error message and apply the suggested fixes",
            "prevention": "Add proper error handling and validation",
            "confidence": 0.8
        }
    
    async def optimize_query(self, query: str, context: Dict[str, Any] = None) -> str:
        """Optimize user queries for better AI understanding"""
        prompt = f"""
        Optimize the following query for better AI understanding and execution:
        Original query: {query}
        Context: {json.dumps(context, indent=2) if context else "No additional context"}

        Provide an optimized version that is clearer, more specific, and includes relevant context.
        """
        
        response = await self.generate_text(prompt, max_tokens=200, temperature=0.2)
        return response.text.strip()
    
    async def get_available_models(self) -> List[str]:
        """Get list of available GPT-OSS models"""
        return self.available_models
    
    async def switch_model(self, model_name: str) -> bool:
        """Switch to a different GPT-OSS model"""
        if model_name in self.available_models:
            self.config.model_name = model_name
            logger.info(f"Switched to model: {model_name}")
            return True
        return False


class QueryStackingSystem:
    """System for handling complex multi-step operations"""
    
    def __init__(self, gpt_integration: GPTOSSIntegration):
        self.gpt = gpt_integration
        self.active_queries: Dict[str, Dict[str, Any]] = {}
    
    async def create_query_stack(self, 
                               main_query: str, 
                               context: Dict[str, Any] = None) -> str:
        """Create a query stack for complex operations"""
        stack_id = f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(main_query) % 10000}"
        
        # Generate task plan
        task_plan = await self.gpt.create_task_plan(main_query)
        
        self.active_queries[stack_id] = {
            "original_query": main_query,
            "context": context or {},
            "task_plan": task_plan,
            "current_step": 0,
            "completed_steps": [],
            "results": {},
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
        
        return stack_id
    
    async def execute_next_step(self, stack_id: str) -> Dict[str, Any]:
        """Execute the next step in the query stack"""
        if stack_id not in self.active_queries:
            return {"error": "Query stack not found"}
        
        stack = self.active_queries[stack_id]
        task_plan = stack["task_plan"]
        
        if stack["current_step"] >= len(task_plan.steps):
            stack["status"] = "completed"
            return {"status": "completed", "results": stack["results"]}
        
        current_step = task_plan.steps[stack["current_step"]]
        
        # Execute step (this would integrate with MCP servers)
        step_result = {
            "step": current_step,
            "executed_at": datetime.now().isoformat(),
            "result": "Step executed successfully"
        }
        
        stack["completed_steps"].append(current_step)
        stack["results"][f"step_{stack['current_step']}"] = step_result
        stack["current_step"] += 1
        
        return {
            "step_executed": current_step,
            "next_step": stack["current_step"],
            "status": "in_progress"
        }
    
    async def get_query_status(self, stack_id: str) -> Dict[str, Any]:
        """Get status of a query stack"""
        if stack_id not in self.active_queries:
            return {"error": "Query stack not found"}
        
        stack = self.active_queries[stack_id]
        task_plan = stack["task_plan"]
        
        return {
            "stack_id": stack_id,
            "original_query": stack["original_query"],
            "status": stack["status"],
            "current_step": stack["current_step"],
            "total_steps": len(task_plan.steps),
            "progress": f"{stack['current_step']}/{len(task_plan.steps)}",
            "estimated_time_remaining": task_plan.estimated_time,
            "results": stack["results"]
        }
    
    async def cancel_query(self, stack_id: str) -> bool:
        """Cancel a query stack"""
        if stack_id in self.active_queries:
            self.active_queries[stack_id]["status"] = "cancelled"
            return True
        return False


# Global instances for easy access
gpt_integration = GPTOSSIntegration()
query_stacking = QueryStackingSystem(gpt_integration)


# Example usage functions
async def example_usage():
    """Example usage of the GPT-OSS integration"""
    async with gpt_integration as gpt:
        # Generate text
        response = await gpt.generate_text("Explain quantum computing in simple terms")
        print(f"Generated: {response.text}")
        
        # Analyze code
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        analysis = await gpt.analyze_code(code, "python")
        print(f"Code analysis: {analysis}")
        
        # Create task plan
        plan = await gpt.create_task_plan("Create a REST API with authentication")
        print(f"Task plan: {plan}")


if __name__ == "__main__":
    asyncio.run(example_usage())