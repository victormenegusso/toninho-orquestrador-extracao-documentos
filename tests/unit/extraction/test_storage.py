"""
Testes unitários para o módulo de storage.
"""

import pytest

from toninho.extraction.storage import (
    LocalFileSystemStorage,
    get_storage,
)


class TestLocalFileSystemStorage:
    """Testes para LocalFileSystemStorage."""

    @pytest.fixture
    def storage(self, tmp_path):
        return LocalFileSystemStorage(base_dir=str(tmp_path))

    # ──────────────────────────────────────────────────────── save_file ──

    @pytest.mark.asyncio
    async def test_save_file_creates_file(self, storage, tmp_path):
        """save_file deve criar o arquivo no caminho indicado."""
        content = b"Hello, World!"
        saved_path = await storage.save_file("test.txt", content)

        assert (tmp_path / "test.txt").exists()
        assert (tmp_path / "test.txt").read_bytes() == content
        assert saved_path == str(tmp_path / "test.txt")

    @pytest.mark.asyncio
    async def test_save_file_creates_nested_dirs(self, storage, tmp_path):
        """save_file deve criar diretórios intermediários."""
        content = b"nested content"
        await storage.save_file("a/b/c/file.md", content)

        assert (tmp_path / "a" / "b" / "c" / "file.md").exists()

    @pytest.mark.asyncio
    async def test_save_file_overwrites_existing(self, storage):
        """save_file deve sobrescrever arquivo existente."""
        await storage.save_file("file.txt", b"old")
        await storage.save_file("file.txt", b"new")

        result = await storage.get_file("file.txt")
        assert result == b"new"

    # ──────────────────────────────────────────────────────── get_file ───

    @pytest.mark.asyncio
    async def test_get_file_reads_content(self, storage):
        """get_file deve retornar o conteúdo salvo."""
        await storage.save_file("read.txt", b"content")
        result = await storage.get_file("read.txt")
        assert result == b"content"

    @pytest.mark.asyncio
    async def test_get_file_not_found_raises(self, storage):
        """get_file deve levantar FileNotFoundError para arquivos inexistentes."""
        with pytest.raises(FileNotFoundError):
            await storage.get_file("nonexistent.txt")

    # ─────────────────────────────────────────────────────── delete_file ─

    @pytest.mark.asyncio
    async def test_delete_file_existing(self, storage, tmp_path):
        """delete_file deve remover arquivo e retornar True."""
        await storage.save_file("del.txt", b"bye")
        result = await storage.delete_file("del.txt")

        assert result is True
        assert not (tmp_path / "del.txt").exists()

    @pytest.mark.asyncio
    async def test_delete_file_nonexistent_returns_false(self, storage):
        """delete_file deve retornar False se arquivo não existe."""
        result = await storage.delete_file("ghost.txt")
        assert result is False

    # ─────────────────────────────────────────────────────── list_files ──

    @pytest.mark.asyncio
    async def test_list_files_empty_dir(self, storage):
        """list_files em diretório vazio deve retornar lista vazia."""
        result = await storage.list_files("empty_dir")
        assert result == []

    @pytest.mark.asyncio
    async def test_list_files_returns_relative_paths(self, storage):
        """list_files deve retornar caminhos relativos ao base_dir."""
        await storage.save_file("subdir/a.md", b"a")
        await storage.save_file("subdir/b.md", b"b")

        result = await storage.list_files("subdir")
        assert len(result) == 2
        assert all(r.startswith("subdir") for r in result)

    @pytest.mark.asyncio
    async def test_list_files_recursive(self, storage):
        """list_files deve listar recursivamente."""
        await storage.save_file("d/x/file1.md", b"1")
        await storage.save_file("d/y/file2.md", b"2")

        result = await storage.list_files("d")
        assert len(result) == 2

    # ────────────────────────────────────────────────────────── exists ───

    def test_exists_true(self, storage, tmp_path):
        """exists deve retornar True para arquivos existentes."""
        (tmp_path / "existing.txt").write_bytes(b"data")
        assert storage.exists("existing.txt") is True

    def test_exists_false(self, storage):
        """exists deve retornar False para arquivos inexistentes."""
        assert storage.exists("no.txt") is False


class TestGetStorageFactory:
    """Testes para a factory get_storage."""

    def test_local_storage(self, tmp_path):
        storage = get_storage("local", base_dir=str(tmp_path))
        assert isinstance(storage, LocalFileSystemStorage)

    def test_s3_not_implemented(self):
        with pytest.raises(NotImplementedError):
            get_storage("s3")

    def test_unknown_type(self):
        with pytest.raises(ValueError, match="desconhecido"):
            get_storage("gcs")

    def test_local_default_base_dir(self, tmp_path, monkeypatch):
        """get_storage sem base_dir usa './output'."""
        # Apenas verificar que não levanta exceção
        storage = get_storage("local", base_dir=str(tmp_path))
        assert storage is not None
