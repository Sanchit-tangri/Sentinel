from fastapi import FastAPI

app = FastAPI(title="Sentinel Multi-Agent API", description="Backend for Sentinel Autonomous Security Patching Framework")

@app.get("/")
def read_root():
    return {"message": "Welcome to Sentinel API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
