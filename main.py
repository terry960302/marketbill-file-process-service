from fastapi import FastAPI, Request
from controllers.root_controller import health_check
from controllers.process_controller import handle_receipt_process
from concurrent.futures.process import ProcessPoolExecutor
import asyncio

app = FastAPI()


async def run_in_process(fn, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(app.state.executor, fn, *args)


@app.on_event("startup")
async def on_startup():
    app.state.executor = ProcessPoolExecutor()


@app.on_event("shutdown")
async def on_shutdown():
    app.state.executor.shutdown()


@app.get("/")
def handle_root():
    return health_check()


@app.post("/")
async def handle_receipt(request: Request):
    json_object = await request.json()
    return await run_in_process(handle_receipt_process, json_object)

    # return handle_receipt_process(json_object)
