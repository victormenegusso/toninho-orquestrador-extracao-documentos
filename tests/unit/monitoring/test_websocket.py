"""Testes para o WebSocketManager."""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestWebSocketManager:
    """Testes para o WebSocketManager."""

    @pytest.fixture
    def manager(self):
        """Fixture que cria um WebSocketManager limpo para cada teste."""
        from toninho.monitoring.websocket import WebSocketManager

        return WebSocketManager()

    def _make_websocket(self, fail_send=False):
        """Cria um mock de WebSocket."""
        ws = MagicMock()
        ws.accept = AsyncMock()
        if fail_send:
            ws.send_json = AsyncMock(side_effect=Exception("Connection lost"))
        else:
            ws.send_json = AsyncMock()
        ws.send_text = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect_global(self, manager):
        """Conexão global é adicionada ao global_connections."""
        ws = self._make_websocket()
        await manager.connect(ws)

        ws.accept.assert_called_once()
        assert ws in manager.global_connections

    @pytest.mark.asyncio
    async def test_connect_to_execucao(self, manager):
        """Conexão por execução é adicionada ao active_connections."""
        ws = self._make_websocket()
        await manager.connect(ws, execucao_id="exec-1")

        ws.accept.assert_called_once()
        assert "exec-1" in manager.active_connections
        assert ws in manager.active_connections["exec-1"]

    @pytest.mark.asyncio
    async def test_connect_multiple_to_same_execucao(self, manager):
        """Múltiplas conexões para a mesma execução."""
        ws1 = self._make_websocket()
        ws2 = self._make_websocket()

        await manager.connect(ws1, execucao_id="exec-1")
        await manager.connect(ws2, execucao_id="exec-1")

        assert len(manager.active_connections["exec-1"]) == 2

    def test_disconnect_global(self, manager):
        """Desconexão global remove do global_connections."""
        ws = self._make_websocket()
        manager.global_connections.add(ws)

        manager.disconnect(ws)
        assert ws not in manager.global_connections

    def test_disconnect_execucao(self, manager):
        """Desconexão de execução remove do active_connections."""
        ws = self._make_websocket()
        manager.active_connections["exec-1"] = {ws}

        manager.disconnect(ws, execucao_id="exec-1")
        assert "exec-1" not in manager.active_connections

    def test_disconnect_execucao_leaves_others(self, manager):
        """Desconexão de um WS não remove outros da mesma execução."""
        ws1 = self._make_websocket()
        ws2 = self._make_websocket()
        manager.active_connections["exec-1"] = {ws1, ws2}

        manager.disconnect(ws1, execucao_id="exec-1")
        assert "exec-1" in manager.active_connections
        assert ws2 in manager.active_connections["exec-1"]

    def test_disconnect_nonexistent_global(self, manager):
        """Desconectar WS que não existe não gera erro."""
        ws = self._make_websocket()
        manager.disconnect(ws)  # Não deve lançar exceção

    def test_disconnect_nonexistent_execucao(self, manager):
        """Desconectar execucao inexistente não gera erro."""
        ws = self._make_websocket()
        manager.disconnect(ws, execucao_id="nonexistent")  # Não deve lançar exceção

    @pytest.mark.asyncio
    async def test_broadcast_to_execucao(self, manager):
        """Broadcast envia mensagem para WebSockets da execução."""
        ws = self._make_websocket()
        manager.active_connections["exec-1"] = {ws}

        message = {"type": "status_update", "data": {"status": "em_execucao"}}
        await manager.broadcast_to_execucao("exec-1", message)

        ws.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_execucao_no_connections(self, manager):
        """Broadcast sem conexões não gera erro."""
        message = {"type": "test"}
        await manager.broadcast_to_execucao(
            "exec-nonexistent", message
        )  # Não deve lançar

    @pytest.mark.asyncio
    async def test_broadcast_to_execucao_removes_failed(self, manager):
        """Conexão com falha é removida durante broadcast."""
        ws = self._make_websocket(fail_send=True)
        manager.active_connections["exec-1"] = {ws}

        await manager.broadcast_to_execucao("exec-1", {"type": "test"})

        assert "exec-1" not in manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_global(self, manager):
        """Broadcast global envia para todas as conexões globais."""
        ws1 = self._make_websocket()
        ws2 = self._make_websocket()
        manager.global_connections = {ws1, ws2}

        message = {"type": "execution_update", "data": {}}
        await manager.broadcast_global(message)

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_global_removes_failed(self, manager):
        """Conexão global com falha é removida durante broadcast."""
        ws = self._make_websocket(fail_send=True)
        manager.global_connections = {ws}

        await manager.broadcast_global({"type": "test"})

        assert ws not in manager.global_connections

    def test_get_connection_count_global(self, manager):
        """Retorna contagem de conexões globais."""
        ws1 = self._make_websocket()
        ws2 = self._make_websocket()
        manager.global_connections = {ws1, ws2}

        assert manager.get_connection_count() == 2

    def test_get_connection_count_execucao(self, manager):
        """Retorna contagem de conexões por execução."""
        ws = self._make_websocket()
        manager.active_connections["exec-1"] = {ws}

        assert manager.get_connection_count(execucao_id="exec-1") == 1
        assert manager.get_connection_count(execucao_id="nonexistent") == 0

    def test_get_all_execucao_ids(self, manager):
        """Retorna IDs de execuções com conexões ativas."""
        ws = self._make_websocket()
        manager.active_connections["exec-1"] = {ws}
        manager.active_connections["exec-2"] = {ws}

        ids = manager.get_all_execucao_ids()
        assert "exec-1" in ids
        assert "exec-2" in ids

    def test_singleton_exists(self):
        """Singleton ws_manager existe e é WebSocketManager."""
        from toninho.monitoring.websocket import WebSocketManager, ws_manager

        assert isinstance(ws_manager, WebSocketManager)
