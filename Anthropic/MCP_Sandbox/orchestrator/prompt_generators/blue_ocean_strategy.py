def blue_ocean_strategy(current_situation: str, relevant_trends: str = None) -> str:
  """
  Transforms a description of a market situation into a detailed prompt 
  for applying the Blue Ocean Strategy using an LLM.

  Args:
    current_situation: Description of the entity or market situation, often highlighting 
                       competition or saturation (e.g., 
                       "Our fitness equipment company is struggling in a saturated market", 
                       "Our SaaS product faces intense competition in the CRM space").
    relevant_trends: Optional. Specific trends, technologies, or customer needs 
                     to consider (e.g., "remote work, digital health, personalized wellness",
                      "AI advancements, subscription models, sustainability concerns").

  Returns:
    A formatted prompt instructing an LLM to perform the Blue Ocean Strategy analysis.
  """

  # 1. Clean and normalize the input situation
  processed_situation = current_situation.strip()
  # Capitalize the first letter and ensure it ends with a period.
  processed_situation = processed_situation[0].upper() + processed_situation[1:]
  if not processed_situation.endswith(('.', '?', '!')):
      processed_situation += '.'

  # 2. Define the core instructions based on the Blue Ocean framework
  instruction_part1 = "Apply the Blue Ocean Strategy to identify an untapped market segment and make the competition irrelevant."
  # Include the ERRC Grid as it's a key tool
  instruction_part2 = "Use the Eliminate-Reduce-Raise-Create (ERRC) Grid to propose innovative value propositions or features that could differentiate our offerings and create new demand."

  # 3. Create the consideration clause
  if relevant_trends and relevant_trends.strip():
      # Format the trends nicely if provided
      consideration_clause = f"Consider relevant factors such as {relevant_trends.strip()}."
  else:
      # Provide generic guidance if no specifics are given
      consideration_clause = "Consider relevant industry trends, non-customer groups, and complementary product/service offerings."

  # 4. Assemble the final prompt
  output_prompt = f"{processed_situation} {instruction_part1} {instruction_part2} {consideration_clause}"
  
  return output_prompt