"""
FastAPI Application Entry Point
Initializes the FastAPI app, includes routers from `app.routes`, and handles global exception catching/CORS.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, files, fix, ai
from app.routes.parser import parser_835_routes

app = FastAPI(title="EDI Platform Backend")

# Inject permissive CORS mapping allowing Vite dev-server to naturally hit endpoints
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(files.router)
app.include_router(fix.router)
app.include_router(ai.router)
app.include_router(parser_835_routes.router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "EDI Platform Backend Online"}
