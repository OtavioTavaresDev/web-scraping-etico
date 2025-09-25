"""
PROJETO PORTFÓLIO: ANALISADOR DE LIVROS - WEB SCRAPING ÉTICO
Autor: Otávio Augusto De Souza Tavares
Data: 24/09/2025
Descrição: Projeto educacional de web scraping usando sites de demonstração
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import os
from datetime import datetime
import logging

# Configurar logging para monitoramento
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping_log.log'),
        logging.StreamHandler()
    ]
)

class AnalisadorLivros:
    """
    Classe para análise ética de livros usando web scraping
    Sites utilizados: Books to Scrape (site de demonstração)
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_headers()
        self.dados_coletados = []
        
    def setup_headers(self):
        """Configurar headers éticos para identificar o bot"""
        self.session.headers.update({
            'User-Agent': 'AnalisadorLivros-Educacional/1.0 (+https://github.com/seu-usuario/portfolio-web-scraping)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def verificar_robots_txt(self, base_url):
        """
        Verificar robots.txt antes de fazer scraping
        Boa prática ética importante
        """
        try:
            robots_url = f"{base_url}/robots.txt"
            response = self.session.get(robots_url, timeout=10)
            
            if response.status_code == 200:
                logging.info("📋 Robots.txt encontrado:")
                logging.info(f"Conteúdo do robots.txt:\n{response.text[:500]}...")
                
                # Verificar se scraping é permitido
                if 'Disallow: /' in response.text:
                    logging.warning("⚠️  Robots.txt pode restringir acesso total")
                else:
                    logging.info("✅ Robots.txt permite acesso")
                    
            return True
        except Exception as e:
            logging.warning(f"❌ Não foi possível verificar robots.txt: {e}")
            return False
    
    def fazer_requisicao_segura(self, url, delay=1):
        """
        Fazer requisição HTTP com tratamento de erros e delays
        """
        try:
            time.sleep(delay)  # Respeitar o servidor
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()  # Levanta exceção para status 4xx/5xx
            
            logging.info(f"✅ Requisição bem-sucedida: {url} (Status: {response.status_code})")
            return response
            
        except requests.exceptions.Timeout:
            logging.error(f"⏰ Timeout na requisição: {url}")
            return None
        except requests.exceptions.HTTPError as e:
            logging.error(f"🚫 Erro HTTP {response.status_code}: {url} - {e}")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"🔌 Erro de conexão: {url} - {e}")
            return None
    
    def extrair_info_livro(self, livro_element):
        """
        Extrair informações de um elemento livro individual
        """
        try:
            # Extrair título
            titulo = livro_element.h3.a['title']
            
            # Extrair preço
            preco_element = livro_element.find('p', class_='price_color')
            preco = preco_element.text if preco_element else 'N/A'
            
            # Extrair disponibilidade
            disponibilidade_element = livro_element.find('p', class_='instock availability')
            disponibilidade = disponibilidade_element.text.strip() if disponibilidade_element else 'N/A'
            
            # Extrair avaliação (rating)
            rating_element = livro_element.find('p', class_='star-rating')
            rating_classes = rating_element.get('class', []) if rating_element else []
            rating = next((cls for cls in rating_classes if cls != 'star-rating'), 'N/A')
            
            # Converter rating para número
            rating_map = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
            rating_numero = rating_map.get(rating, 0)
            
            return {
                'titulo': titulo,
                'preco': preco,
                'disponibilidade': disponibilidade,
                'rating_texto': rating,
                'rating_numero': rating_numero,
                'timestamp_coleta': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"❌ Erro ao extrair info do livro: {e}")
            return None
    
    def scrape_pagina_unica(self, url):
        """
        Fazer scraping de uma única página
        """
        logging.info(f"🔍 Iniciando scraping da página: {url}")
        
        response = self.fazer_requisicao_segura(url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Encontrar todos os livros na página
        livros = soup.find_all('article', class_='product_pod')
        logging.info(f"📚 Encontrados {len(livros)} livros na página")
        
        dados_pagina = []
        
        for i, livro in enumerate(livros, 1):
            info_livro = self.extrair_info_livro(livro)
            if info_livro:
                info_livro['numero_sequencia'] = i
                dados_pagina.append(info_livro)
                logging.info(f"✅ Livro {i} processado: {info_livro['titulo'][:30]}...")
        
        return dados_pagina
    
    def scrape_multiplas_paginas(self, url_base, total_paginas=3):
        """
        Fazer scraping de múltiplas páginas com controle
        """
        logging.info(f"🚀 Iniciando scraping de {total_paginas} páginas")
        
        todas_info_livros = []
        
        for pagina in range(1, total_paginas + 1):
            url = f"{url_base}/catalogue/page-{pagina}.html"
            logging.info(f"📄 Processando página {pagina}/{total_paginas}")
            
            livros_pagina = self.scrape_pagina_unica(url)
            for livro in livros_pagina:
                livro['pagina'] = pagina
                todas_info_livros.append(livro)
            
            # Delay maior entre páginas para ser ético
            time.sleep(2)
        
        logging.info(f"🎯 Total de livros coletados: {len(todas_info_livros)}")
        return todas_info_livros
    
    def analisar_dados(self, dados_livros):
        """
        Realizar análise básica dos dados coletados
        """
        if not dados_livros:
            logging.warning("📊 Nenhum dado para analisar")
            return {}
        
        df = pd.DataFrame(dados_livros)
        
        analise = {
            'total_livros': len(dados_livros),
            'preco_medio': 'N/A',
            'avaliacao_media': 0,
            'distribuicao_rating': {},
            'livros_por_pagina': {}
        }
        
        try:
            # Análise de preços (remover símbolo de moeda)
            precos = df['preco'].str.replace('£', '').astype(float)
            analise['preco_medio'] = f"£{precos.mean():.2f}"
            
            # Análise de ratings
            analise['avaliacao_media'] = df['rating_numero'].mean()
            analise['distribuicao_rating'] = df['rating_texto'].value_counts().to_dict()
            analise['livros_por_pagina'] = df['pagina'].value_counts().sort_index().to_dict()
            
        except Exception as e:
            logging.error(f"❌ Erro na análise: {e}")
        
        return analise
    
    def exportar_dados(self, dados_livros, analise):
        """
        Exportar dados em múltiplos formatos para portfólio
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Criar diretório de resultados
        os.makedirs('resultados', exist_ok=True)
        
        # Exportar para CSV
        df = pd.DataFrame(dados_livros)
        csv_path = f'resultados/livros_analisados_{timestamp}.csv'
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        # Exportar para JSON
        json_path = f'resultados/livros_analisados_{timestamp}.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'data_coleta': timestamp,
                    'total_livros': len(dados_livros),
                    'projeto': 'Analisador de Livros - Web Scraping Ético'
                },
                'analise': analise,
                'dados': dados_livros
            }, f, indent=2, ensure_ascii=False)
        
        # Exportar análise resumida
        resumo_path = f'resultados/resumo_analise_{timestamp}.txt'
        with open(resumo_path, 'w', encoding='utf-8') as f:
            f.write("=== RESUMO DA ANÁLISE DE LIVROS ===\n\n")
            f.write(f"Data da coleta: {timestamp}\n")
            f.write(f"Total de livros analisados: {analise['total_livros']}\n")
            f.write(f"Preço médio: {analise['preco_medio']}\n")
            f.write(f"Avaliação média: {analise['avaliacao_media']:.2f}/5.0\n\n")
            
            f.write("Distribuição por rating:\n")
            for rating, count in analise['distribuicao_rating'].items():
                f.write(f"  {rating}: {count} livros\n")
        
        logging.info(f"💾 Dados exportados:")
        logging.info(f"   CSV: {csv_path}")
        logging.info(f"   JSON: {json_path}")
        logging.info(f"   Resumo: {resumo_path}")
        
        return csv_path, json_path
    
    def gerar_relatorio(self, analise):
        """
        Gerar relatório formatado para exibição
        """
        print("\n" + "="*60)
        print("📊 RELATÓRIO DE ANÁLISE - WEB SCRAPING ÉTICO")
        print("="*60)
        
        print(f"📚 Total de livros analisados: {analise['total_livros']}")
        print(f"💰 Preço médio: {analise['preco_medio']}")
        print(f"⭐ Avaliação média: {analise['avaliacao_media']:.2f}/5.0")
        
        print("\n📈 Distribuição por avaliação:")
        for rating, count in analise.get('distribuicao_rating', {}).items():
            print(f"   {rating}: {count} livros")
        
        print("\n🌐 Livros por página:")
        for pagina, count in analise.get('livros_por_pagina', {}).items():
            print(f"   Página {pagina}: {count} livros")
        
        print("\n✅ Coleta realizada com práticas éticas de web scraping")
        print("="*60)

def main():
    """
    Função principal - executar todo o pipeline
    """
    print("🚀 INICIANDO ANALISADOR DE LIVROS - WEB SCRAPING ÉTICO")
    print("📍 Site utilizado: Books to Scrape (site de demonstração)")
    print("⏰ Aguarde, isso pode levar alguns segundos...\n")
    
    # Inicializar analisador
    analisador = AnalisadorLivros()
    
    # Configurações
    BASE_URL = "http://books.toscrape.com"
    TOTAL_PAGINAS = 3  # Limitar para demonstração
    
    try:
        # 1. Verificar robots.txt (boas práticas)
        analisador.verificar_robots_txt(BASE_URL)
        
        # 2. Fazer scraping das páginas
        dados_livros = analisador.scrape_multiplas_paginas(BASE_URL, TOTAL_PAGINAS)
        
        if not dados_livros:
            logging.error("❌ Nenhum dado foi coletado")
            return
        
        # 3. Analisar dados
        analise = analisador.analisar_dados(dados_livros)
        
        # 4. Exportar dados
        analisador.exportar_dados(dados_livros, analise)
        
        # 5. Gerar relatório
        analisador.gerar_relatorio(analise)
        
        logging.info("🎉 Processo concluído com sucesso!")
        
    except KeyboardInterrupt:
        logging.info("⏹️  Processo interrompido pelo usuário")
    except Exception as e:
        logging.error(f"💥 Erro crítico: {e}")

if __name__ == "__main__":
    main()