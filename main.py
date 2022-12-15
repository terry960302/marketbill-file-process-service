from fastapi import FastAPI, Request
from controllers.root_controller import health_check
from controllers.process_controller import handle_receipt_process

app = FastAPI()


@app.get("/")
def handle_root():
    return health_check()


@app.post("/")
async def handle_receipt(request: Request):
    json_object = await request.json()
    return handle_receipt_process(json_object)
