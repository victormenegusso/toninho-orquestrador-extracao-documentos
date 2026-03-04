"""
WebSocket manager para atualizações em tempo real.

Gerencia conexões WebSocket para o dashboard e por execução.
"""

from fastapi import WebSocket
from loguru import logger


class WebSocketManager:
    """Gerencia conexões WebSocket para real-time updates."""

    def __init__(self):
        # Connections por execução
        self.active_connections: dict[str, set[WebSocket]] = {}

        # Connections globais (dashboard)
        self.global_connections: set[WebSocket] = set()

    async def connect(
        self, websocket: WebSocket, execucao_id: str | None = None
    ) -> None:
        """Adiciona nova conexão WebSocket."""
        await websocket.accept()

        if execucao_id:
            if execucao_id not in self.active_connections:
                self.active_connections[execucao_id] = set()
            self.active_connections[execucao_id].add(websocket)
            logger.info(f"WebSocket connected for execucao {execucao_id}")
        else:
            self.global_connections.add(websocket)
            logger.info("WebSocket connected to global channel")

    def disconnect(self, websocket: WebSocket, execucao_id: str | None = None) -> None:
        """Remove conexão WebSocket."""
        if execucao_id:
            if execucao_id in self.active_connections:
                self.active_connections[execucao_id].discard(websocket)
                if not self.active_connections[execucao_id]:
                    del self.active_connections[execucao_id]
        else:
            self.global_connections.discard(websocket)

    async def broadcast_to_execucao(self, execucao_id: str, message: dict) -> None:
        """Envia mensagem para todos conectados a uma execução."""
        if execucao_id not in self.active_connections:
            return

        disconnected: set[WebSocket] = set()

        for connection in list(self.active_connections[execucao_id]):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(
                    f"Error sending WebSocket message to execucao {execucao_id}: {e}"
                )
                disconnected.add(connection)

        for conn in disconnected:
            self.disconnect(conn, execucao_id)

    async def broadcast_global(self, message: dict) -> None:
        """Envia mensagem para todas as conexões globais."""
        disconnected: set[WebSocket] = set()

        for connection in list(self.global_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending global WebSocket message: {e}")
                disconnected.add(connection)

        for conn in disconnected:
            self.disconnect(conn)

    def get_connection_count(self, execucao_id: str | None = None) -> int:
        """Retorna número de conexões ativas."""
        if execucao_id:
            return len(self.active_connections.get(execucao_id, set()))
        return len(self.global_connections)

    def get_all_execucao_ids(self) -> list:
        """Retorna IDs de execuções com conexões ativas."""
        return list(self.active_connections.keys())


# Singleton global
ws_manager = WebSocketManager()
