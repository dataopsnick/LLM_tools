import re

def cost_benefit_analysis(decision_or_scenario: str, comparison_factors: str = None, additional_analysis_requests: str = None) -> str:
  """
  Transforms a decision/scenario description into a detailed prompt for generating 
  a Cost-Benefit Analysis (CBA) using an LLM.

  Args:
    decision_or_scenario: The core decision, action, or comparison being evaluated 
                          (e.g., "Should our startup build an in-house AI team or outsource?", 
                           "Investing in employee training program",
                           "Upgrading our current software platform").
    comparison_factors: Optional. Specific costs and benefits the analysis should focus on 
                        (e.g., "5-year costs, IP control, and speed-to-market",
                         "implementation cost, productivity gains, employee retention").
    additional_analysis_requests: Optional. Specific types of analysis to include 
                                   (e.g., "sensitivity analysis for funding changes",
                                    "risk assessment", "qualitative impact summary").

  Returns:
    A formatted prompt instructing an LLM to perform the Cost-Benefit Analysis.
  """

  # 1. Clean and normalize the input decision/scenario
  processed_decision = decision_or_scenario.strip()
  # Simple regex to remove common leading phrases (can be expanded)
  processed_decision = re.sub(r'^(Analyze|Evaluate|Compare|Should we|Perform CBA on)\s+', '', processed_decision, flags=re.IGNORECASE)
  # Capitalize the first letter and ensure it ends with punctuation.
  processed_decision = processed_decision[0].upper() + processed_decision[1:]
  if not processed_decision.endswith(('.', '?', '!')):
      processed_decision += '.'

  # 2. Start constructing the prompt
  prompt_start = f"{processed_decision} Perform a Cost-Benefit Analysis."

  # 3. Add clause for comparison factors
  if comparison_factors and comparison_factors.strip():
      factors_clause = f" Focus the comparison on factors such as: {comparison_factors.strip()}."
  else:
      # Provide generic guidance if no specifics are given
      factors_clause = " Identify and compare key quantitative and qualitative costs and benefits over a relevant timeframe (e.g., 3-5 years)."

  # 4. Add clause for additional analysis requests
  analysis_clause = ""
  if additional_analysis_requests and additional_analysis_requests.strip():
       # Clean up the request slightly
       add_req_cleaned = additional_analysis_requests.strip()
       if not add_req_cleaned.endswith('.'):
           add_req_cleaned += '.'
       # Make the prompt instruction clear
       if not add_req_cleaned.lower().startswith(('include', 'perform', 'conduct', 'assess')):
           analysis_clause = f" Also, include analysis on {add_req_cleaned.lower()}"
       else:
            analysis_clause = f" Also, {add_req_cleaned}" # Use provided instruction verb

  # 5. Add suggestion for output structure/summary
  output_suggestion = " Present the results clearly, potentially using a table to list costs and benefits. Summarize the net benefit or loss and provide a recommendation based on the analysis."

  # 6. Assemble the final prompt
  output_prompt = f"{prompt_start}{factors_clause}{analysis_clause}{output_suggestion}"

  return output_prompt