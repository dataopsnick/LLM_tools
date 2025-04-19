import re

def counterfactual_reasoning(premise: str, specific_focus_areas: str = None) -> str:
  """
  Transforms a counterfactual premise into a detailed prompt for exploring 
  "what if" historical scenarios using an LLM.

  Args:
    premise: The counterfactual starting point or question 
             (e.g., "What if Blockbuster had acquired Netflix in 2000?",
              "Imagine the Roman Empire never fell").
    specific_focus_areas: Optional. A string describing specific domains or impacts 
                            the analysis should focus on (e.g., 
                            "the streaming market's evolution, content production, and global internet infrastructure",
                            "technological development, political structures, and cultural diffusion").

  Returns:
    A formatted prompt instructing an LLM to perform the counterfactual analysis.
  """

  # 1. Clean and normalize the premise
  processed_premise = premise.strip()
  # Ensure it starts appropriately (often with "What if" or similar)
  if not re.match(r'^(What if|Imagine|Suppose)\s+', processed_premise, flags=re.IGNORECASE):
      # If it doesn't start like a question/premise, prepend "What if "
      if not processed_premise.endswith('?'):
          processed_premise = "What if " + processed_premise.strip('.') + "?"
      else: # It's already a question, likely okay
          processed_premise = processed_premise[0].upper() + processed_premise[1:]
  else:
       processed_premise = processed_premise[0].upper() + processed_premise[1:] # Capitalize first letter
       if not processed_premise.endswith('?'):
           processed_premise += '?' # Ensure it ends with a question mark

  # 2. Construct the core request - adapt based on phrasing
  core_request = "Explore the potential consequences of this alternate scenario."
  if re.match(r'^(What if)\s+', processed_premise, flags=re.IGNORECASE):
       core_request = "Simulate the likely outcomes and evolution resulting from this premise."
  elif re.match(r'^(Imagine|Suppose)\s+', processed_premise, flags=re.IGNORECASE):
       core_request = "Describe the world or situation that might have resulted."


  # 3. Add specific focus areas if provided, otherwise add generic guidance
  if specific_focus_areas and specific_focus_areas.strip():
      focus_clause = f" Focus the analysis on impacts related to {specific_focus_areas.strip()}"
      if not focus_clause.endswith('.'):
          focus_clause += '.'
  else:
      # Provide generic guidance if no specifics are given
      focus_clause = " Include analysis of key turning points, major affected domains (e.g., technology, society, economy), and significant deviations from our actual timeline."

  # 4. Assemble the final prompt
  output_prompt = f"{processed_premise} {core_request}{focus_clause}"
  
  return output_prompt