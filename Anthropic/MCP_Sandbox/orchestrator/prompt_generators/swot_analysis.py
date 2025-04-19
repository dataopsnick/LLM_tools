# orchestrator/prompt_generators/swot_analysis.py
import re

def swot_analysis(subject_or_context: str, specific_considerations: str = None) -> str:
  """
  Transforms a subject/context into a detailed prompt for generating
  a SWOT (Strengths, Weaknesses, Opportunities, Threats) analysis using an LLM.
  # ... (rest of the function code from swot_analysis.txt) ...
  """
  # 1. Clean and normalize the input subject/context
  processed_subject = subject_or_context.strip()
  processed_subject = re.sub(r'^(Analyze|Evaluate|Consider|Perform a SWOT on)\s+', '', processed_subject, flags=re.IGNORECASE)
  processed_subject = processed_subject[0].upper() + processed_subject[1:]
  if not processed_subject.endswith(('.', '?', '!')):
      processed_subject += '.'

  # 2. Construct the core request
  core_request = "Conduct a SWOT analysis"

  # 3. Add specific considerations if provided, otherwise add generic guidance
  if specific_considerations and specific_considerations.strip():
      considerations_clause = f" considering {specific_considerations.strip()}"
      if not considerations_clause.endswith('.'):
          considerations_clause += '.'
  else:
      considerations_clause = " identifying key internal (Strengths, Weaknesses) and external (Opportunities, Threats) factors."

  # 4. Add a concluding actionable request
  concluding_request = " Highlight potential strategic implications or actions based on the findings."

  # 5. Assemble the final prompt
  output_prompt = f"{processed_subject} {core_request}{considerations_clause}{concluding_request}"

  return output_prompt
# Ensure necessary imports like 're' are included