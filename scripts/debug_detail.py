"""Debug script to check execution detail HTML."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile, os

db_fd, db_path = tempfile.mkstemp(suffix='.db')
engine = create_engine(f'sqlite:///{db_path}', connect_args={'check_same_thread': False})

from toninho.models import Base, Execucao, Processo
from toninho.models.enums import ExecucaoStatus
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

processo = Processo(nome='Test', descricao='Test')
db.add(processo)
db.commit()
db.refresh(processo)

execucao = Execucao(
    processo_id=processo.id,
    status=ExecucaoStatus.EM_EXECUCAO,
    paginas_processadas=5,
    bytes_extraidos=1024,
    taxa_erro=0.0,
    tentativa_atual=1
)
db.add(execucao)
db.commit()
db.refresh(execucao)
exec_id = execucao.id
db.close()

from fastapi.testclient import TestClient
from toninho.main import app
from toninho.core.database import get_db

def override_get_db():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app, raise_server_exceptions=True)

response = client.get(f'/execucoes/{exec_id}')
print('Status Code:', response.status_code)

html = response.text
for term in ['em_execucao', 'EM_EXECUCAO', 'Status', 'Páginas', 'Logs', 'bg-blue', 'Execução']:
    found = term in html
    print(f'  {term!r}: {found}')

# Print the relevant section around status
idx = html.find('Status')
if idx >= 0:
    print('\nContext around "Status":')
    print(html[idx:idx+500])

app.dependency_overrides.clear()
os.close(db_fd)
os.unlink(db_path)
