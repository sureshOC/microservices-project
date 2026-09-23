from fastapi import FastAPI
from pydantic import BaseModel
import time

app = FastAPI()


@app.get("/users/{user_id}")
def get_user(user_id: int):

    time.sleep(1)
    return {
        # "id": user_id,
        'id': user_id,
        "name": "Suresh",
        "email": "suresh@example.com"
    }


