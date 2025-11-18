import pandas as pd
from playwright.sync_api import sync_playwright
import re
import os
import io # <-- Importar IO

# Mapeamento de Mês - formato "Janeiro/2020"
MESES_MAP = {
    '1': 'Janeiro', '2': 'Fevereiro', '3': 'Março', '4': 'Abril',
    '5': 'Maio', '6': 'Junho', '7': 'Julho', '8': 'Agosto',
    '9': 'Setembro', '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro'
}

# --- 1. DOWNLOAD COM PLAYWRIGHT ---
def SMT_download():
    """
    Navega até o site e baixa o arquivo de tabelas.
    Retorna o caminho do arquivo baixado se for bem-sucedido, senão None.
    """
    print("Iniciando o download (Playwright)...")
    try:
        with sync_playwright() as p: 
            browser = p.chromium.launch() 
            page = browser.new_page()
            page.goto("https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/novo-caged")
            print(f"Página Inicial: {page.title()}") 

            link_locator = page.get_by_role("link", name="Tabelas.xls")
            link_url = link_locator.get_attribute("href")

            if link_url:
                print(f"\nURL extraída do link: {link_url}")
                page.goto(link_url)
                assert "drive.google.com" in page.url
                page.wait_for_load_state("domcontentloaded")
                print(f"Navegação bem-sucedida para o Google Drive: {page.url}")

                exp_Regex = re.compile(r"3-tabelas.*\.xlsx")
                arquivo_locator = page.get_by_text(exp_Regex)
                arquivo_locator.hover()
                page.wait_for_timeout(2000)
                
                with page.expect_download(timeout=60000) as download_info:
                    botao_baixar = page.get_by_role("button", name="Baixar", exact=True)
                    botao_baixar.wait_for(state="visible", timeout=50000)
                    botao_baixar.click()
                
                download = download_info.value
                
                # Salva em uma pasta temporária
                temp_folder = "temp_downloads"
                os.makedirs(temp_folder, exist_ok=True)
                file_path = os.path.join(temp_folder, download.suggested_filename)
                
                download.save_as(file_path)

                print(f"\nDownload concluído. Arquivo salvo em: {file_path}")
                browser.close()
                return file_path # Retorna o caminho do arquivo baixado

            else:
                print("ERRO: Não foi possível extrair o atributo 'href'.")
                browser.close()
                return None
            
    except Exception as e:
        print(f"Ocorreu um erro no download com Playwright: {e}")
        return None

# ---  PROCESSAMENTO COM PANDAS ---
def processar_excel(caminho_original, uf, ano, mes_num):
    """
    Recebe o caminho do arquivo baixado, processa, e retorna um 
    buffer em memória e o nome do novo arquivo.
    """
    
    SMT = 'Tabela 8' 
    coluna_uf = 'UF' 
    COLUNA_COD_MUN = 'Código do Município'
    COLUNA_MUNICIPIO = 'Município'
    
    try:
        nome_mes = MESES_MAP.get(str(mes_num))
        if not nome_mes:
            print(f"Erro: Número do mês '{mes_num}' é inválido.")
            return None, None
        
        nome_coluna_data = f"{nome_mes}/{ano}"
        nome_excel_saida = f"SMT_{uf}_{ano}_{mes_num}.xlsx"
        print(f"Coluna de data alvo: {nome_coluna_data}")

        print(f"Lendo a aba '{SMT}' do arquivo: {caminho_original}...")
        df = pd.read_excel(caminho_original, sheet_name=SMT, header=4) 

        print("Limpando nomes das colunas...")
        df.columns = df.columns.str.strip()

        colunas_para_manter = [coluna_uf, COLUNA_COD_MUN, COLUNA_MUNICIPIO, nome_coluna_data]
        
        # Validação das colunas
        for col in colunas_para_manter:
            if col not in df.columns:
                print(f"Erro: A coluna '{col}' não foi encontrada.")
                print(f"Colunas disponíveis: {list(df.columns)}")
                return None, None

        # Filtrar
        print(f"Filtrando LINHAS pela UF: '{uf}'...")
        condicao_uf = (df[coluna_uf] == uf)
        df_linhas_filtradas = df[condicao_uf]
        
        print(f"Selecionando COLUNAS...")
        df_filtrado = df_linhas_filtradas[colunas_para_manter]
        
        if df_filtrado.empty:
            print(f"Aviso: Nenhum dado encontrado para UF '{uf}'.")
            return None, None

        # Salvar em memória
        print(f"\nSalvando os dados modificados na memória...")
        output_buffer = io.BytesIO()
        df_filtrado.to_excel(output_buffer, index=False, sheet_name=SMT) 
        output_buffer.seek(0)
        
        print(f"Buffer criado com sucesso. Nome do arquivo: {nome_excel_saida}")
        return output_buffer, nome_excel_saida

    except Exception as e:
        print(f"Ocorreu um erro inesperado no processamento: {e}")
        return None, None


# --- FUNÇÃO PRINCIPAL (Chamada pelo Flask) ---
def processar_smt(uf, ano, mes_num):
    
    caminho_arquivo_baixado = None
    try:
        # 1. Executa o Download 
        caminho_arquivo_baixado = SMT_download()
        
        if caminho_arquivo_baixado:
            print("\n--- Download concluído. Processando filtros ---")
            
            # 2. Processa o arquivo
            buffer, nome_arquivo = processar_excel(caminho_arquivo_baixado, uf, ano, mes_num)
            
            return buffer, nome_arquivo
        else:
            print("Download falhou. O script não pode continuar.")
            return None, None
            
    except Exception as e:
        print(f"Ocorreu um erro durante a automação SMT: {e}")
        return None, None
    finally:
        # LIMPEZA: Remove o arquivo temporário
        if caminho_arquivo_baixado and os.path.exists(caminho_arquivo_baixado):
            print(f"Limpando arquivo temporário: {caminho_arquivo_baixado}")
            os.remove(caminho_arquivo_baixado)