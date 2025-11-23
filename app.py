from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(title="Kimberly AI Assistant", version="0.1.0")

# Load credentials from env
HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

# Load a small language model for demonstration
# Note: For production, use Llama 3.1 with proper hardware
generator = pipeline('text-generation', model='gpt2', use_auth_token=HUGGINGFACE_TOKEN if HUGGINGFACE_TOKEN else None)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Generate response using the model
    # This is a minimal implementation; replace with Llama 3.1 for full functionality
    generated = generator(request.message, max_length=50, num_return_sequences=1)
    response_text = generated[0]['generated_text']
    return ChatResponse(response=response_text)

@app.get("/")
async def root():
    return {"message": "Kimberly AI Assistant API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)