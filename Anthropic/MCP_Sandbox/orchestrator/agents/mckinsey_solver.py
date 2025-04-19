# orchestrator/agents/mckinsey_solver.py
from pydantic import BaseModel, Field
from typing import List, Optional

class AnalysisStep(BaseModel):
    step_name: str = Field(description="Clear name for the analysis step (e.g., 'Market Size Estimation', 'Competitor Benchmarking').")
    description: str = Field(description="What specific question this analysis answers or what data it aims to gather.")
    data_sources: List[str] = Field(description="Potential sources of data required (e.g., 'Internal sales data', 'Industry reports', 'Customer surveys').")
    responsible: Optional[str] = Field(default=None, description="Team or role potentially responsible (e.g., 'Marketing Team', 'Data Science').")

class Recommendation(BaseModel):
    recommendation_title: str = Field(description="Concise title for the recommendation.")
    description: str = Field(description="Detailed explanation of the proposed action or strategy.")
    key_supporting_findings: List[str] = Field(description="List of key synthesized findings that support this recommendation.")
    potential_risks: Optional[List[str]] = Field(default=None, description="Potential risks or challenges associated with this recommendation.")
    next_steps: Optional[List[str]] = Field(default=None, description="Immediate next steps to implement this recommendation.")

class McKinseySolutionPlan(BaseModel):
    """
    A structured plan following the McKinsey 7-step problem-solving process,
    derived from a comprehensive problem analysis using multiple frameworks.
    """
    problem_definition: str = Field(description="A clear, concise, and actionable definition of the core problem, synthesized from the input analyses.")
    structured_issues: List[str] = Field(description="The problem broken down into distinct, MECE (Mutually Exclusive, Collectively Exhaustive) key issues or questions.")
    prioritized_issues: List[str] = Field(description="The critical few issues from the structured list that need to be addressed first, based on potential impact and feasibility.")
    analysis_workplan: List[AnalysisStep] = Field(description="A plan outlining the analyses needed to address the prioritized issues.")
    synthesized_findings: str = Field(description="A summary of the key insights derived from the input analyses and the planned analyses (or hypothetical results).")
    recommendations: List[Recommendation] = Field(description="Actionable recommendations based on the synthesized findings.")
    communication_summary: Optional[str] = Field(default=None, description="A brief narrative or storyline (Situation-Complication-Resolution) summarizing the core message for stakeholders.")

    model_config = {
        "json_schema_extra": {
            "description": "Structured output for a McKinsey 7-Step Problem Solving approach."
        }
    }

# System prompt can also be stored here as a constant string
MCKINSEY_SYSTEM_PROMPT = """
You are an expert Strategy Consultant embodying the McKinsey 7-Step Problem Solving approach. Your input is a comprehensive analysis of a problem statement, viewed through multiple analytical frameworks (like SWOT, Six Hats, Fishbone, etc.). Your task is to synthesize this multi-faceted input and generate a structured solution plan.

**Input:** You will receive a block of text containing analyses of a core problem from various perspectives.

**Your Goal:** Generate a `McKinseySolutionPlan` JSON object adhering to the provided Pydantic schema.

**Steps to Follow (Mentally):**

1.  **Define the Problem:** Synthesize the *single, core problem* from the diverse inputs. Make it SMART (Specific, Measurable, Action-oriented, Relevant, Time-bound) if possible.
2.  **Structure the Problem:** Break down the core problem into its key component issues or questions. Ensure these are MECE (Mutually Exclusive, Collectively Exhaustive).
3.  **Prioritize Issues:** Identify the most critical issues from the structured list based on likely impact and the insights provided in the input analysis.
4.  **Plan Analyses:** For the *prioritized* issues, outline the specific analyses required to develop solutions. What data is needed? Where might it come from?
5.  **Synthesize Findings:** Briefly summarize the most critical insights drawn from the input analyses that inform the potential solutions.
6.  **Develop Recommendations:** Based on the findings, formulate clear, actionable recommendations. Link them back to the findings. Consider risks and next steps.
7.  **Communication (Optional but good):** Frame the core argument using a Situation-Complication-Resolution structure if possible.

**Output:** Respond **ONLY** with the JSON object conforming to the `McKinseySolutionPlan` schema. Ensure all required fields are present.
"""