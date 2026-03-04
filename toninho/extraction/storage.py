"""
Interfaces e implementações de storage para arquivos extraídos.

Abstrai o acesso a diferentes backends de armazenamento
(filesystem local, S3, etc).
"""

from abc import ABC, abstractmethod
from pathlib import Path


class StorageInterface(ABC):
    """Interface abstrata para diferentes tipos de armazenamento."""

    @abstractmethod
    async def save_file(self, path: str, content: bytes) -> str:
        """Salva arquivo e retorna o caminho/URL completo."""
        ...

    @abstractmethod
    async def get_file(self, path: str) -> bytes:
        """Recupera conteúdo do arquivo."""
        ...

    @abstractmethod
    async def delete_file(self, path: str) -> bool:
        """Deleta arquivo. Retorna True se deletado, False se não existia."""
        ...

    @abstractmethod
    async def list_files(self, directory: str) -> list[str]:
        """Lista arquivos em um diretório (caminhos relativos ao base_dir)."""
        ...

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Verifica se arquivo existe."""
        ...


class LocalFileSystemStorage(StorageInterface):
    """Implementação de storage para filesystem local."""

    def __init__(self, base_dir: str = "./output"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, path: str, content: bytes) -> str:
        """
        Salva arquivo no filesystem local.

        Args:
            path: Caminho relativo ao base_dir
            content: Conteúdo em bytes

        Returns:
            Caminho absoluto do arquivo salvo
        """
        full_path = self.base_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        full_path.write_bytes(content)
        return str(full_path)

    async def get_file(self, path: str) -> bytes:
        """
        Lê arquivo do filesystem local.

        Args:
            path: Caminho relativo ao base_dir

        Raises:
            FileNotFoundError: Se o arquivo não existir
        """
        full_path = self.base_dir / path
        if not full_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")
        return full_path.read_bytes()

    async def delete_file(self, path: str) -> bool:
        """
        Deleta arquivo do filesystem local.

        Returns:
            True se o arquivo foi deletado, False se não existia
        """
        full_path = self.base_dir / path
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    async def list_files(self, directory: str) -> list[str]:
        """
        Lista todos os arquivos dentro de um diretório.

        Returns:
            Lista de caminhos relativos ao base_dir
        """
        dir_path = self.base_dir / directory
        if not dir_path.exists():
            return []
        return [
            str(f.relative_to(self.base_dir))
            for f in dir_path.rglob("*")
            if f.is_file()
        ]

    def exists(self, path: str) -> bool:
        """Verifica se arquivo existe no filesystem."""
        return (self.base_dir / path).exists()


def get_storage(storage_type: str = "local", **kwargs) -> StorageInterface:
    """
    Factory para criar instância de storage.

    Args:
        storage_type: Tipo de storage ("local" suportado por ora)
        **kwargs: Argumentos específicos para o tipo de storage

    Returns:
        Instância de StorageInterface

    Raises:
        NotImplementedError: Se o tipo não for implementado
        ValueError: Se o tipo não for reconhecido
    """
    if storage_type == "local":
        base_dir = kwargs.get("base_dir", "./output")
        return LocalFileSystemStorage(base_dir=base_dir)
    elif storage_type == "s3":
        raise NotImplementedError("S3 storage não implementado ainda")
    else:
        raise ValueError(f"Tipo de storage desconhecido: {storage_type}")
