from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(title = settings.APP_NAME, debug=settings.DEBUG)


@app.get('/')
def welcome():
    return {"message": "Welcome to the app"}