# Catálogo Digital de Mamíferos Extintos desde 1500

Status: Em Produção
Data: Junho de 2026
Repositório: https://github.com/Ilay-ap/Cat-logo-Digital-de-Mam-feros-Extintos-desde-1500
Site em Produção: https://extinct-mammals.onrender.com

---

## Sobre o Projeto

Catálogo digital interativo focado na compilação de 114 mamíferos extintos desde o ano 1500. A aplicação foi desenvolvida no formato Progressive Web Application (PWA) utilizando o framework Django e documenta dados taxonômicos, geográficos e causais sobre a extinção destas espécies, servindo como ferramenta de pesquisa e conscientização.

### Características Principais

- 114 espécies catalogadas com verificação baseada em registros de distribuição geográfica oficial.
- Mapeamento geoespacial rigoroso englobando 80 localidades globais exclusivas via Nominatim API.
- Hospedagem em arquitetura na nuvem (Render + PostgreSQL).
- Tradução automática assíncrona (PT-BR / EN) através da Google Translate API.
- Sistema de busca indexada e filtros múltiplos (região, taxonomia e época de extinção).
- Painel para usuários autenticados gerenciarem comentários e lista de favoritos.
- Nível de Acessibilidade aderente à especificação WCAG 2.1 Nível AA.
- Conjunto de testes automatizados estruturado em Pytest.

---

## Acesso em Produção

URL: https://extinct-mammals.onrender.com

A infraestrutura atual está configurada sob os seguintes parâmetros:
- Hospedagem: Render
- Banco de Dados: PostgreSQL 15 (Instância na Nuvem)
- Protocolo: HTTPS obrigatório (com configurações de HSTS habilitadas)
- Pipeline de Deploy: CI/CD integrado ao GitHub

Para utilização do PWA offline, acesse a URL via navegador e utilize a função nativa de "Instalar aplicativo".

---

## Módulos do Sistema

### 1. Mapa Global Georreferenciado
Interface que renderiza 80 localizações distintas utilizando clusterização dinâmica (Leaflet.markercluster). O sistema processa um mapa de calor que reflete com precisão as áreas de concentração dos habitats extintos, sem sobreposição artificial.

### 2. Catálogo e Pesquisa
Módulo responsável por indexar os 114 registros da tabela. Permite pesquisa por nome comum, nome científico e aplicação de filtros combinados baseados em regiões e classes taxonômicas.

### 3. Fichas de Detalhamento Individual
Cada mamífero possui uma visualização dedicada contendo seus metadados completos, incluindo causa principal do desaparecimento, continente e a delimitação de sua ocorrência histórica via mapa individual (Leaflet).

### 4. Segurança e Auditoria
As rotas de requisição e autenticação do sistema possuem camadas de segurança configuradas com proteção contra CSRF, controle de tráfego por IP (Rate Limiting de 10 requisições por minuto em endpoints sensíveis), rotação restrita de logs contra exaustão de disco e hashing moderno de senhas com Argon2.

---

## Tecnologias Utilizadas

### Backend
- Python 3.11
- Django 5.0
- PostgreSQL 15
- Gunicorn (Servidor WSGI)
- WhiteNoise (Compressão e fornecimento de arquivos estáticos)

### Frontend
- HTML5 Semântico
- CSS3
- JavaScript (ES6+)
- Leaflet.js

### APIs e Integrações Externas
- Nominatim API (OpenStreetMap)
- Google Translate API
- Service Workers e Manifest (PWA)

### Testes
- Pytest / pytest-django

---

## Instalação Local (Ambiente de Desenvolvimento)

### Pré-requisitos
- Python 3.11 ou superior
- Git

### Procedimento

1. Clone o repositório em sua máquina:
```bash
git clone https://github.com/Ilay-ap/Cat-logo-Digital-de-Mam-feros-Extintos-desde-1500.git
cd Cat-logo-Digital-de-Mam-feros-Extintos-desde-1500
```

2. Crie e ative o ambiente virtual:
```bash
python -m venv venv
# Linux ou macOS
source venv/bin/activate
# Windows
venv\Scripts\activate
```

3. Instale as dependências listadas:
```bash
pip install -r requirements.txt
```

4. Configure o arquivo de variáveis de ambiente (`.env`) na raiz do diretório com os seguintes dados básicos:
```env
SECRET_KEY=chave-secreta-de-desenvolvimento
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

5. Aplique as migrações no banco de dados local:
```bash
python manage.py migrate
```

6. Crie o superusuário para acesso ao painel de administração:
```bash
python manage.py createsuperuser
```

7. Inicie o servidor local:
```bash
python manage.py runserver
```

A aplicação estará disponível no endereço http://localhost:8000.

---

## Testes

O ambiente conta com testes de software automatizados via Pytest para validar as rotinas de banco, views e formulários.

Para executar todos os testes da aplicação:
```bash
pytest tests/ -v
```

---

## Arquitetura de Diretórios

- `/extinct_mammals_django`: Configurações globais e de segurança da aplicação.
- `/mammals`: Lógica de negócios central, modelos do banco de dados de mamíferos, endpoints da API e integrações de mapas e tradução.
- `/accounts`: Funcionalidades de autenticação de usuários, perfil, e registro.
- `/templates`: Arquivos HTML do projeto integrados com tags nativas do Django.
- `/static`: Scripts customizados (JS), folha de estilos padronizada (CSS) e imagens das espécies.
- `/tests`: Suíte de arquivos de validação e garantia de qualidade (QA).
- `/scratch`: Scripts de migração e auditoria de base de dados para ambiente de desenvolvimento.

---

## Gestão de Dados e Contribuições

Os dados de produção baseiam-se estritamente na versão auditada `mamiferos_extintos_v18.txt`. Alterações diretas em metadados de espécies ou coordenadas devem ser comprovadas por dados paleontológicos ou referências da IUCN. Mudanças na estrutura de software podem ser submetidas via sistema de Pull Requests do repositório no GitHub.

Autor: Ilay-ap  
Contato: Ilay.pag@gmail.com
