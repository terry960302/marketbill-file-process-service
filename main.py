from fastapi import FastAPI, Request
from handler.root_handler import health_check
from handler.process_handler import handle_receipt_process

app = FastAPI()


@app.get("/")
def handle_root():
    return health_check()


@app.post("/")
async def handle_receipt(request: Request):
    json_object = await request.json()
    return handle_receipt_process(json_object)
