def analogous_reasoning(source_domain_concept: str, target_problem_domain: str, adaptation_goal: str = None) -> str:
  """
  Transforms a source concept and target problem into a prompt for 
  generating solutions using analogous reasoning with an LLM.

  Args:
    source_domain_concept: The source concept, model, process, or domain 
                           to draw inspiration from (e.g., 
                           "Netflix's recommendation algorithm", 
                           "ant colony optimization", 
                           "the structure of a rainforest ecosystem").
    target_problem_domain: The target problem, area, or domain where the 
                           analogy should be applied (e.g., 
                           "personalized learning paths for high school math",
                           "optimizing city traffic flow",
                           "designing a sustainable co-living space").
    adaptation_goal: Optional. A specific goal or focus for the adaptation 
                     (e.g., "education", "improve efficiency", 
                      "foster collaboration"). If None, a general adaptation
                      instruction will be used.

  Returns:
    A formatted prompt instructing an LLM to perform the analogous reasoning.
  """

  # 1. Clean inputs (basic stripping)
  source_clean = source_domain_concept.strip()
  target_clean = target_problem_domain.strip()
  
  # 2. Construct the core question
  core_question = f"How would the principles or structure of '{source_clean}' be applied to '{target_clean}'?"

  # 3. Construct the adaptation instruction
  if adaptation_goal and adaptation_goal.strip():
    goal_clean = adaptation_goal.strip()
    adaptation_instruction = f"Adapt its core concepts or logic specifically for {goal_clean}."
  else:
    adaptation_instruction = "Describe how its core principles or underlying logic could be adapted to this new context."
    
  # 4. Add a request for specifics (to encourage concrete output)
  specifics_request = "Outline the key components or steps of this analogous approach."

  # 5. Assemble the final prompt
  output_prompt = f"{core_question} {adaptation_instruction} {specifics_request}"
  
  return output_prompt
