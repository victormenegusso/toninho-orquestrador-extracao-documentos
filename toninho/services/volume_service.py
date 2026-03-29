"""Service para lógica de negócio de Volume."""

import os
from uuid import UUID

from sqlalchemy.orm import Session

from toninho.core.exceptions import ConflictError, NotFoundError, ValidationError
from toninho.models.enums import VolumeStatus, VolumeTipo
from toninho.models.volume import Volume
from toninho.repositories.volume_repository import VolumeRepository
from toninho.schemas.responses import PaginationMeta, SuccessListResponse
from toninho.schemas.volume import (
    VolumeCreate,
    VolumeResponse,
    VolumeSummary,
    VolumeUpdate,
    VolumeValidationResult,
)


class VolumeService:
    """Service para operações de negócio com Volume."""

    def __init__(self, repository: VolumeRepository):
        """
        Inicializa o service.

        Args:
            repository: Repository de Volume
        """
        self.repository = repository

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_volume(self, db: Session, volume_create: VolumeCreate) -> VolumeResponse:
        """
        Cria um novo volume.

        Args:
            db: Sessão do banco de dados
            volume_create: Dados para criação

        Returns:
            VolumeResponse com dados do volume criado

        Raises:
            ConflictError: Se já existe volume com mesmo nome ou path
            ValidationError: Se o path não é acessível
        """
        # 1. Normalizar path
        normalized_path = os.path.normpath(volume_create.path)

        # 2. Validar nome único
        if self.repository.exists_by_nome(db, volume_create.nome):
            raise ConflictError(
                f"Já existe um volume com o nome '{volume_create.nome}'"
            )

        # 3. Validar path único
        if self.repository.exists_by_path(db, normalized_path):
            raise ConflictError(f"Já existe um volume com o path '{normalized_path}'")

        # 4. Validar acesso ao path
        validation = self.validate_path_access(normalized_path)
        if not validation.valido:
            raise ValidationError(
                f"Path '{normalized_path}' não é acessível: {validation.erro}"
            )

        # 5. Criar model
        volume = Volume(
            nome=volume_create.nome,
            path=normalized_path,
            tipo=VolumeTipo.LOCAL,
            status=VolumeStatus.ATIVO,
            descricao=volume_create.descricao,
        )

        # 6. Salvar e retornar
        volume = self.repository.create(db, volume)
        return self._to_response(db, volume)

    def get_volume(self, db: Session, volume_id: UUID) -> VolumeResponse:
        """
        Busca um volume por ID.

        Args:
            db: Sessão do banco de dados
            volume_id: UUID do volume

        Returns:
            VolumeResponse com dados do volume

        Raises:
            NotFoundError: Se volume não existe
        """
        volume = self.repository.get_by_id(db, volume_id)
        if not volume:
            raise NotFoundError("Volume", str(volume_id))
        return self._to_response(db, volume)

    def list_volumes(
        self,
        db: Session,
        page: int = 1,
        per_page: int = 20,
        status: VolumeStatus | None = None,
        busca: str | None = None,
    ) -> SuccessListResponse[VolumeResponse]:
        """
        Lista volumes com paginação e filtros.

        Args:
            db: Sessão do banco de dados
            page: Número da página (1-indexed)
            per_page: Registros por página (1-100)
            status: Filtro por status (opcional)
            busca: Busca por nome (opcional)

        Returns:
            SuccessListResponse com lista paginada de VolumeResponse

        Raises:
            ValidationError: Se parâmetros inválidos
        """
        if page < 1:
            raise ValidationError("Número da página deve ser maior que 0")

        if per_page < 1 or per_page > 100:
            raise ValidationError("Registros por página deve estar entre 1 e 100")

        skip = (page - 1) * per_page

        volumes, total = self.repository.get_all(
            db=db,
            skip=skip,
            limit=per_page,
            status=status,
            busca=busca,
        )

        items = [self._to_response(db, v) for v in volumes]

        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        meta = PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
        )

        return SuccessListResponse(data=items, meta=meta)

    def get_volumes_ativos(self, db: Session) -> list[VolumeSummary]:
        """
        Lista volumes ativos para uso em combos/selects.

        Args:
            db: Sessão do banco de dados

        Returns:
            Lista de VolumeSummary dos volumes ativos
        """
        volumes = self.repository.get_ativos(db)
        return [VolumeSummary.model_validate(v) for v in volumes]

    def update_volume(
        self,
        db: Session,
        volume_id: UUID,
        volume_update: VolumeUpdate,
    ) -> VolumeResponse:
        """
        Atualiza um volume existente.

        Args:
            db: Sessão do banco de dados
            volume_id: UUID do volume
            volume_update: Dados para atualização

        Returns:
            VolumeResponse com dados atualizados

        Raises:
            NotFoundError: Se volume não existe
            ConflictError: Se nome ou path duplicado
            ValidationError: Se nenhum campo fornecido ou path inválido
        """
        volume = self.repository.get_by_id(db, volume_id)
        if not volume:
            raise NotFoundError("Volume", str(volume_id))

        update_data = volume_update.model_dump(exclude_unset=True)
        if not update_data:
            raise ValidationError("Nenhum campo fornecido para atualização")

        # Validar nome único se foi alterado
        if (
            volume_update.nome
            and volume_update.nome != volume.nome
            and self.repository.exists_by_nome(
                db, volume_update.nome, exclude_id=volume_id
            )
        ):
            raise ConflictError(
                f"Já existe um volume com o nome '{volume_update.nome}'"
            )

        # Validar path único e acesso se foi alterado
        if volume_update.path:
            normalized_path = os.path.normpath(volume_update.path)
            if normalized_path != volume.path:
                if self.repository.exists_by_path(
                    db, normalized_path, exclude_id=volume_id
                ):
                    raise ConflictError(
                        f"Já existe um volume com o path '{normalized_path}'"
                    )

                validation = self.validate_path_access(normalized_path)
                if not validation.valido:
                    raise ValidationError(
                        f"Path '{normalized_path}' não é acessível: {validation.erro}"
                    )

                update_data["path"] = normalized_path

        # Aplicar mudanças
        for field, value in update_data.items():
            setattr(volume, field, value)

        volume = self.repository.update(db, volume)
        return self._to_response(db, volume)

    def delete_volume(self, db: Session, volume_id: UUID) -> bool:
        """
        Remove um volume pelo ID.

        Args:
            db: Sessão do banco de dados
            volume_id: UUID do volume

        Returns:
            True se removido

        Raises:
            NotFoundError: Se volume não existe
            ConflictError: Se há configurações vinculadas
        """
        volume = self.repository.get_by_id(db, volume_id)
        if not volume:
            raise NotFoundError("Volume", str(volume_id))

        total_config = self.repository.count_configuracoes(db, volume_id)
        if total_config > 0:
            raise ConflictError(
                f"Não é possível deletar volume com {total_config} "
                "configuração(ões) vinculada(s)"
            )

        return self.repository.delete(db, volume_id)

    def test_volume(self, db: Session, volume_id: UUID) -> VolumeValidationResult:
        """
        Testa o acesso ao path de um volume existente.

        Args:
            db: Sessão do banco de dados
            volume_id: UUID do volume

        Returns:
            VolumeValidationResult com resultado do teste

        Raises:
            NotFoundError: Se volume não existe
        """
        volume = self.repository.get_by_id(db, volume_id)
        if not volume:
            raise NotFoundError("Volume", str(volume_id))

        return self.validate_path_access(volume.path)

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    def validate_path_access(self, path: str) -> VolumeValidationResult:
        """
        Valida se um path é acessível para leitura e escrita.

        Etapas:
        1. Verifica se o diretório existe
        2. Se não, tenta criar com mkdir -p
        3. Tenta escrever arquivo temporário
        4. Tenta ler o arquivo temporário
        5. Remove arquivo temporário

        Args:
            path: Caminho do diretório a ser validado

        Returns:
            VolumeValidationResult com flags detalhados
        """
        normalized = os.path.normpath(path)
        existe = os.path.isdir(normalized)
        criado = False
        pode_ler = False
        pode_escrever = False
        erro = None

        try:
            # 1/2. Verificar existência e tentar criar
            if not existe:
                try:
                    os.makedirs(normalized, exist_ok=True)
                    criado = True
                    existe = True
                except OSError as e:
                    erro = f"Não foi possível criar o diretório: {e}"
                    return VolumeValidationResult(
                        path=normalized,
                        valido=False,
                        pode_ler=False,
                        pode_escrever=False,
                        existe=False,
                        criado=False,
                        erro=erro,
                    )

            # 3. Tentar escrever arquivo temporário
            test_file = os.path.join(normalized, ".toninho_volume_test")
            test_content = "toninho_volume_validation_test"
            try:
                with open(test_file, "w") as f:
                    f.write(test_content)
                pode_escrever = True
            except OSError as e:
                erro = f"Sem permissão de escrita: {e}"
                pode_ler = os.access(normalized, os.R_OK)
                return VolumeValidationResult(
                    path=normalized,
                    valido=False,
                    pode_ler=pode_ler,
                    pode_escrever=False,
                    existe=existe,
                    criado=criado,
                    erro=erro,
                )

            # 4. Tentar ler arquivo temporário
            try:
                with open(test_file) as f:
                    content = f.read()
                pode_ler = content == test_content
                if not pode_ler:
                    erro = "Conteúdo lido não corresponde ao esperado"
            except OSError as e:
                erro = f"Sem permissão de leitura: {e}"

            # 5. Remover arquivo temporário
            import contextlib

            with contextlib.suppress(OSError):
                os.remove(test_file)

        except Exception as e:
            erro = f"Erro inesperado ao validar path: {e}"

        valido = pode_ler and pode_escrever

        return VolumeValidationResult(
            path=normalized,
            valido=valido,
            pode_ler=pode_ler,
            pode_escrever=pode_escrever,
            existe=existe,
            criado=criado,
            erro=erro,
        )

    def _to_response(self, db: Session, volume: Volume) -> VolumeResponse:
        """
        Converte um model Volume em VolumeResponse com total_processos calculado.

        Args:
            db: Sessão do banco de dados
            volume: Instância do modelo Volume

        Returns:
            VolumeResponse com total_processos computado
        """
        total = self.repository.count_configuracoes(db, volume.id)
        return VolumeResponse(
            id=volume.id,
            nome=volume.nome,
            path=volume.path,
            tipo=volume.tipo,
            status=volume.status,
            descricao=volume.descricao,
            total_processos=total,
            created_at=volume.created_at,
            updated_at=volume.updated_at,
        )
