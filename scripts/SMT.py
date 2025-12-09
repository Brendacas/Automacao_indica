import pandas as pd
from playwright.sync_api import sync_playwright
import os

# Mapeamento de Mês
MESES_MAP = {
    '1': 'Janeiro', '2': 'Fevereiro', '3': 'Março', '4': 'Abril',
    '5': 'Maio', '6': 'Junho', '7': 'Julho', '8': 'Agosto',
    '9': 'Setembro', '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro'
}

def SMT_download():
    """
    Baixa o arquivo do Novo Caged usando Playwright.
    """
    print("Iniciando o download SMT (Playwright)...")
    # Define a pasta segura
    temp_folder = "/var/www/indica/automacao_python/documentos_novos"
    os.makedirs(temp_folder, exist_ok=True)

    try:
        with sync_playwright() as p: 
            # Configuração vital para servidor Linux (Headless + No Sandbox)
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"])
            page = browser.new_page()
            
            # Aumentei o timeout para 90s (governo é lento)
            page.goto("https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/novo-caged", timeout=90000)
            print(f"Página acessada: {page.title()}") 

            link_locator = page.get_by_role("link", name="Tabelas.xlsx")
            link_url = link_locator.get_attribute("href")

            if link_url:
                print(f"Link encontrado: {link_url}")
                page.goto(link_url)
                
                # Tenta baixar
                with page.expect_download(timeout=120000) as download_info:
                    try:
                        botao_baixar = page.get_by_role("button", name="Baixar", exact=True)
                        if botao_baixar.is_visible():
                            botao_baixar.click()
                    except:
                        pass # Se baixar sozinho, ok
                
                download = download_info.value
                file_path = os.path.join(temp_folder, "SMT_temp_raw.xlsx")
                download.save_as(file_path)

                print(f"Download concluído: {file_path}")
                #browser.close()
                return file_path
            else:
                print("ERRO: Link não encontrado.")
                #browser.close()
                return None
            
    except Exception as e:
        print(f"Erro no Playwright: {e}")
        return None

def processar_excel(caminho_original, uf, ano, mes_num):
    """
    Filtra o Excel e SALVA NO DISCO.
    """
    try:
        SMT_Sheet = 'Tabela 8' 
        nome_mes = MESES_MAP.get(str(mes_num))
        
        if not nome_mes:
            print(f"Mês inválido: {mes_num}")
            return None, None
            
        print(f"Processando para {uf} - {nome_mes}/{ano}")
        
        df = pd.read_excel(caminho_original, sheet_name=SMT_Sheet, header=4)
        df.columns = df.columns.str.strip()

        coluna_data = f"{nome_mes}/{ano}"
        if coluna_data not in df.columns:
            print(f"Coluna {coluna_data} não encontrada.")
            return None, None

        df_filtrado = df[df['UF'] == uf]
        
        if df_filtrado.empty:
            print("Filtro vazio.")
            return None, None

        cols = ['UF', 'Código do Município', 'Município', coluna_data]
        df_final = df_filtrado[cols]

        # SALVA NO DISCO
        nome_saida = f"SMT_{uf}_{ano}_{mes_num}.xlsx"
        pasta_destino = "/var/www/indica/automacao_python/documentos_novos"
        os.makedirs(pasta_destino, exist_ok=True)
        
        caminho_final = os.path.join(pasta_destino, nome_saida)
        
        df_final.to_excel(caminho_final, index=False)
        print(f"Arquivo salvo: {caminho_final}")
        
        return caminho_final, nome_saida

    except Exception as e:
        print(f"Erro no processamento Pandas: {e}")
        return None, None

# --- FUNÇÃO PRINCIPAL CORRIGIDA ---
# AGORA ACEITA ARGUMENTOS!
def processar_smt(uf, ano, mes_num):
    
    try:
        # 1. Baixa
        caminho_raw = SMT_download()
        
        if caminho_raw and os.path.exists(caminho_raw):
            # 2. Processa
            caminho_final, nome_final = processar_excel(caminho_raw, uf, ano, mes_num)
            
            # Limpeza
            try:
                os.remove(caminho_raw)
            except:
                pass
                
            return caminho_final, nome_final
        else:
            return None, None

    except Exception as e:
        print(f"Erro geral SMT: {e}")
        return None, None
