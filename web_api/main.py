import asyncio
from typing import List

from database import get_table_feed, Database
from models import Agent, RecordType, Record, Property, PropertyPage, NotFound
from websocket_manager import WebSocketManager

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect


app = FastAPI(
    title="Paas4Chain API",
    description="API for querying Blockchain state.")
db = Database()
manager = WebSocketManager()
updates_queue = asyncio.Queue()
background_tasks = []  # A reference needs to be kept, or tasks die


@app.get("/agents", response_model=List[Agent])
async def agents():
    return await db.get_agents()


@app.get("/record_types", response_model=List[RecordType])
async def record_types():
    return await db.get_record_types()


@app.get("/records", response_model=List[Record])
async def records():
    return await db.get_records()


@app.get(
    "/property_page/{record_id}/{property_name}/{page_num}",
    response_model=PropertyPage,
    response_model_exclude_unset=True,
    responses={"404": {"model": NotFound}})
async def record_property_page(record_id: str, property_name: str, page_num: int):
    return await db.get_property_page(record_id, property_name, page_num)


@app.get("/properties/{record_id}", response_model=List[Property], responses={"404": {"model": NotFound}})
async def record_properties(record_id: str):
    return await db.get_properties(record_id)


@app.get("/property/{record_id}/{property_name}", response_model=Property, responses={"404": {"model": NotFound}})
async def record_property(record_id: str, property_name: str):
    return await db.get_property(record_id, property_name)


@app.websocket("/ws/feed")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            _ = await websocket.receive_text()  # Keeping the websocket open
    except WebSocketDisconnect:
        print("WS Client disconnected!")
        manager.disconnect(websocket)


async def table_change_task(table):
    feed = await get_table_feed(table)
    while await feed.fetch_next():
        change = await feed.next()
        await updates_queue.put({"updated_table": table, **change})


async def change_broadcaster_task():
    while True:
        change = await updates_queue.get()
        await manager.broadcast(change)
        updates_queue.task_done()


@app.on_event("startup")
async def tasks_setup():
    background_tasks.append(asyncio.create_task(table_change_task("blocks")))
    background_tasks.append(asyncio.create_task(table_change_task("agents")))
    background_tasks.append(asyncio.create_task(table_change_task("recordTypes")))
    background_tasks.append(asyncio.create_task(change_broadcaster_task()))
    await db.connect()
