import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import redis
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from agent_runner import AgentRunner
# Import our modules
from memory_scoring import MeditationEngine, MemoryScorer

# Load environment variables
# load_dotenv()

app = FastAPI(title="Kimberly AI Assistant", version="0.1.0")

# Security setup
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Use a pure-Python safe default for CI and test environments. bcrypt requires
# a compiled backend which can be flaky in minimal CI images; pbkdf2_sha256
# is widely supported and deterministic for tests.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
security = HTTPBearer()

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# app.add_middleware(SlowAPIMiddleware)

# Redis for caching and short-term memory
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# Initialize components
memory_scorer = MemoryScorer()
meditation_engine = MeditationEngine(memory_scorer)
agent_runner = AgentRunner()


# Pydantic models
class UserCredentials(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"


class ChatResponse(BaseModel):
    response: str
    memory_stored: bool = False


class MemoryItem(BaseModel):
    id: str
    user_id: str
    type: str  # short-term, long-term, permanent
    content: str
    size_bytes: int
    metadata: Dict[str, Any]
    score: float = 0.0
    created_at: str
    last_seen_at: str


class MemoryRequest(BaseModel):
    content: str
    type: str = "long-term"
    metadata: Optional[Dict[str, Any]] = {}


class AgentTask(BaseModel):
    type: str
    description: str
    parameters: Optional[Dict[str, Any]] = {}


# Auth functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(username: str, password: str):
    # Mock user store - in real app, use database
    users_db = {
        "testuser": {
            "username": "testuser",
            "hashed_password": get_password_hash("testpass"),
        }
    }
    user = users_db.get(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    # Mock user verification
    if token_data.username != "testuser":
        raise credentials_exception
    return token_data.username


# API endpoints
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: UserCredentials):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/")
async def root():
    return {"message": "Kimberly AI Assistant API"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: str = Depends(get_current_user)):
    # Mock response - integrate with Llama 3.1 later
    response_text = f"Echo: {request.message}"

    # Store in short-term memory
    memory_key = f"memory:{request.user_id}:short-term"
    memory_item = {
        "id": f"mem_{int(datetime.now().timestamp())}",
        "user_id": request.user_id,
        "type": "short-term",
        "content": f"User: {request.message}\nAI: {response_text}",
        "size_bytes": len(response_text.encode()),
        "metadata": {"source": "chat"},
        "created_at": datetime.now().isoformat(),
        "last_seen_at": datetime.now().isoformat(),
    }

    # Cache in Redis (expires in 24 hours)
    redis_client.setex(memory_key, 86400, json.dumps(memory_item))

    return ChatResponse(response=response_text, memory_stored=True)


@app.post("/memory")
async def store_memory(
    request: MemoryRequest, current_user: str = Depends(get_current_user)
):
    # Create memory item
    memory_item = {
        "id": f"mem_{int(datetime.now().timestamp())}",
        "user_id": current_user,
        "type": request.type,
        "content": request.content,
        "size_bytes": len(request.content.encode()),
        "metadata": request.metadata,
        "score": 0.0,
        "created_at": datetime.now().isoformat(),
        "last_seen_at": datetime.now().isoformat(),
    }

    # Store based on type
    if request.type == "short-term":
        key = f"memory:{current_user}:short-term"
        redis_client.setex(key, 86400, json.dumps(memory_item))
    else:
        # For long-term/permanent, would store in DB - mock for now
        key = f"memory:{current_user}:{request.type}"
        redis_client.set(key, json.dumps(memory_item))

    return {"status": "stored", "id": memory_item["id"]}


@app.get("/memory")
async def get_memory(
    user_id: str,
    memory_type: str = "long-term",
    current_user: str = Depends(get_current_user),
):
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Access denied")

    # Retrieve from Redis
    key = f"memory:{user_id}:{memory_type}"
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return {"message": "No memory found"}


@app.post("/meditation")
async def run_meditation(user_id: str, current_user: str = Depends(get_current_user)):
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Access denied")

    # Gather all user memories (mock - in real app, query DB)
    memories = []
    for key in redis_client.scan_iter(f"memory:{user_id}:*"):
        data = redis_client.get(key)
        if data:
            memories.append(json.loads(data))

    # Run meditation
    quotas = {
        "short-term": 512 * 1024,  # 512KB
        "long-term": 2 * 1024 * 1024,  # 2MB
        "permanent": 10 * 1024 * 1024,  # 10MB
    }

    result = meditation_engine.run_meditation(memories, quotas)

    # Prune items
    for item_id in result["to_prune"]:
        for key in redis_client.scan_iter(f"memory:{user_id}:*"):
            data = redis_client.get(key)
            if data and json.loads(data)["id"] == item_id:
                redis_client.delete(key)
                break

    return result


@app.post("/agent")
async def delegate_agent(
    task: AgentTask, current_user: str = Depends(get_current_user)
):
    task_dict = task.model_dump()
    task_dict["user_id"] = current_user

    result = await agent_runner.delegate_task(task_dict)
    return result


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
