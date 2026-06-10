/**
 * Mapa Interativo de Distribuição de Mamíferos Extintos
 * Versão otimizada - SEM MARCADORES
 */

class MammalDistributionMap {
    constructor(containerId, mapData) {
        this.containerId = containerId;
        this.mapData = mapData;
        this.map = null;
        this.territories = [];
        this.overlapCount = {};
        this.geometryCache = {};
    }

    /**
     * Inicializa o mapa
     */
    init() {
        if (!this.mapData || !this.mapData.center) {
            console.error('Dados do mapa inválidos');
            return;
        }

        const mapContainer = document.getElementById(this.containerId);
        const getMinZoom = (w) => Math.max(2, Math.ceil(Math.log2(w / 256)));
        const initialWidth = mapContainer ? mapContainer.offsetWidth : 1024;
        const initialMinZoom = getMinZoom(initialWidth);

        // Criar mapa sem repetição e SEM marcador padrão
        this.map = L.map(this.containerId, {
            worldCopyJump: false,
            maxBounds: [[-90, -180], [90, 180]],
            maxBoundsViscosity: 1.0,
            minZoom: initialMinZoom,
            zoomControl: true,
            attributionControl: true,
            // Desabilitar marcadores padrão
            markerZoomAnimation: false
        }).setView(
            [this.mapData.center.lat, this.mapData.center.lon],
            Math.max(initialMinZoom, this.mapData.zoom)
        );

        window.addEventListener('resize', () => {
            const newWidth = mapContainer ? mapContainer.offsetWidth : 1024;
            const newMinZoom = getMinZoom(newWidth);
            this.map.setMinZoom(newMinZoom);
        });

        // Adicionar camada de tiles sem repetição
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            maxZoom: 18,
            minZoom: 2,
            noWrap: true
        }).addTo(this.map);

        // Filtrar coordenadas (remover continentes completamente)
        const filteredCoords = this.filterCoordinates(this.mapData.coordinates);

        // Adicionar legenda
        this.addLegend();

        // Carregar territórios
        if (filteredCoords.length > 0) {
            this.loadTerritories(filteredCoords);
        } else {
            console.warn('Nenhuma coordenada válida após filtragem');
        }
    }

    /**
     * Filtra coordenadas removendo COMPLETAMENTE continentes
     */
    filterCoordinates(coordinates) {
        if (!coordinates || coordinates.length === 0) {
            return [];
        }

        // Classificar por especificidade
        const classified = coordinates.map(coord => {
            const specificity = this.getSpecificity(coord.location, coord.display_name);
            return { ...coord, specificity };
        });

        // REMOVER COMPLETAMENTE CONTINENTES (especificidade 1)
        const withoutContinents = classified.filter(c => c.specificity >= 2);

        // Se não sobrou nada, retornar vazio
        if (withoutContinents.length === 0) {
            console.warn('Apenas continentes encontrados - não será exibido mapa');
            return [];
        }

        // Ordenar por especificidade
        withoutContinents.sort((a, b) => b.specificity - a.specificity);

        return withoutContinents;
    }

    /**
     * Determina especificidade (1=continente, 2=país, 3=estado, 4=cidade, 5=local)
     */
    getSpecificity(location, displayName) {
        const locationLower = location.toLowerCase().trim();
        const displayLower = displayName.toLowerCase().trim();

        // CONTINENTES - SEMPRE NÍVEL 1 (serão removidos)
        const continents = [
            'oceania', 'africa', 'áfrica', 'américa', 'america', 
            'asia', 'europe', 'europa', 'antartica', 'antártica',
            'south america', 'north america', 'américa do sul', 'américa do norte'
        ];
        
        if (continents.includes(locationLower)) {
            return 1;
        }

        // Verificar se contém palavra de continente
        if (continents.some(cont => locationLower.includes(cont))) {
            return 1;
        }

        // Local muito específico (cavernas, formações, sítios)
        if (displayLower.match(/\b(cave|caverna|site|sítio|locality|localidade|point|formation|formação|fossil)\b/)) {
            return 5;
        }

        // Cidade ou ilha
        if (displayLower.match(/\b(city|cidade|town|village|vila|municipality|município)\b/) ||
            locationLower.match(/\bisland\b|\bilha\b|\bisle\b/i)) {
            return 4;
        }

        // Estado, província, região
        if (displayLower.match(/\b(state|province|província|estado|region|região|territory|território|peninsula|península|plain|planície|plains|desert|deserto|mainland)\b/)) {
            return 3;
        }

        // País (padrão)
        return 2;
    }

    /**
     * Carrega territórios com otimização
     */
    async loadTerritories(coordinates) {
        if (!coordinates || coordinates.length === 0) {
            return;
        }

        // Carregar em paralelo com limite de requisições simultâneas
        const batchSize = 3;
        for (let i = 0; i < coordinates.length; i += batchSize) {
            const batch = coordinates.slice(i, i + batchSize);
            await Promise.all(batch.map(coord => this.fetchAndDrawTerritory(coord)));
            
            if (i + batchSize < coordinates.length) {
                await this.delay(500);
            }
        }

        // Ajustar visualização
        setTimeout(() => {
            this.fitBounds();
        }, 500);
    }

    /**
     * Delay helper
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Calcula opacidade baseada em sobreposições
     */
    getOpacityForOverlap(locationKey) {
        const count = this.overlapCount[locationKey] || 1;
        const baseFillOpacity = 0.25;
        const baseStrokeOpacity = 0.7;
        
        return {
            fillOpacity: Math.min(baseFillOpacity * count, 0.65),
            strokeOpacity: Math.min(baseStrokeOpacity + (count - 1) * 0.15, 1.0)
        };
    }

    /**
     * Registra sobreposição
     */
    registerOverlap(locationKey) {
        if (!this.overlapCount[locationKey]) {
            this.overlapCount[locationKey] = 0;
        }
        this.overlapCount[locationKey]++;
    }

    /**
     * Busca e desenha território com cache - SEM MARCADORES
     */
    async fetchAndDrawTerritory(coord) {
        try {
            const locationKey = coord.location.toLowerCase();

            // Verificar cache
            let geojson = this.geometryCache[locationKey];

            if (!geojson) {
                // Buscar geometria via Nominatim
                const query = encodeURIComponent(coord.location);
                const url = `https://nominatim.openstreetmap.org/search?q=${query}&format=json&polygon_geojson=1&limit=1`;

                const response = await fetch(url);
                const data = await response.json();

                if (data && data.length > 0 && data[0].geojson) {
                    geojson = data[0].geojson;
                    this.geometryCache[locationKey] = geojson;
                }
            }

            if (geojson) {
                // Registrar sobreposição
                this.registerOverlap(locationKey);

                // Obter opacidades
                const opacities = this.getOpacityForOverlap(locationKey);

                // Desenhar APENAS polígono - SEM MARCADOR
                const layer = L.geoJSON(geojson, {
                    style: {
                        color: '#d32f2f',
                        fillColor: '#f44336',
                        fillOpacity: opacities.fillOpacity,
                        weight: 2,
                        opacity: opacities.strokeOpacity
                    }
                }).addTo(this.map);

                // Popup
                const popupContent = `
                    <div class="map-popup">
                        <h4>Território Histórico</h4>
                        <p class="popup-detail"><strong>${coord.location}</strong></p>
                        <p class="popup-detail">${coord.display_name}</p>
                    </div>
                `;
                layer.bindPopup(popupContent);

                // Tooltip
                layer.bindTooltip(coord.location, {
                    permanent: false,
                    direction: 'top'
                });

                this.territories.push(layer);
            } else {
                // Fallback para círculo pequeno - SEM MARCADOR
                console.warn(`Geometria não encontrada para: ${coord.location}`);
                this.addFallbackCircle(coord);
            }
        } catch (error) {
            console.error(`Erro ao buscar geometria para ${coord.location}:`, error);
            this.addFallbackCircle(coord);
        }
    }

    /**
     * Adiciona círculo pequeno como fallback - SEM MARCADOR
     */
    addFallbackCircle(coord) {
        const radius = this.getFallbackRadius(coord);
        const locationKey = coord.location.toLowerCase();

        // Registrar sobreposição
        this.registerOverlap(locationKey);

        // Obter opacidades
        const opacities = this.getOpacityForOverlap(locationKey);

        // Desenhar APENAS círculo - SEM MARCADOR
        const circle = L.circle([coord.lat, coord.lon], {
            color: '#d32f2f',
            fillColor: '#f44336',
            fillOpacity: opacities.fillOpacity,
            weight: 2,
            opacity: opacities.strokeOpacity,
            radius: radius
        }).addTo(this.map);

        const popupContent = `
            <div class="map-popup">
                <h4>Território Histórico</h4>
                <p class="popup-detail"><strong>${coord.location}</strong></p>
                <p class="popup-detail">${coord.display_name}</p>
            </div>
        `;
        circle.bindPopup(popupContent);
        circle.bindTooltip(coord.location);

        this.territories.push(circle);
    }

    /**
     * Calcula raio fallback
     */
    getFallbackRadius(coord) {
        const specificity = this.getSpecificity(coord.location, coord.display_name);

        if (specificity === 5) return 5000;    // 5 km
        if (specificity === 4) return 15000;   // 15 km
        if (specificity === 3) return 50000;   // 50 km
        if (specificity === 2) return 100000;  // 100 km
        return 50000;
    }

    /**
     * Ajusta zoom
     */
    fitBounds() {
        if (this.territories.length === 0) {
            return;
        }

        const group = L.featureGroup(this.territories);
        const bounds = group.getBounds();
        
        if (bounds.isValid()) {
            this.map.fitBounds(bounds.pad(0.2));
        }
    }

    /**
     * Adiciona legenda
     */
    addLegend() {
        const legend = L.control({ position: 'bottomright' });

        legend.onAdd = function (map) {
            const div = L.DomUtil.create('div', 'map-legend');
            div.innerHTML = `
                <h4>Distribuição Histórica</h4>
                <p>
                    <span style="display: inline-block; width: 20px; height: 12px; background-color: rgba(244, 67, 54, 0.25); border: 2px solid rgba(211, 47, 47, 0.7); border-radius: 3px; vertical-align: middle;"></span>
                    Área onde a espécie vivia
                </p>
                <p style="margin-top: 8px; font-size: 11px; color: #666;">
                    <em>Áreas mais escuras indicam sobreposição de regiões</em>
                </p>
            `;
            return div;
        };

        legend.addTo(this.map);
    }

    /**
     * Destrói o mapa
     */
    destroy() {
        if (this.map) {
            this.map.remove();
            this.map = null;
            this.territories = [];
            this.overlapCount = {};
            this.geometryCache = {};
        }
    }
}

/**
 * Inicializa o mapa - SEM MARCADORES
 */
function initMammalMap(mapDataJson) {
    if (!mapDataJson) {

        return;
    }

    try {
        const mapData = typeof mapDataJson === 'string' ? JSON.parse(mapDataJson) : mapDataJson;

        if (!mapData || !mapData.coordinates || mapData.coordinates.length === 0) {

            const container = document.getElementById('distribution-map-container');
            if (container) {
                container.style.display = 'none';
            }
            return;
        }

        const mapInstance = new MammalDistributionMap('distribution-map', mapData);
        mapInstance.init();

    } catch (error) {
        console.error('Erro ao inicializar mapa:', error);
        const container = document.getElementById('distribution-map-container');
        if (container) {
            container.style.display = 'none';
        }
    }
}

