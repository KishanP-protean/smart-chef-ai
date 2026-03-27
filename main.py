"""
Smart Chef AI — FastAPI Server

Multi-agent recipe generator with intelligent file content analysis.
Agent 1 validates food content, Agent 2 generates recipes.
Non-food documents are rejected gracefully.
"""

import os
import io
import json
import logging
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Document processing
import PyPDF2
from docx import Document
from PIL import Image

# --- Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart Chef AI",
    description="Multi-agent recipe generator — analyzes content, rejects non-food, generates recipes",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ADK Agent Setup (with error handling) ---
AGENT_READY = False
runner = None
session_service = None

try:
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    from recipe_agent.agent import root_agent

    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="smart_chef_ai_app",
        session_service=session_service,
    )
    AGENT_READY = True
    logger.info("✅ ADK Agent initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize ADK Agent: {e}")
    import traceback
    traceback.print_exc()

APP_NAME = "smart_chef_ai_app"
USER_ID = "web_user"


async def call_agent(user_message: str, session_id: str) -> str:
    """Send a message to the ADK multi-agent system and get the response."""
    if not AGENT_READY:
        raise HTTPException(
            status_code=503,
            detail="Agent not initialized. Check server logs for details.",
        )

    from google.genai import types

    session = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session_id
    )
    if session is None:
        session = await session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )

    content = types.Content(
        role="user", parts=[types.Part.from_text(text=user_message)]
    )

    final_response = ""
    async for event in runner.run_async(
        user_id=USER_ID, session_id=session_id, new_message=content
    ):
        if event.is_final_response():
            for part in event.content.parts:
                if part.text:
                    final_response += part.text

    return final_response


# ═══════════════════════════════════════════════
#  Document Text Extraction
# ═══════════════════════════════════════════════

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise HTTPException(status_code=400, detail=f"Could not read PDF: {str(e)}")


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a Word document."""
    try:
        doc = Document(io.BytesIO(file_bytes))
        text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        return text.strip()
    except Exception as e:
        logger.error(f"DOCX extraction error: {e}")
        raise HTTPException(
            status_code=400, detail=f"Could not read Word document: {str(e)}"
        )


def extract_text_from_image(file_bytes: bytes) -> str:
    """Extract description from an image for Gemini to analyze."""
    try:
        img = Image.open(io.BytesIO(file_bytes))
        width, height = img.size
        return (
            f"[Uploaded image: {width}x{height}, format={img.format or 'unknown'}. "
            f"This is a photo that may show food items, ingredients, a recipe card, "
            f"a grocery receipt, or something entirely unrelated to food. "
            f"Please analyze what this image likely contains and determine if it's food-related.]"
        )
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        raise HTTPException(
            status_code=400, detail=f"Could not process image: {str(e)}"
        )


# ═══════════════════════════════════════════════
#  API: Generate Recipe from Text Input
# ═══════════════════════════════════════════════

@app.post("/api/generate")
async def generate_recipe(
    ingredients: str = Form(...),
    dietary_restrictions: str = Form(""),
    cuisine_preference: str = Form(""),
    meal_type: str = Form(""),
):
    """Generate a recipe from text input. Agent 1 validates, Agent 2 cooks."""
    if not ingredients.strip():
        raise HTTPException(status_code=400, detail="Ingredients list cannot be empty")

    # Build the prompt for the multi-agent pipeline
    prompt = (
        f"Here is what the user provided as text input:\n\n"
        f"---\n{ingredients}\n---\n\n"
        f"Please analyze this content. If it contains food/cooking ingredients, "
        f"generate a recipe."
    )
    if dietary_restrictions:
        prompt += f" Dietary restrictions: {dietary_restrictions}."
    if cuisine_preference:
        prompt += f" Preferred cuisine: {cuisine_preference}."
    if meal_type:
        prompt += f" Meal type: {meal_type}."

    session_id = str(uuid.uuid4())

    try:
        response = await call_agent(prompt, session_id)
        return JSONResponse(content={"status": "success", "recipe": response})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process request: {str(e)}"
        )


# ═══════════════════════════════════════════════
#  API: Upload Document → Analyze → Generate
# ═══════════════════════════════════════════════

@app.post("/api/upload")
async def upload_and_generate(
    file: UploadFile = File(...),
    dietary_restrictions: str = Form(""),
    cuisine_preference: str = Form(""),
    meal_type: str = Form(""),
):
    """
    Upload a file → Agent 1 analyzes for food content → Agent 2 generates recipe.
    Non-food documents are rejected by Agent 1.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    file_bytes = await file.read()
    filename = file.filename.lower()

    # Extract text based on file type
    if filename.endswith(".pdf"):
        extracted_text = extract_text_from_pdf(file_bytes)
        file_type = "PDF document"
    elif filename.endswith((".docx", ".doc")):
        extracted_text = extract_text_from_docx(file_bytes)
        file_type = "Word document"
    elif filename.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")):
        extracted_text = extract_text_from_image(file_bytes)
        file_type = "Image"
    elif filename.endswith(".txt"):
        extracted_text = file_bytes.decode("utf-8", errors="ignore").strip()
        file_type = "Text file"
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload PDF, DOCX, TXT, or image files.",
        )

    if not extracted_text:
        raise HTTPException(
            status_code=400, detail="Could not extract any text from the uploaded file."
        )

    # Build prompt — Agent 1 will determine if this is food-related
    prompt = (
        f"The user uploaded a {file_type} named '{file.filename}'.\n"
        f"Here is the extracted content from the document:\n\n"
        f"---\n{extracted_text}\n---\n\n"
        f"Please analyze this document content carefully:\n"
        f"1. Is this content related to food, cooking, ingredients, or recipes?\n"
        f"2. If YES → Extract the ingredients and generate a delicious recipe.\n"
        f"3. If NO → Reject the file and tell the user to upload food-related content."
    )
    if dietary_restrictions:
        prompt += f"\nDietary restrictions: {dietary_restrictions}."
    if cuisine_preference:
        prompt += f"\nPreferred cuisine: {cuisine_preference}."
    if meal_type:
        prompt += f"\nMeal type: {meal_type}."

    session_id = str(uuid.uuid4())

    try:
        response = await call_agent(prompt, session_id)

        return JSONResponse(
            content={
                "status": "success",
                "file_name": file.filename,
                "file_type": file_type,
                "extracted_text": extracted_text[:500],
                "recipe": response,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process file: {str(e)}"
        )


# ═══════════════════════════════════════════════
#  Health Check
# ═══════════════════════════════════════════════

@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {
        "status": "healthy",
        "service": "smart-chef-ai",
        "version": "2.0.0",
        "agent_ready": AGENT_READY,
        "agents": ["content_analyzer", "recipe_chef"],
        "architecture": "multi-agent (SequentialAgent)",
    }


# --- Serve Static Files ---
static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
