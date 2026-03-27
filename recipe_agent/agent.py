"""
Smart Chef AI — Multi-Agent Recipe Generator
Built with Google ADK + Gemini

Multi-Agent Architecture (SequentialAgent):
  Agent 1: Content Analyzer → Reads files, identifies food/cooking content, rejects non-food
  Agent 2: Recipe Chef      → Takes identified ingredients and generates a complete recipe
"""

import os
import logging
from dotenv import load_dotenv

from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools.tool_context import ToolContext

# --- Setup ---
load_dotenv()

MODEL_NAME = os.getenv("MODEL", "gemini-2.5-flash")


# ═══════════════════════════════════════════════
#  Tool: Analyze Content
# ═══════════════════════════════════════════════
def analyze_content(
    tool_context: ToolContext,
    content: str,
    source_type: str = "text",
) -> dict:
    """
    Analyzes the provided content to determine if it is food/cooking related.
    Extracts ingredients and food items if found.

    Args:
        tool_context: The ADK tool context for state management.
        content: The text content to analyze (raw text or extracted from a document).
        source_type: The source of the content - 'text' for typed input, 'document' for uploaded files.

    Returns:
        A dictionary with analysis results including whether the content is food-related.
    """
    tool_context.state["raw_content"] = content
    tool_context.state["source_type"] = source_type
    logging.info(f"[Content Analyzer] Source: {source_type}, Content length: {len(content)}")

    return {
        "status": "success",
        "message": "Content received for analysis.",
    }


# ═══════════════════════════════════════════════
#  Tool: Prepare Recipe Output
# ═══════════════════════════════════════════════
def prepare_recipe(
    tool_context: ToolContext,
    ingredients: str,
    dietary_restrictions: str = "",
    cuisine_preference: str = "",
    meal_type: str = "",
) -> dict:
    """
    Stores the validated ingredients and preferences for recipe generation.

    Args:
        tool_context: The ADK tool context for state management.
        ingredients: The validated, extracted ingredients list.
        dietary_restrictions: Optional dietary restrictions.
        cuisine_preference: Optional cuisine preference.
        meal_type: Optional meal type.

    Returns:
        A dictionary confirming ingredients are ready for recipe generation.
    """
    tool_context.state["ingredients"] = ingredients
    tool_context.state["dietary_restrictions"] = dietary_restrictions
    tool_context.state["cuisine_preference"] = cuisine_preference
    tool_context.state["meal_type"] = meal_type

    logging.info(f"[Recipe Chef] Ingredients: {ingredients}")

    return {
        "status": "success",
        "message": "Ingredients validated and ready for recipe generation.",
    }


# ═══════════════════════════════════════════════
#  AGENT 1: Content Analyzer
# ═══════════════════════════════════════════════
content_analyzer = Agent(
    name="content_analyzer",
    model=MODEL_NAME,
    description="Analyzes uploaded content to determine if it is food/cooking related and extracts ingredients.",
    instruction="""You are a **Content Analysis Specialist** 🔍. Your ONLY job is to analyze content
and determine if it is related to food, cooking, or ingredients.

**When content is provided:**
1. FIRST, use the 'analyze_content' tool to store the raw content.
2. Then carefully analyze the content.

**Decision Logic:**
- ✅ **FOOD-RELATED**: The content contains ingredients, recipes, cooking instructions,
  grocery lists, meal plans, food items, or anything related to cooking/food.
  → Extract ALL food ingredients/items found.
  → Output a clear summary: "FOOD_CONTENT_DETECTED" followed by the list of identified ingredients.

- ❌ **NOT FOOD-RELATED**: The content is about work, business, code, finance, legal documents,
  technical content, academic papers, or anything NOT related to food/cooking.
  → Output exactly: "REJECTED: This file does not contain food or cooking-related content.
  Please upload a document with ingredients, recipes, or grocery lists."

**Examples of FOOD content:** ingredient lists, recipe cards, grocery lists, meal plans,
cooking blogs, restaurant menus, food labels, nutrition facts.

**Examples of NON-FOOD content:** code files, business reports, resumes, legal contracts,
meeting notes, financial statements, academic papers, invoices.

Be strict in your classification. If the content is primarily non-food with just a
mention of food (like "lunch meeting"), classify it as NOT food-related.

CONTENT TO ANALYZE:
{raw_content}
""",
    tools=[analyze_content],
    output_key="analysis_result",
)


# ═══════════════════════════════════════════════
#  AGENT 2: Recipe Chef
# ═══════════════════════════════════════════════
recipe_chef = Agent(
    name="recipe_chef",
    model=MODEL_NAME,
    description="Takes analyzed ingredients and generates a detailed, structured recipe.",
    instruction="""You are **Chef Gemini** 👨‍🍳, a world-class AI chef with expertise in global cuisines.

**First, check the ANALYSIS_RESULT from the Content Analyzer agent:**

If the analysis says "REJECTED" → Simply repeat the rejection message. Do NOT generate a recipe.
Stop here and provide the rejection message to the user in a friendly way.

If the analysis says "FOOD_CONTENT_DETECTED" → Use the 'prepare_recipe' tool to store
the ingredients, then generate a complete recipe.

**Your recipe response MUST follow this structure:**

## 🍽️ [Creative Recipe Name]

### ⏱️ Quick Info
| Detail | Value |
|--------|-------|
| **Prep Time** | [time] |
| **Cook Time** | [time] |
| **Total Time** | [time] |
| **Servings** | [number] |
| **Difficulty** | [Easy/Medium/Hard] |

### 📝 Ingredients
- List each ingredient with exact measurements
- Mark user's ingredients with ✅
- Suggest essential additions with 💡

### 👨‍🍳 Step-by-Step Instructions
1. Number each step clearly
2. Include temperatures and times
3. Add helpful tips in *italics*

### 💡 Chef's Pro Tips
- 2-3 professional cooking tips

### 🔄 Variations
- 1-2 alternative versions of the recipe

**Rules:**
- ALWAYS use the 'prepare_recipe' tool first to store validated ingredients
- Focus on the identified ingredients
- Respect any dietary restrictions
- Be warm, encouraging, and make cooking feel accessible
- Use emojis to make it visually appealing

ANALYSIS_RESULT: {analysis_result}
""",
    tools=[prepare_recipe],
)


# ═══════════════════════════════════════════════
#  Sequential Workflow: Analyzer → Chef
# ═══════════════════════════════════════════════
smart_chef_workflow = SequentialAgent(
    name="smart_chef_workflow",
    description="Multi-agent workflow: first analyzes content for food relevance, then generates recipe.",
    sub_agents=[
        content_analyzer,  # Step 1: Analyze & validate content
        recipe_chef,        # Step 2: Generate recipe (or reject)
    ],
)


# ═══════════════════════════════════════════════
#  ROOT AGENT: Entry Point
# ═══════════════════════════════════════════════
root_agent = Agent(
    name="smart_chef_ai",
    model=MODEL_NAME,
    description="Smart Chef AI — Intelligent recipe generator that validates food content before cooking.",
    instruction="""You are the **Smart Chef AI** 🧠👨‍🍳 assistant.

Welcome the user and let them know you can:
1. Generate recipes from ingredients they type
2. Read uploaded documents (PDF, Word, images, text) and extract ingredients
3. REJECT non-food documents with a helpful message

When the user provides input (text or extracted document content):
- Use the 'analyze_content' tool to save their content
- Then transfer control to the 'smart_chef_workflow' to analyze and cook!

Be friendly and enthusiastic about food! 🍳
""",
    tools=[analyze_content],
    sub_agents=[smart_chef_workflow],
)
