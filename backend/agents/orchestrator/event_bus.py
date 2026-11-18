import asyncio
import logging
from datetime import datetime
from typing import Dict, Set, Any, Optional, List
from fastapi import WebSocket

logger = logging.getLogger("Sentinel.EventBus")


class SessionEventBus:
    """
    Real-Time WebSocket Event Bus for Sentinel v1.0 Multi-Agent Studio.
    Handles:
      - Connection multiplexing per session_id.
      - Streaming structured telemetry events: AGENT_STATE, CURSOR_MOVE, VULN_DETECTED, LIVE_DIFF_CHUNK.
      - Interactive Vibe Coding pause/approval coordination via asyncio.Event.
      - Persona-aware message styling (cyberpunk, principal_engineer, mentor).
    """

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.pending_approvals: Dict[str, asyncio.Event] = {}
        self.approval_payloads: Dict[str, Dict[str, Any]] = {}
        self.event_history: Dict[str, List[Dict[str, Any]]] = {}

    async def register(self, session_id: str, websocket: WebSocket) -> None:
        """Registers a new WebSocket connection for a given session."""
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
        logger.info(f"[EventBus] WebSocket registered for session {session_id} (Total: {len(self.active_connections[session_id])})")

    async def unregister(self, session_id: str, websocket: WebSocket) -> None:
        """Unregisters a closed WebSocket connection."""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"[EventBus] WebSocket disconnected for session {session_id}")

    async def broadcast(self, session_id: str, event: Dict[str, Any]) -> None:
        """Broadcasts a telemetry event to all connected clients for a session."""
        # Record in history
        if session_id not in self.event_history:
            self.event_history[session_id] = []
        event_with_ts = {**event, "timestamp": datetime.utcnow().isoformat()}
        self.event_history[session_id].append(event_with_ts)

        connections = self.active_connections.get(session_id, set())
        if not connections:
            return

        dead_connections = set()
        for ws in connections:
            try:
                await ws.send_json(event_with_ts)
            except Exception as e:
                logger.warning(f"[EventBus] Failed to send event to WebSocket in session {session_id}: {e}")
                dead_connections.add(ws)

        for dead in dead_connections:
            connections.discard(dead)

    def emit_sync(self, session_id: str, event: Dict[str, Any]) -> None:
        """Synchronous wrapper to broadcast events when running inside an event loop."""
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                asyncio.create_task(self.broadcast(session_id, event))
        except RuntimeError:
            # No running event loop; record event in history
            if session_id not in self.event_history:
                self.event_history[session_id] = []
            self.event_history[session_id].append({**event, "timestamp": datetime.utcnow().isoformat()})

    # -------------------------------------------------------------------------
    # Vibe Coding Interactive Approval Synchronization
    # -------------------------------------------------------------------------
    async def wait_for_approval(
        self,
        session_id: str,
        finding_id: Optional[str] = None,
        timeout: Optional[float] = 180.0
    ) -> Dict[str, Any]:
        """
        Pauses execution in vibe_interactive mode until an APPROVE_FIX command
        is received over the WebSocket.
        """
        key = f"{session_id}:{finding_id}" if finding_id else session_id
        event = asyncio.Event()
        self.pending_approvals[key] = event
        self.pending_approvals[session_id] = event

        try:
            if timeout:
                await asyncio.wait_for(event.wait(), timeout=timeout)
            else:
                await event.wait()
            return self.approval_payloads.get(key) or self.approval_payloads.get(session_id) or {}
        except asyncio.TimeoutError:
            logger.warning(f"[EventBus] Approval timed out for session {session_id}, finding {finding_id}")
            return {
                "action": "AUTO_APPROVE_TIMEOUT",
                "selected_strategy": "Default recommended architectural remediation",
                "custom_instruction": ""
            }
        finally:
            self.pending_approvals.pop(key, None)
            self.pending_approvals.pop(session_id, None)

    def submit_approval(self, session_id: str, command: Dict[str, Any]) -> bool:
        """
        Resolves a pending approval when the client sends APPROVE_FIX.
        """
        finding_id = command.get("finding_id")
        key = f"{session_id}:{finding_id}" if finding_id else session_id

        self.approval_payloads[key] = command
        self.approval_payloads[session_id] = command

        event = self.pending_approvals.get(key) or self.pending_approvals.get(session_id)
        if event:
            event.set()
            return True
        return False

    # -------------------------------------------------------------------------
    # Persona Message Styler
    # -------------------------------------------------------------------------
    @staticmethod
    def style_message(
        agent: str,
        stage: str,
        detail: str = "",
        persona: str = "principal_engineer"
    ) -> str:
        """Generates thematic persona-tailored status messages."""
        if persona == "cyberpunk":
            mapping = {
                ("dex", "thinking"): f"Dex jacked into root terminal. Probing perimeter defense grid. {detail}".strip(),
                ("pixel", "editing"): f"Pixel running neural synthesis at 5.2GHz. Injecting fortified bytecode. {detail}".strip(),
                ("snooze", "scanning"): f"Snooze scanning memory segments and AST vectors. {detail}".strip(),
                ("snooze", "waiting_approval"): f"Snooze identified threat signature. Holding ICE breach pending operator authorization.",
                ("glitch", "editing"): f"Glitch deploying surgical exploit neutralization subroutine. {detail}".strip(),
                ("glitch", "completed"): "Glitch confirmed target patched and secured. Neutralization complete.",
            }
        elif persona == "mentor":
            mapping = {
                ("dex", "thinking"): f"Dex is analyzing the architecture to make sure our security boundaries are clean. {detail}".strip(),
                ("pixel", "editing"): f"Pixel is writing safe, maintainable code following industry best practices. {detail}".strip(),
                ("snooze", "scanning"): f"Snooze is performing a comprehensive security audit of our files. {detail}".strip(),
                ("snooze", "waiting_approval"): f"Snooze found potential security issues. Let's review the options together before patching.",
                ("glitch", "editing"): f"Glitch is applying your chosen fix without modifying business logic. {detail}".strip(),
                ("glitch", "completed"): "Glitch verified the patch is clean, tested, and secure!",
            }
        else:  # principal_engineer
            mapping = {
                ("dex", "thinking"): f"Dex formulating formal trust boundaries and architectural invariants. {detail}".strip(),
                ("pixel", "editing"): f"Pixel synthesizing production-grade implementation via OmniRoute. {detail}".strip(),
                ("snooze", "scanning"): f"Snooze auditing code against OWASP Top 10 and CWE taxonomies. {detail}".strip(),
                ("snooze", "waiting_approval"): "Snooze identified security findings. Paused for interactive architectural review.",
                ("glitch", "editing"): f"Glitch executing zero-regression surgical remediation. {detail}".strip(),
                ("glitch", "completed"): "Glitch verified zero AST drift and certified remediation integrity.",
            }

        return mapping.get((agent, stage), detail or f"{agent.capitalize()} is {stage}.")
