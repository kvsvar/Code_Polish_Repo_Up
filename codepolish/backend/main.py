from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import analyze, tree

app = FastAPI(title="CodePolish API")

# Enable CORS for localhost React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(tree.router)

@app.get("/")
def read_root():
    return {"message": "CodePolish API is running"}
