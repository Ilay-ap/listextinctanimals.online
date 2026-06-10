// ============================================================================
// SISTEMA DE TRADUÇÃO DINÂMICA
// ============================================================================

// Objeto global de traduções (será preenchido pelo template)
window.translations = window.translations || {};

function getTranslation(key) {
    return window.translations[key] || key;
}

// ============================================================================
// BUSCA E FILTROS DE MAMÍFEROS
// ============================================================================

document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("search-input");
    const searchBtn = document.getElementById("search-btn");
    const clearBtn = document.getElementById("clear-btn");
    const mammalsList = document.getElementById("mammals-list");
    const filterButtons = document.querySelectorAll(".filter-btn");

    let activeFilters = {
        region: [],
        taxonomy: [],
    };

    let allMammals = []; // Armazenar todos os mamíferos
    let filteredMammals = []; // Mamíferos após filtros
    let currentPage = 1;
    let itemsPerPage = 20; // Padrão: 20 por página

    // Carregar todos os mamíferos ao iniciar
    function loadAllMammals() {
        const searchUrl = (window.URLS && window.URLS.search) ? window.URLS.search : '/search/';
        fetch(searchUrl)
            .then(response => response.json())
            .then(data => {
                allMammals = data;
                filteredMammals = data;
                
                // Hide empty filters
                const normalizeStr = (str) => str ? str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase() : '';
                const availableRegions = new Set(data.map(m => normalizeStr(m.continent)));
                const availableTaxonomies = new Set(data.map(m => m.taxonomy_order ? String(m.taxonomy_order).toUpperCase().trim() : ''));
                
                filterButtons.forEach(btn => {
                    const type = btn.dataset.filterType;
                    const val = btn.dataset.filterValue;
                    if (type === 'region') {
                        const nVal = normalizeStr(val);
                        // Check if any region string includes the normalized value
                        const hasRegion = Array.from(availableRegions).some(r => r.includes(nVal));
                        if (!hasRegion) btn.style.display = 'none';
                    } else if (type === 'taxonomy') {
                        if (!availableTaxonomies.has(String(val).toUpperCase().trim())) {
                            btn.style.display = 'none';
                        }
                    }
                });

                displayMammalsWithPagination();
            })
            .catch(error => console.error('Erro ao carregar mamíferos:', error));
    }

    function performSearch() {
        const query = searchInput ? searchInput.value.trim().toLowerCase() : "";

        let filtered = allMammals;

        // Filtrar por continente
        if (activeFilters.region && activeFilters.region.length > 0) {
            filtered = filtered.filter(m => {
                if (!m.continent) return false;
                const continent = m.continent.toLowerCase();
                
                // Normalizar acentos para comparação
                const normalizeStr = (str) => str.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
                const normContinent = normalizeStr(continent);

                return activeFilters.region.some(region => {
                    const normRegion = normalizeStr(region.toLowerCase());
                    return normContinent.includes(normRegion);
                });
            });
        }

        // Filtrar por taxonomia
        if (activeFilters.taxonomy && activeFilters.taxonomy.length > 0) {
            filtered = filtered.filter(m => {
                if (!m.taxonomy_order) return false;
                const taxonomy = String(m.taxonomy_order).toUpperCase().trim();
                
                return activeFilters.taxonomy.some(tax => {
                    return taxonomy === String(tax).toUpperCase().trim();
                });
            });
        }

        // Filtrar por busca de texto
        if (query) {
            filtered = filtered.filter(m =>
                (m.common_name && m.common_name.toLowerCase().includes(query)) ||
                (m.binomial_name && m.binomial_name.toLowerCase().includes(query)) ||
                (m.description && m.description.toLowerCase().includes(query))
            );
        }

        filteredMammals = filtered;
        currentPage = 1; // Resetar para primeira página ao filtrar
        displayMammalsWithPagination();
    }

    function displayMammalsWithPagination() {
        const totalItems = filteredMammals.length;
        const totalPages = itemsPerPage === 'all' ? 1 : Math.ceil(totalItems / itemsPerPage);

        // Ajustar página atual se necessário
        if (currentPage > totalPages) currentPage = totalPages || 1;

        // Calcular itens da página atual
        let mammalsToDisplay;
        if (itemsPerPage === 'all') {
            mammalsToDisplay = filteredMammals;
        } else {
            const startIndex = (currentPage - 1) * itemsPerPage;
            const endIndex = startIndex + itemsPerPage;
            mammalsToDisplay = filteredMammals.slice(startIndex, endIndex);
        }

        // Renderizar mamíferos
        renderMammals(mammalsToDisplay);

        // Atualizar contador
        const speciesCount = document.getElementById('species-count');
        if (speciesCount) {
            speciesCount.textContent = `${getTranslation('all_species')} (${totalItems})`;
        }

        // Atualizar informações de paginação
        updatePaginationInfo(totalItems, totalPages);
    }

    function renderMammals(mammals) {
        if (!mammalsList) return;

        if (mammals.length === 0) {
            mammalsList.innerHTML = `
                <div class="no-results" style="grid-column: 1/-1; text-align: center; padding: 3rem; background-color: var(--card-bg); border-radius: 12px; box-shadow: var(--shadow-md);">
                    <p style="font-size: 1.5rem; color: var(--text-light); margin: 0;">🔍 ${getTranslation('no_results')}</p>
                    <p style="font-size: 1rem; color: var(--text-light); margin-top: 0.5rem;">${getTranslation('try_adjust_filters')}</p>
                </div>
            `;
            return;
        }

        const mammalsHTML = mammals
            .map(mammal => `
                <div class="mammal-card">
                    ${mammal.image_url ? `
                    <div class="card-image">
                        <img src="${mammal.image_url}" 
                             alt="${escapeHtml(mammal.common_name)}"
                             loading="lazy"
                             onerror="if (this.src.indexOf('/media/') !== -1 && '${escapeHtml(mammal.image_filename)}') { this.onerror=null; this.src = '/static/images/' + '${escapeHtml(mammal.image_filename)}'; } else { this.onerror=null; this.parentElement.innerHTML='<div class=\\'placeholder-content\\'><span class=\\'placeholder-icon\\'>📷</span><span class=\\'placeholder-text\\'>${getTranslation('no_image') || 'Sem imagem'}</span></div>'; this.parentElement.classList.add('placeholder-image'); }">
                    </div>
                    ` : `
                    <div class="card-image placeholder-image">
                        <div class="placeholder-content">
                            <span class="placeholder-icon">📷</span>
                            <span class="placeholder-text">${getTranslation('no_image') || 'Sem imagem'}</span>
                        </div>
                    </div>
                    `}
                    <div class="card-header">
                        <h4 class="common-name">${escapeHtml(mammal.common_name)}</h4>
                        <p class="binomial-name"><em>${escapeHtml(mammal.binomial_name)}</em></p>
                    </div>
                    <div class="card-body">
                        <p class="description">${escapeHtml(mammal.description.substring(0, 150))}${mammal.description.length > 150 ? '...' : ''}</p>
                    </div>
                    <div class="card-footer">
                        <a href="${(window.URLS && window.URLS.mammalBase) ? window.URLS.mammalBase + mammal.id + '/' : '/mammal/' + mammal.id + '/'}" class="btn-primary">${getTranslation('view_details')} →</a>
                    </div>
                </div>
            `)
            .join("");

        mammalsList.innerHTML = mammalsHTML;
    }

    function updatePaginationInfo(totalItems, totalPages) {
        const currentPageEl = document.getElementById('current-page');
        const totalPagesEl = document.getElementById('total-pages');
        const totalItemsEl = document.getElementById('total-items');
        const firstPageBtn = document.getElementById('first-page-btn');
        const prevPageBtn = document.getElementById('prev-page-btn');
        const nextPageBtn = document.getElementById('next-page-btn');
        const lastPageBtn = document.getElementById('last-page-btn');

        if (currentPageEl) currentPageEl.textContent = currentPage;
        if (totalPagesEl) totalPagesEl.textContent = totalPages;
        if (totalItemsEl) totalItemsEl.textContent = totalItems;

        // Desabilitar/habilitar botões
        if (firstPageBtn) {
            firstPageBtn.disabled = currentPage === 1;
            firstPageBtn.classList.toggle('disabled', currentPage === 1);
        }
        if (prevPageBtn) {
            prevPageBtn.disabled = currentPage === 1;
            prevPageBtn.classList.toggle('disabled', currentPage === 1);
        }
        if (nextPageBtn) {
            nextPageBtn.disabled = currentPage === totalPages || itemsPerPage === 'all';
            nextPageBtn.classList.toggle('disabled', currentPage === totalPages || itemsPerPage === 'all');
        }
        if (lastPageBtn) {
            lastPageBtn.disabled = currentPage === totalPages || itemsPerPage === 'all';
            lastPageBtn.classList.toggle('disabled', currentPage === totalPages || itemsPerPage === 'all');
        }

        // Ocultar apenas os botões de navegação se "Todos" estiver selecionado
        const paginationNav = document.querySelector('.pagination-nav');
        const paginationTotal = document.querySelector('.pagination-total');

        if (paginationNav) {
            paginationNav.style.display = itemsPerPage === 'all' ? 'none' : 'flex';
        }
        if (paginationTotal) {
            paginationTotal.style.display = itemsPerPage === 'all' ? 'none' : 'block';
        }
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function clearFilters() {
        if (searchInput) searchInput.value = "";
        activeFilters = { region: [], taxonomy: [] };
        filterButtons.forEach(btn => btn.classList.remove("active"));
        filteredMammals = allMammals;
        currentPage = 1;
        displayMammalsWithPagination();
        updateFilterBadge();
        renderActiveTags();
    }

    function updateFilterBadge() {
        const badge = document.getElementById('filter-badge');
        const toggleBtn = document.getElementById('filter-toggle-btn');
        const count = activeFilters.region.length + activeFilters.taxonomy.length;
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-flex' : 'none';
        }
        if (toggleBtn) {
            toggleBtn.classList.toggle('active', count > 0);
        }
    }

    function renderActiveTags() {
        const container = document.getElementById('active-filters');
        if (!container) return;
        let tags = [];
        Object.entries(activeFilters).forEach(([type, values]) => {
            if (!Array.isArray(values)) return;
            values.forEach(value => {
                const btn = document.querySelector(`.filter-btn[data-filter-type="${type}"][data-filter-value="${value}"]`);
                const label = btn ? btn.textContent.trim() : value;
                tags.push(`<span class="filter-tag">${label} <button class="filter-tag-remove" data-type="${type}" data-value="${value}" title="Remove filter">×</button></span>`);
            });
        });
        container.innerHTML = tags.join('');
        container.style.display = tags.length > 0 ? 'flex' : 'none';
        
        container.querySelectorAll('.filter-tag-remove').forEach(btn => {
            btn.addEventListener('click', () => {
                const type = btn.dataset.type;
                const val = btn.dataset.value;
                if (Array.isArray(activeFilters[type])) {
                    activeFilters[type] = activeFilters[type].filter(v => v !== val);
                }
                const b = document.querySelector(`.filter-btn[data-filter-type="${type}"][data-filter-value="${val}"]`);
                if (b) {
                    b.classList.remove('active');
                    b.setAttribute('aria-pressed', 'false');
                }
                performSearch();
                updateFilterBadge();
                renderActiveTags();
            });
        });
    }

    // Event Listeners
    if (searchBtn) {
        searchBtn.addEventListener("click", performSearch);
    }

    if (searchInput) {
        searchInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                performSearch();
            }
        });

        // Busca em tempo real
        searchInput.addEventListener("input", performSearch);
    }

    if (clearBtn) {
        clearBtn.addEventListener("click", clearFilters);
    }

    filterButtons.forEach((button) => {
        button.addEventListener("click", function () {
            const filterType = this.dataset.filterType;
            const filterValue = this.dataset.filterValue;

            if (activeFilters[filterType].includes(filterValue)) {
                // Desativar filtro
                activeFilters[filterType] = activeFilters[filterType].filter(v => v !== filterValue);
                this.classList.remove("active");
                this.setAttribute("aria-pressed", "false");
            } else {
                // Ativar filtro
                activeFilters[filterType].push(filterValue);
                this.classList.add("active");
                this.setAttribute("aria-pressed", "true");
            }

            performSearch();
            updateFilterBadge();
            renderActiveTags();
        });
    });

    // Filter dropdown toggle
    const filterToggleBtn = document.getElementById('filter-toggle-btn');
    const filterPanel = document.getElementById('filter-panel');
    const clearFiltersBtn = document.getElementById('clear-filters-btn');

    if (filterToggleBtn && filterPanel) {
        filterToggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = filterPanel.style.display !== 'none';
            filterPanel.style.display = isOpen ? 'none' : 'block';
            filterToggleBtn.setAttribute('aria-expanded', !isOpen);
        });
        // Close panel when clicking outside
        document.addEventListener('click', (e) => {
            if (!filterPanel.contains(e.target) && e.target !== filterToggleBtn) {
                filterPanel.style.display = 'none';
                filterToggleBtn.setAttribute('aria-expanded', 'false');
            }
        });
        // Prevent panel clicks from closing it
        filterPanel.addEventListener('click', (e) => e.stopPropagation());
    }

    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', () => {
            clearFilters();
        });
    }

    // Event Listeners de Paginação
    const firstPageBtn = document.getElementById('first-page-btn');
    const prevPageBtn = document.getElementById('prev-page-btn');
    const nextPageBtn = document.getElementById('next-page-btn');
    const lastPageBtn = document.getElementById('last-page-btn');
    const itemsPerPageSelect = document.getElementById('items-per-page');

    if (firstPageBtn) {
        firstPageBtn.addEventListener('click', () => {
            currentPage = 1;
            displayMammalsWithPagination();
        });
    }

    if (prevPageBtn) {
        prevPageBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                displayMammalsWithPagination();
            }
        });
    }

    if (nextPageBtn) {
        nextPageBtn.addEventListener('click', () => {
            const totalPages = Math.ceil(filteredMammals.length / itemsPerPage);
            if (currentPage < totalPages) {
                currentPage++;
                displayMammalsWithPagination();
            }
        });
    }

    if (lastPageBtn) {
        lastPageBtn.addEventListener('click', () => {
            const totalPages = Math.ceil(filteredMammals.length / itemsPerPage);
            currentPage = totalPages;
            displayMammalsWithPagination();
        });
    }

    if (itemsPerPageSelect) {
        itemsPerPageSelect.addEventListener('change', (e) => {
            const value = e.target.value;
            itemsPerPage = value === 'all' ? 'all' : parseInt(value);
            currentPage = 1; // Resetar para primeira página
            displayMammalsWithPagination();
        });
    }

    // Carregar mamíferos ao iniciar
    loadAllMammals();
});



