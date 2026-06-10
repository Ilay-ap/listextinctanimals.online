"""
Serviço de tradução automática com cache inteligente
Usa deep-translator (Google Translate gratuito) com cache persistente
"""
from django.core.cache import cache
from django.db import models
import hashlib


def get_translation_cache_key(text, source_lang, target_lang):
    """Gera chave única para cache de tradução"""
    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    return f"trans_{source_lang}_{target_lang}_{text_hash}"


def translate_text(text, source_lang='pt', target_lang='en'):
    """
    Traduz texto usando deep-translator com cache inteligente
    
    Args:
        text: Texto para traduzir
        source_lang: Idioma de origem (pt, en, es, etc.)
        target_lang: Idioma de destino (pt, en, es, etc.)
    
    Returns:
        Texto traduzido (instantâneo se estiver em cache)
    """
    if not text or not text.strip():
        return text
    
    # Normalizar códigos de idioma
    source_lang = source_lang.split('-')[0].lower()
    target_lang = target_lang.split('-')[0].lower()
    
    # Se for o mesmo idioma, retornar original
    if source_lang == target_lang:
        return text
    
    # Buscar no cache primeiro (INSTANTÂNEO)
    cache_key = get_translation_cache_key(text, source_lang, target_lang)
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Se não estiver em cache, traduzir via API
    try:
        from deep_translator import GoogleTranslator
        
        # Traduzir
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        
        # Dividir texto longo em partes (limite de 5000 caracteres)
        max_length = 4500
        if len(text) <= max_length:
            translated = translator.translate(text)
        else:
            # Dividir por parágrafos para manter formatação
            paragraphs = text.split('\n\n')
            translated_paragraphs = []
            current_chunk = ""
            
            for para in paragraphs:
                if len(current_chunk) + len(para) + 2 < max_length:
                    current_chunk += para + "\n\n"
                else:
                    if current_chunk.strip():
                        translated_paragraphs.append(translator.translate(current_chunk.strip()))
                    current_chunk = para + "\n\n"
            
            if current_chunk.strip():
                translated_paragraphs.append(translator.translate(current_chunk.strip()))
            
            translated = "\n\n".join(translated_paragraphs)
        
        # Salvar no cache por 30 dias (praticamente permanente)
        cache.set(cache_key, translated, 60 * 60 * 24 * 30)
        
        return translated
        
    except ImportError:
        # Se deep-translator não estiver instalado, retornar texto original
        return text
    except Exception as e:
        # Em caso de erro, retornar texto original
        print(f"Erro ao traduzir: {e}")
        return text


class TranslatedMammal:
    """
    Wrapper que retorna mamífero com conteúdo traduzido
    Usa cache para performance máxima
    """
    def __init__(self, mammal, target_lang='en'):
        self.mammal = mammal
        self.target_lang = target_lang.split('-')[0].lower()
        self._translation_cache = {}
    
    def _translate_field(self, field_name):
        """Traduz um campo específico com cache"""
        if field_name in self._translation_cache:
            return self._translation_cache[field_name]
        
        original_value = getattr(self.mammal, field_name, '')
        if not original_value:
            return ''
        
        # Se for português, retornar original
        if self.target_lang == 'pt':
            translated = original_value
        else:
            translated = translate_text(original_value, 'pt', self.target_lang)
        
        self._translation_cache[field_name] = translated
        return translated
    
    @property
    def common_name(self):
        return self.mammal.common_name
    
    @property
    def binomial_name(self):
        return self.mammal.binomial_name
    
    @property
    def description(self):
        return self._translate_field('description')
    
    @property
    def short_description(self):
        desc = self.description
        if len(desc) > 200:
            return desc[:200] + '...'
        return desc
    
    @property
    def habitat(self):
        return self._translate_field('habitat')
    
    @property
    def distribution(self):
        return self._translate_field('distribution')
    
    @property
    def extinction_causes(self):
        return self._translate_field('extinction_causes')
    
    @property
    def taxonomy_order(self):
        return self.mammal.taxonomy_order
    
    @property
    def continent(self):
        return self.mammal.continent
    
    @property
    def image_filename(self):
        return self.mammal.image_filename
    
    @property
    def pk(self):
        return self.mammal.pk
    
    @property
    def id(self):
        return self.mammal.id
    
    def __getattr__(self, name):
        """Fallback para atributos não traduzidos"""
        return getattr(self.mammal, name)

