from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, groups, session, questions, comments, dashboard
from app.core.config import settings
from app.websocket.routes import router as ws_router

#from app.db.base import Base  # to be removed after create alembic migrations and run alembic upgrade head
#from app.db.session import engine #to be removed after create alembic migrations and run alembic upgrade head


app = FastAPI(title=settings.app_name.capitalize())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # add frontend url here
    allow_methods=["*"], 
    allow_headers=["*"], # for authorization header, you can add "Authorization" here if you want to restrict it
)

#Base.metadata.create_all(bind=engine) # to be removed after create alembic migrations and run alembic upgrade head

app.include_router(auth.router, prefix="/api/v1")
app.include_router(groups.router, prefix="/api/v1")
app.include_router(session.router, prefix="/api/v1")
app.include_router(questions.router, prefix="/api/v1")
app.include_router(comments.router, prefix="/api/v1")
app.include_router(dashboard.router, prefex="/api/v1")
app.include_router(ws_router)


@app.get("/", status_code=200)
def health_check():
    return {"status": "ok", "app": settings.app_name}


