import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from simulation import Simulation

app = FastAPI()
sim = Simulation()

STATIC_DIR = Path(__file__).parent / "static"
TICK_HZ = 30
DT = 1.0 / TICK_HZ
clients: set[WebSocket] = set()


def state_payload() -> str:
    s = sim.state
    m = sim.mesh
    ex = m.extent
    return json.dumps({
        "cart": {
            "x": round(s.x, 3),
            "y": round(s.y, 3),
            "angle": round(s.angle, 3),
            "left_speed": s.left_speed,
            "right_speed": s.right_speed,
            "target": list(s.target) if s.target else None,
        },
        "anchors": [
            {"id": a.id, "x": a.x, "y": a.y}
            for a in m.anchors.values()
        ],
        "distances": {k: round(v, 3) for k, v in sim.last_distances.items()},
        "estimate": (
            [round(sim.last_estimate[0], 3), round(sim.last_estimate[1], 3)]
            if sim.last_estimate else None
        ),
        "mesh": {
            "min_x": ex[0], "min_y": ex[1],
            "max_x": ex[2], "max_y": ex[3],
            "noise_std": m.noise_std,
        },
    })


async def simulation_loop():
    while True:
        sim.tick(DT)
        payload = state_payload()
        dead = []
        for ws in list(clients):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            clients.discard(ws)
        await asyncio.sleep(DT)


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(simulation_loop())


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    await ws.send_text(state_payload())
    try:
        while True:
            raw = await ws.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                sim.set_command(raw.strip().lower())
                continue

            kind = data.get("type")
            if kind == "command":
                sim.set_command(str(data["value"]))
            elif kind == "target":
                sim.set_target(float(data["x"]), float(data["y"]))
            elif kind == "clear_target":
                sim.clear_target()
            elif kind == "noise":
                sim.set_noise(float(data["value"]))
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(ws)


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)