// ============================================================================
// MODO ESCURO - TOGGLE DE TEMA
// ============================================================================

(function initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.querySelector('.theme-toggle-icon');
    const themeText = document.querySelector('.theme-toggle-text');

    if (!themeToggle) return;

    // Carregar tema salvo do localStorage
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);

    // Event listener para o botão de toggle
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
        localStorage.setItem('theme', newTheme);
    });

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);

        if (theme === 'dark') {
            themeIcon.textContent = '☀️';
            themeText.textContent = getTranslation('light_theme');
            themeToggle.setAttribute('aria-pressed', 'true');
        } else {
            themeIcon.textContent = '🌙';
            themeText.textContent = getTranslation('dark_theme');
            themeToggle.setAttribute('aria-pressed', 'false');
        }
    }
})();




// ============================================================================
// MENU HAMBÚRGUER MOBILE
// ============================================================================

(function initMobileMenu() {
    const hamburgerMenu = document.getElementById('hamburger-menu');
    const menuClose = document.getElementById('menu-close');
    const navMenu = document.getElementById('nav-menu');
    const menuOverlay = document.getElementById('menu-overlay');
    const navLinks = document.querySelectorAll('.nav-link');

    if (!hamburgerMenu || !navMenu || !menuOverlay) return;

    // Abrir menu
    function openMenu() {
        navMenu.classList.add('active');
        menuOverlay.classList.add('active');
        hamburgerMenu.setAttribute('aria-expanded', 'true');
        document.body.style.overflow = 'hidden'; // Prevenir scroll
    }

    // Fechar menu
    function closeMenu() {
        navMenu.classList.remove('active');
        menuOverlay.classList.remove('active');
        hamburgerMenu.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = ''; // Restaurar scroll
    }

    // Event listeners
    hamburgerMenu.addEventListener('click', openMenu);

    if (menuClose) {
        menuClose.addEventListener('click', closeMenu);
    }

    menuOverlay.addEventListener('click', closeMenu);

    // Fechar menu ao clicar em um link
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 1024) {
                closeMenu();
            }
        });
    });

    // Fechar menu ao pressionar ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && navMenu.classList.contains('active')) {
            closeMenu();
        }
    });

    // Fechar menu ao redimensionar para desktop
    window.addEventListener('resize', () => {
        if (window.innerWidth > 1024 && navMenu.classList.contains('active')) {
            closeMenu();
        }
    });
})();




// ============================================================================
// SCROLL REVEAL - ANIMAÇÃO AO ROLAR A PÁGINA
// ============================================================================

(function initScrollReveal() {
    const revealElements = document.querySelectorAll('.reveal');

    if (revealElements.length === 0) return;

    const revealOnScroll = () => {
        const windowHeight = window.innerHeight;
        const revealPoint = 100;

        revealElements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;

            if (elementTop < windowHeight - revealPoint) {
                element.classList.add('active');
            }
        });
    };

    // Revelar elementos visíveis ao carregar
    revealOnScroll();

    // Revelar elementos ao rolar
    window.addEventListener('scroll', revealOnScroll);
})();
