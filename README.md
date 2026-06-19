# 🦴 Catálogo Digital de Mamíferos Extintos desde 1500

[![Deploy Status](https://img.shields.io/badge/deploy-active-success)](https://extinct-mammals.onrender.com)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.0-green)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**🌐 Site em Produção**: https://extinct-mammals.onrender.com  
**📦 Repositório**: https://github.com/Ilay-ap/Cat-logo-Digital-de-Mam-feros-Extintos-desde-1500  
**📄 Versão**: 56  
**📅 Data**: Novembro 2025  
**✅ Status**: Em Produção

---

## 📖 Sobre o Projeto

Catálogo digital interativo de **85 mamíferos extintos desde 1500**, desenvolvido como Progressive Web Application (PWA) utilizando Django. O projeto visa preservar a memória biológica de espécies extintas e promover conscientização sobre conservação da biodiversidade através de tecnologias modernas de informação e comunicação.

### 🎯 Principais Características

- ✅ **85 espécies catalogadas** com informações científicas completas
- ✅ **Site em produção** na nuvem (Render + PostgreSQL)
- ✅ **Mapas interativos** com geocodificação via Nominatim API
- ✅ **Tradução automática** PT-BR ↔ EN via Google Translate API
- ✅ **Progressive Web App** (instalável, funciona offline)
- ✅ **Sistema de busca e filtros** por região e taxonomia
- ✅ **Comentários e favoritos** para usuários autenticados
- ✅ **Acessibilidade** WCAG 2.1 Nível AA
- ✅ **1860 linhas de testes** automatizados (Pytest)
- ✅ **Documentação SCRUM** completa

---

## 📸 Screenshots

### Homepage - Catálogo de Espécies
![Homepage](https://raw.githubusercontent.com/Ilay-ap/Cat-logo-Digital-de-Mam-feros-Extintos-desde-1500/main/Site_v55/static/images/screenshots/homepage.webp )
*Catálogo completo com 85 espécies, busca e filtros por região e taxonomia*

### Mapa Global Interativo
![Mapa Global](https://raw.githubusercontent.com/Ilay-ap/Cat-logo-Digital-de-Mam-feros-Extintos-desde-1500/main/Site_v55/static/images/screenshots/global_map.webp )
*Visualização de 77 localizações únicas com clustering inteligente e heatmap*

### Página de Detalhes com Mapa Individual

![Detalhes](https://raw.githubusercontent.com/Ilay-ap/Cat-logo-Digital-de-Mam-feros-Extintos-desde-1500/main/Site_v55/static/images/screenshots/detail_map.webp )
*Informações completas da espécie com mapa de distribuição histórica via Nominatim API*
---

## 🚀 Acesso Rápido

### 🌐 Site em Produção

**URL**: https://extinct-mammals.onrender.com

- **Hospedagem**: Render (https://render.com)
- **Banco de Dados**: PostgreSQL 15 na nuvem
- **HTTPS**: Certificado SSL automático
- **Deploy**: Contínuo via GitHub

### 📱 Instalar como App

O site é uma PWA e pode ser instalado:

1. Acesse https://extinct-mammals.onrender.com
2. Clique no botão "📱 Instalar App" ou
3. No navegador: Menu → "Instalar aplicativo"
4. Use offline após instalação!

---

## ✨ Funcionalidades Principais

### 1. 🗺️ Mapa Global Interativo

**URL**: https://extinct-mammals.onrender.com/pt-br/global-map/

- **77 localizações únicas** mapeadas
- **Clustering inteligente** com Leaflet.markercluster
- **Heatmap de concentração**: Verde → Amarelo → Laranja → Vermelho
- **Popups informativos** com lista de espécies
- **Estatísticas em tempo real**:
  - 📍 77 localizações
  - 🦴 85 espécies
  - 🔥 Concentração máxima: 4 espécies/local

### 2. 📋 Catálogo Completo de Espécies

**URL**: https://extinct-mammals.onrender.com/pt-br/

- **85 mamíferos extintos** catalogados
- **Busca por texto** (nome comum, científico, descrição)
- **Filtros por região**: África, América, Ásia, Europa, Oceania
- **Filtros por taxonomia**: Roedores, Carnívoros, Artiodáctilos, etc.
- **Paginação**: 10, 20, 30 ou todos
- **Cards com imagens** de alta qualidade

### 3. 📄 Páginas de Detalhes

**Exemplo**: https://extinct-mammals.onrender.com/pt-br/mammal/1/

Cada espécie possui:

- **Informações completas**: Nome comum/científico, taxonomia, habitat, distribuição, causas de extinção
- **Mapa interativo individual** com geocodificação via **Nominatim API**
- **Polígonos geográficos** mostrando territórios históricos
- **Sistema de comentários** (usuários autenticados)
- **Botão de favoritar** (usuários autenticados)
- **Tradução automática** PT-BR ↔ EN

### 4. 🌍 Integração com APIs Externas

#### Nominatim API (OpenStreetMap)

- **Função**: Geocodificação e obtenção de geometrias geográficas
- **Uso**: Mapear territórios históricos de distribuição das espécies
- **Implementação**: `static/js/map.js`
- **Endpoint**: https://nominatim.openstreetmap.org/search
- **Gratuita**: Sim, sem necessidade de chave de API

#### Google Translate API (via deep-translator)

- **Função**: Tradução automática de conteúdo
- **Uso**: Suporte multilíngue PT-BR ↔ EN
- **Implementação**: `mammals/translation_service.py`
- **Cache**: 30 dias para otimizar performance
- **Biblioteca**: deep-translator 1.11.4

### 5. 👤 Sistema de Usuários

- **Registro e login** com validação
- **Perfil editável** com biografia
- **Comentários** em espécies
- **Favoritos pessoais** com página dedicada
- **Painel administrativo** (apenas admins)

### 6. 🎨 Temas e Acessibilidade

- **Modo claro/escuro** com persistência
- **Acessibilidade WCAG 2.1 AA**:
  - Navegação por teclado
  - ARIA labels e roles
  - Contraste adequado (4.5:1)
  - Suporte a leitores de tela
- **Responsivo**: Mobile, tablet, desktop

### 7. 📱 Progressive Web App (PWA)

- **Instalável** em qualquer dispositivo
- **Funciona offline** via Service Worker
- **Cache inteligente** de recursos
- **Manifest completo** com 8 ícones
- **Splash screens** customizadas

---

## 🛠️ Tecnologias Utilizadas

### Backend

- **Python 3.11**
- **Django 5.0** (framework web)
- **PostgreSQL 15** (produção)
- **SQLite** (desenvolvimento)
- **Gunicorn** (servidor WSGI)
- **WhiteNoise** (arquivos estáticos)

### Frontend

- **HTML5** semântico
- **CSS3** com variáveis e temas
- **JavaScript ES6+**
- **Leaflet.js** (mapas interativos)
- **Leaflet.markercluster** (clustering)

### APIs Externas

- **Nominatim API** (geocodificação)
- **Google Translate API** (tradução)

### PWA

- **Service Worker** (cache e offline)
- **Web App Manifest** (instalação)
- **Cache API** (armazenamento)

### DevOps

- **Git/GitHub** (controle de versão)
- **Render** (hospedagem)
- **PostgreSQL Cloud** (banco de dados)
- **HTTPS** via Let's Encrypt

### Testes

- **Pytest** (framework de testes)
- **pytest-django** (integração Django)
- **1860 linhas** de testes automatizados

---

## 📦 Instalação Local

### Pré-requisitos

- Python 3.11+
- pip
- Git


### Usando Docker (Recomendado para Produção)

`ash
# 1. Construir e iniciar os contêineres
docker-compose up -d --build

# 2. Executar as migrações (se necessário, o script de inicialização já cuida disso)
docker-compose exec web python manage.py migrate

# 3. Criar superusuário
docker-compose exec web python manage.py createsuperuser
`

**Acesse**: http://localhost:8000
**Healthcheck**: http://localhost:8000/health/

### Passo a Passo (Manual)


```bash
# 1. Clonar repositório
git clone https://github.com/Ilay-ap/Cat-logo-Digital-de-Mam-feros-Extintos-desde-1500.git
cd Site_v55

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
# Criar arquivo .env na raiz:
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1

# 5. Aplicar migrations
python manage.py migrate

# 6. Criar superusuário
python manage.py createsuperuser

# 7. Coletar arquivos estáticos
python manage.py collectstatic --noinput

# 8. Executar servidor
python manage.py runserver
```

**Acesse**: http://localhost:8000

---

## 🧪 Testes

### Executar todos os testes

```bash
pytest tests/ -v
```

### Executar testes específicos

```bash
# Testes de autenticação
pytest tests/test_auth.py -v

# Testes de CRUD
pytest tests/test_crud.py -v

# Testes de rotas
pytest tests/test_routes.py -v
```

### Cobertura de Testes

- **Total de testes**: 81
- **Arquivos de teste**: 7
- **Linhas de código de teste**: ~1860
- **Cobertura**: Autenticação, CRUD, banco de dados, formulários, modelos, rotas, views

---

## 🗂️ Estrutura do Projeto

```
Site_v55/
├── extinct_mammals_django/     # Configurações Django
│   ├── settings.py            # Configurações principais
│   ├── urls.py                # URLs principais
│   └── wsgi.py                # WSGI para produção
├── mammals/                    # App principal
│   ├── models.py              # Modelos (Mammal, Comment, Favorite)
│   ├── views.py               # Views e lógica
│   ├── translation_service.py # Integração Google Translate
│   └── admin.py               # Painel administrativo
├── accounts/                   # App de autenticação
│   ├── models.py              # UserProfile
│   ├── views.py               # Login, registro, perfil
│   └── forms.py               # Formulários
├── templates/                  # Templates HTML
│   ├── mammals/               # Templates de mamíferos
│   ├── accounts/              # Templates de usuários
│   └── base.html              # Template base
├── static/                     # Arquivos estáticos
│   ├── css/                   # Estilos
│   ├── js/
│   │   ├── map.js            # Integração Nominatim API
│   │   ├── global_map.js     # Mapa global
│   │   └── pwa.js            # PWA
│   ├── images/                # Imagens das espécies
│   └── icons/                 # Ícones PWA
├── tests/                      # Testes automatizados
│   ├── test_auth.py
│   ├── test_crud.py
│   ├── test_database.py
│   ├── test_forms.py
│   ├── test_models.py
│   ├── test_routes.py
│   └── test_views.py
├── locale/                     # Arquivos de tradução
│   ├── pt_BR/
│   └── en/
├── manage.py                   # CLI Django
├── requirements.txt            # Dependências Python
├── render.yaml                 # Configuração Render
├── sw.js                       # Service Worker
├── manifest.json               # PWA Manifest
├── README.md                   # Este arquivo
├── ARTIGO_COMPLETO.md         # Artigo TCC
└── DOCUMENTACAO_SCRUM.md      # Documentação SCRUM
```

---

## 📊 Estatísticas do Projeto

### Dados

- **Espécies catalogadas**: 85
- **Localizações únicas**: 77
- **Imagens**: 85 (alta qualidade)
- **Idiomas**: 2 (PT-BR, EN)
- **Concentração máxima**: 4 espécies/local

### Código

- **Linhas de Python**: ~3500
- **Linhas de JavaScript**: ~1200
- **Linhas de CSS**: ~800
- **Linhas de HTML**: ~2000
- **Linhas de testes**: ~1860
- **Total**: ~9360 linhas

### Banco de Dados

- **Entidades**: 5 (Mammal, User, UserProfile, Comment, Favorite)
- **Migrations**: 21
- **Relacionamentos**: ForeignKey, OneToOne, unique_together

### Desenvolvimento

- **Duração**: 8 semanas
- **Sprints**: 4 (2 semanas cada)
- **Commits**: 150+
- **Horas estimadas**: 200+

---

## 🐛 Troubleshooting

### Site não carrega

- Verifique se está acessando https://extinct-mammals.onrender.com
- Primeiro acesso pode demorar 30-60s (cold start do plano gratuito)

### Erro "You have unapplied migration(s)"

```bash
python manage.py migrate
```

### Erro "No module named 'django'"

```bash
pip install -r requirements.txt
```

### Mapas não carregam

- Verifique conexão com internet (Nominatim API requer conexão)
- Aguarde alguns segundos para carregar geometrias

### Tradução não funciona

- Verifique conexão com internet (Google Translate API requer conexão)
- Cache de traduções dura 30 dias

---

## 📚 Documentação Adicional

- **Artigo Completo**: [ARTIGO_COMPLETO.md](ARTIGO_COMPLETO.md)
- **Documentação SCRUM**: [DOCUMENTACAO_SCRUM.md](DOCUMENTACAO_SCRUM.md)
- **Changelogs**: Ver DOCUMENTACAO_SCRUM.md

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 👤 Autor

**[Seu Nome]**

- GitHub: [@Ilay-ap](https://github.com/Ilay-ap)
- Email: [Ilay.pag@gmail.com]

---

## 🙏 Agradecimentos

- **IUCN Red List** - Dados sobre espécies extintas
- **OpenStreetMap/Nominatim** - API de geocodificação
- **Google Translate** - API de tradução
- **Leaflet.js** - Biblioteca de mapas
- **Django Community** - Framework robusto
- **Render** - Hospedagem gratuita

---

## 🔗 Links Úteis

- **Site em Produção**: https://extinct-mammals.onrender.com
- **Repositório GitHub**: https://github.com/Ilay-ap/Cat-logo-Digital-de-Mam-feros-Extintos-desde-1500
- **Django Documentation**: https://docs.djangoproject.com/
- **Leaflet Documentation**: https://leafletjs.com/reference.html
- **Nominatim API**: https://nominatim.org/release-docs/latest/api/Overview/
- **WCAG 2.1**: https://www.w3.org/WAI/WCAG21/quickref/

---

## 🎯 Roadmap Futuro

- [ ] Adicionar mais espécies (pré-1500, outras classes)
- [ ] Implementar API pública REST
- [ ] Adicionar quizzes educativos
- [ ] Timeline interativa de extinções
- [ ] Integração com GBIF API
- [ ] Realidade aumentada (3D)
- [ ] Compartilhamento em redes sociais
- [ ] Modo offline completo
- [ ] Mais idiomas (ES, FR, DE)

---

## 📈 Status do Projeto

**✅ PRONTO PARA PRODUÇÃO**

O projeto está **100% funcional** e **em produção** em:

🌐 **https://extinct-mammals.onrender.com**

---

**Desenvolvido com ❤️ para preservar a memória biológica dos mamíferos extintos**

*"Conhecer o passado para proteger o futuro"*

---

**Última atualização**: Novembro 2025  
**Versão**: 56
