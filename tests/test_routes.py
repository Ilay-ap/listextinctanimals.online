"""
Testes de Rotas - test_routes.py

Testa todas as rotas principais do site:
- Página inicial (/)
- Página de detalhes de mamífero (/mammal/<id>)
- Endpoint de busca (/search)
- Página sobre (/about)
- Página inexistente (404)
"""

import pytest
from django.test import Client
from django.urls import reverse
from mammals.models import Mammal
from django.contrib.auth.models import User
import json


@pytest.mark.django_db
class TestRoutes:
    """Classe de testes para rotas do site"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup executado antes de cada teste"""
        self.client = Client()
        
        # Criar mamífero de teste
        self.mammal = Mammal.objects.create(
            common_name="Tigre-da-Tasmânia",
            binomial_name="Thylacinus cynocephalus",
            description="Um carnívoro marsupial extinto nativo da Tasmânia, Austrália e Nova Guiné.",
            habitat="Florestas temperadas e pastagens",
            distribution="Tasmânia, Austrália",
            extinction_causes="Caça excessiva, perda de habitat, doenças",
            continent="Oceania",
            taxonomy_order="DASYUROMORPHIA"
        )
    
    def test_homepage_returns_200(self):
        """
        Teste 1: GET / retorna 200
        Verifica se a página inicial carrega corretamente
        """
        response = self.client.get(reverse('mammals:index'))
        
        assert response.status_code == 200
        assert 'mammals' in response.context
        assert len(response.context['mammals']) > 0
        
        # Verificar se o template correto foi usado
        assert 'mammals/index.html' in [t.name for t in response.templates]
    
    def test_mammal_detail_returns_200(self):
        """
        Teste 2: GET /mammal/1 retorna 200
        Verifica se a página de detalhes de um mamífero carrega
        """
        response = self.client.get(
            reverse('mammals:detail', kwargs={'pk': self.mammal.pk})
        )
        
        assert response.status_code == 200
        assert response.context['mammal'] == self.mammal
        assert 'mammals/detail.html' in [t.name for t in response.templates]
        
        # Verificar se os dados do mamífero estão no conteúdo
        content = response.content.decode('utf-8')
        assert "Tigre-da-Tasmânia" in content
        assert "Thylacinus cynocephalus" in content
    
    def test_search_returns_valid_json(self):
        """
        Teste 3: GET /search?q=tiger retorna JSON válido
        Verifica se o endpoint de busca retorna JSON correto
        """
        response = self.client.get(
            reverse('mammals:search'),
            {'q': 'Tigre'}
        )
        
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'
        
        # Parsear JSON
        data = json.loads(response.content)
        assert isinstance(data, list)
        
        # Verificar se encontrou o mamífero
        assert len(data) > 0
        assert data[0]['common_name'] == "Tigre-da-Tasmânia"
        assert 'id' in data[0]
        assert 'binomial_name' in data[0]
        assert 'description' in data[0]
    
    def test_nonexistent_page_returns_404(self):
        """
        Teste 4: GET /pagina-inexistente retorna 404
        Verifica se páginas inexistentes retornam erro 404
        """
        response = self.client.get('/pagina-que-nao-existe/')
        
        assert response.status_code == 404
    
    def test_about_page_returns_200(self):
        """
        Teste 5: GET /about retorna 200
        Verifica se a página "Sobre" carrega corretamente
        """
        response = self.client.get(reverse('mammals:about'))
        
        assert response.status_code == 200
        assert 'mammals/about.html' in [t.name for t in response.templates]
        
        # Verificar se há conteúdo sobre o projeto
        content = response.content.decode('utf-8')
        assert len(content) > 0


@pytest.mark.django_db
class TestSearchFilters:
    """Testes adicionais para filtros de busca"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup com múltiplos mamíferos"""
        self.client = Client()
        
        # Criar mamíferos de diferentes continentes
        Mammal.objects.create(
            common_name="Leão-do-Atlas",
            binomial_name="Panthera leo leo",
            description="Subespécie de leão extinta do Norte da África",
            continent="Africa",
            taxonomy_order="CARNIVORA"
        )
        
        Mammal.objects.create(
            common_name="Auroch",
            binomial_name="Bos primigenius",
            description="Ancestral selvagem do gado doméstico",
            continent="Europe",
            taxonomy_order="ARTIODACTYLA"
        )
    
    def test_search_by_continent(self):
        """Testa filtro por continente"""
        response = self.client.get(
            reverse('mammals:search'),
            {'region': 'Africa'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.content)
        
        # Deve retornar apenas mamíferos da África
        assert len(data) == 1
        assert data[0]['common_name'] == "Leão-do-Atlas"
    
    def test_search_by_taxonomy(self):
        """Testa filtro por taxonomia"""
        response = self.client.get(
            reverse('mammals:search'),
            {'taxonomy': 'CARNIVORA'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.content)
        
        # Deve retornar apenas carnívoros
        assert len(data) == 1
        assert data[0]['common_name'] == "Leão-do-Atlas"
    
    def test_search_combined_filters(self):
        """Testa combinação de filtros"""
        response = self.client.get(
            reverse('mammals:search'),
            {'q': 'leão', 'continent': 'Africa'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.content)
        
        assert len(data) == 1
        assert data[0]['common_name'] == "Leão-do-Atlas"

