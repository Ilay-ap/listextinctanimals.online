# Catálogo Digital de Mamíferos Extintos desde 1500

Status: Em Produção
Data: Junho de 2026
Repositório: https://github.com/Ilay-ap/listextinctanimals.online
Site em Produção: https://listextinctanimals-online-1.onrender.com

---

## Sobre o Projeto

Catálogo digital interativo compilando 114 mamíferos extintos desde o ano 1500, operando como uma Progressive Web Application (PWA) baseada em Django. A aplicação documenta dados geográficos, taxonômicos e causas de extinção, apoiada por registros validados.

### Destaques
- 114 espécies catalogadas com base na IUCN.
- Mapeamento geográfico de 80 localidades via Nominatim API e clusterização dinâmica.
- Banco de Dados PostgreSQL em arquitetura Cloud (Render).
- Integração assíncrona com a Google Translate API (PT-BR / EN).
- Autenticação de usuários para comentários e marcação de favoritos.
- Conformidade com acessibilidade WCAG 2.1 (AA).
- Cobertura de 81 testes automatizados (~1860 linhas de asserção em Pytest).

---

## Estrutura Técnica

- **Backend:** Python 3.11, Django 5.0, Gunicorn, PostgreSQL 15, WhiteNoise.
- **Frontend:** HTML5, CSS3, ES6+, Leaflet.js (Mapas).
- **Segurança:** Configurações HSTS, restrições CSRF rigorosas, hashing Argon2 e Rate Limiting ativo em endpoints sensíveis.

---

## Instalação Local (Desenvolvimento)

1. **Clonar e Acessar:**
```bash
git clone https://github.com/Ilay-ap/listextinctanimals.online.git
cd listextinctanimals.online
```

2. **Ambiente Virtual e Dependências:**
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

3. **Variáveis de Ambiente (.env na raiz):**
```env
SECRET_KEY=sua_chave_secreta
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

4. **Migrações e Execução:**
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Acesse em: http://localhost:8000

---

## Manutenção de Dados

A base estrutural de dados repousa sobre a versão atual do arquivo `mamiferos_extintos_v18.txt`. Adições e alterações de metadados devem seguir validações paleobiológicas oficiais antes de qualquer Pull Request.

Autor: Ilay-ap  
Contato: Ilay.pag@gmail.com
