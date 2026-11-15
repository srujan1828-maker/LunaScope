"""
WebSocket Real-Time Simulation Handler.
Streams live physics, topocentric coordinates, power telemetry, and predictive events to clients.
"""

import asyncio
import json
import time
from typing import Dict, Any, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.simulation_engine import RealtimeSimulationSession
from app.data.sites_catalog import get_sites_catalog

ws_router = APIRouter()


class SimulationConnectionManager:
    """Manages active WebSocket connections and their associated simulation sessions."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.sessions: Dict[WebSocket, RealtimeSimulationSession] = {}
        self.tasks: Dict[WebSocket, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        # Default session starting Jan 1, 2027 00:00:00 UTC (1735689600.0)
        default_session = await asyncio.to_thread(RealtimeSimulationSession,
            site_ids=[s["site_id"] for s in get_sites_catalog()[:2]],
            start_unix=1798761600.0,
            mast_height_m=2.0,
            speed_multiplier=60.0
        )
        self.sessions[websocket] = default_session

        # Send initial state frame
        initial_frame = await asyncio.to_thread(default_session.compute_frame,dt_seconds=0.0)
        await websocket.send_json({
            "type": "session_init",
            "message": "Connected to LunaScope Real-Time Simulation Engine",
            "frame": initial_frame
        })

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.sessions:
            del self.sessions[websocket]
        if websocket in self.tasks:
            self.tasks[websocket].cancel()
            del self.tasks[websocket]

    async def start_streaming(self, websocket: WebSocket):
        session = self.sessions.get(websocket)
        if not session:
            return

        session.is_running = True

        async def stream_loop():
            tick_rate_hz = 5.0  # 5 updates per real second
            tick_interval = 1.0 / tick_rate_hz

            try:
                while session.is_running and websocket in self.active_connections:
                    # Simulated seconds per tick = tick_interval * speed_multiplier
                    sim_dt = tick_interval * session.speed_multiplier
                    frame = await asyncio.to_thread(session.advance_time,sim_dt)
                    await websocket.send_json(frame)
                    await asyncio.sleep(tick_interval)
            except (asyncio.CancelledError, WebSocketDisconnect):
                pass
            except Exception as e:
                try:
                    await websocket.send_json({"type": "error", "message": str(e)})
                except Exception:
                    pass

        # Cancel any existing task
        if websocket in self.tasks:
            self.tasks[websocket].cancel()
        self.tasks[websocket] = asyncio.create_task(stream_loop())

    def pause_streaming(self, websocket: WebSocket):
        session = self.sessions.get(websocket)
        if session:
            session.is_running = False
        if websocket in self.tasks:
            self.tasks[websocket].cancel()


manager = SimulationConnectionManager()


@ws_router.websocket("/ws/simulation")
async def websocket_simulation_endpoint(websocket: WebSocket):
    from app.core.nasa_data import readiness
    if not readiness()['ready']:
        await websocket.accept()
        await websocket.send_json({'type':'error','message':'Official NASA files are not installed. No synthetic fallback is used.'})
        await websocket.close(code=1013)
        return
    await manager.connect(websocket)
    try:
        while True:
            data_text = await websocket.receive_text()
            try:
                msg = json.loads(data_text)
            except Exception:
                await websocket.send_json({"type": "error", "message": "Invalid JSON format"})
                continue

            import math
            if not isinstance(msg,dict):
                await websocket.send_json({'type':'error','message':'Expected command object'})
                continue
            valid = True
            for key, lo, hi in [('speed',0.1,3600),('dt_seconds',0,86400),('mast_height_m',0.5,30),('timestamp_unix',1735689600,1988150400)]:
                if key in msg:
                    try:
                        value = float(msg[key])
                        valid = valid and math.isfinite(value) and lo <= value <= hi
                    except (ValueError,TypeError):
                        valid = False
            if not valid:
                await websocket.send_json({'type':'error','message':'Command value outside supported limits'})
                continue
            cmd = msg.get("command")
            session = manager.sessions.get(websocket)

            if not session:
                break

            if cmd == "start":
                # Start or resume streaming
                if "speed" in msg:
                    session.speed_multiplier = float(msg["speed"])
                await manager.start_streaming(websocket)

            elif cmd == "pause":
                manager.pause_streaming(websocket)
                await websocket.send_json({"type": "status", "is_running": False})

            elif cmd == "step":
                # Single step forward or backward
                manager.pause_streaming(websocket)
                dt = float(msg.get("dt_seconds", 3600.0))
                frame = await asyncio.to_thread(session.advance_time,dt)
                await websocket.send_json(frame)

            elif cmd == "seek":
                target_unix = float(msg.get("timestamp_unix", session.current_unix))
                manager.pause_streaming(websocket)
                session.battery_energy_wh = {sid: session.battery_capacity_wh * getattr(session,"initial_soc_pct",100)/100 for sid in session.site_ids}
                session.current_unix = target_unix
                frame = await asyncio.to_thread(session.compute_frame,dt_seconds=0.0)
                await websocket.send_json(frame)

            elif cmd == "set_speed":
                session.speed_multiplier = float(msg.get("speed", 60.0))
                await websocket.send_json({"type": "status", "speed_multiplier": session.speed_multiplier})

            elif cmd == "set_mast":
                new_mast = float(msg.get("mast_height_m", 2.0))
                await asyncio.to_thread(session.update_mast_height,new_mast)
                frame = await asyncio.to_thread(session.compute_frame,dt_seconds=0.0)
                await websocket.send_json(frame)

            elif cmd == "configure":
                from app.api.schemas import PowerConfig
                from pydantic import ValidationError
                try:
                    cfg = PowerConfig.model_validate(msg.get('power_config', {}))
                    margin = float(msg.get('antenna_margin_deg',0))
                    if not math.isfinite(margin) or not 0 <= margin <= 10:
                        raise ValueError('Invalid antenna margin')
                    session.antenna_margin_deg = margin
                    changed = session.battery_capacity_wh != cfg.battery_capacity_wh
                    session.spacecraft_load_w = cfg.spacecraft_load_w
                    session.panel_area_m2 = cfg.panel_area_m2
                    session.panel_efficiency = cfg.panel_efficiency
                    session.panel_orientation = cfg.panel_orientation
                    for key in ['fixed_azimuth_deg','derating_factor','charge_efficiency','discharge_efficiency']:
                        setattr(session,key,getattr(cfg,key))
                    session.reserve_margin_pct = cfg.reserve_margin_pct
                    session.battery_capacity_wh = cfg.battery_capacity_wh
                    session.initial_soc_pct = cfg.initial_soc_pct
                    if changed:
                        session.battery_energy_wh = {sid: cfg.battery_capacity_wh * cfg.initial_soc_pct/100 for sid in session.site_ids}
                    await websocket.send_json(await asyncio.to_thread(session.compute_frame))
                except (ValueError,TypeError,ValidationError) as exc:
                    await websocket.send_json({'type':'error','message':str(exc)})

            elif cmd == "select_sites":
                new_sites = msg.get("site_ids", session.site_ids)
                from app.data.sites_catalog import get_site_by_id
                if not isinstance(new_sites,list) or not 1 <= len(new_sites) <= 3 or any(not get_site_by_id(s) for s in new_sites):
                    await websocket.send_json({'type':'error','message':'Select 1 to 3 known sites'})
                    continue
                was_running = session.is_running
                manager.pause_streaming(websocket)
                replacement = await asyncio.to_thread(RealtimeSimulationSession,new_sites, session.current_unix,
                    session.mast_height_m, session.antenna_margin_deg, session.speed_multiplier,
                    session.spacecraft_load_w, session.panel_area_m2, session.battery_capacity_wh)
                for sid in new_sites:
                    replacement.battery_energy_wh[sid] = session.battery_energy_wh.get(sid,replacement.battery_energy_wh[sid])
                for key in ["panel_efficiency", "panel_orientation", "reserve_margin_pct", "initial_soc_pct",'fixed_azimuth_deg','derating_factor','charge_efficiency','discharge_efficiency']:
                    if hasattr(session,key): setattr(replacement,key,getattr(session,key))
                session = replacement
                manager.sessions[websocket] = session
                if was_running:
                    await manager.start_streaming(websocket)
                frame = await asyncio.to_thread(session.compute_frame,dt_seconds=0.0)
                await websocket.send_json(frame)

            else:
                await websocket.send_json({"type": "error", "message": f"Unknown command: {cmd}"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
