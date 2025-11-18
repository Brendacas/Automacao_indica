import requests
import os
import pandas as pd
import io  # Importa a biblioteca para IO em memória
import urllib3 

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #silenciar os avisos

def baixar_em_memoria(tipo, ano):
    """
    Baixa o CSV do Comexstat para a memória (usando streaming) 
    e o carrega em um DataFrame.
    """
    url_base = "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/mun/"
    link_download = f"{url_base}{tipo}_{ano}_MUN.csv"

    print(f"Baixando e processando em memória (streaming): {link_download}...")
    
    try:
        # 3. Usamos 'stream=True' e um 'with' statement
        with requests.get(link_download, timeout=600, verify=False, stream=True) as resposta:
            
            # Verifica o status DEPOIS de obter a resposta
            if resposta.status_code != 200:
                print(f"Erro: Falha ao baixar o arquivo. Status: {resposta.status_code}")
                return None

            # 4. Cria um buffer em memória para escrever os "pedaços"
            buffer_em_memoria = io.BytesIO()
            
            total_baixado = 0
            # 5. Itera sobre o download em pedaços de 8KB
            for chunk in resposta.iter_content(chunk_size=8192):
                if chunk: # Filtra 'keep-alive' chunks
                    buffer_em_memoria.write(chunk)
                    total_baixado += len(chunk)

            print(f"Download (streaming) concluído. Total: {total_baixado / 1024 / 1024:.2f} MB")
            
            # 6. "Rebobina" o buffer para o início
            buffer_em_memoria.seek(0)
            
            # 7. Lê o buffer em memória com o Pandas
            df = pd.read_csv(
                buffer_em_memoria, 
                encoding='utf-8', 
                sep=';'
            )
            
        print("DataFrame carregado com sucesso.")
        return df

    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão ou streaming: {e}")
        return None
    except Exception as e:
        print(f"Ocorreu um erro inesperado em baixar_em_memoria: {e}")
        return None

def processar_sae(tipo, ano, mes, uf):
    """
    Função principal que o Flask vai chamar.
    Recebe os inputs, baixa, filtra e retorna um buffer de Excel e o nome do arquivo.
    """
    
    # --- 1. Validação de Inputs ---
    print(f"Processando SAE: tipo={tipo}, ano={ano}, mes={mes}, uf={uf}")
    try:
        tipo = str(tipo).strip().upper()
        ano = str(ano).strip()
        mes_int = int(mes) # O Mês precisa ser int para o filtro
        uf = str(uf).strip().upper()
        
        if tipo not in ["IMP", "EXP"]:
            print(f"Erro: Tipo inválido '{tipo}'.")
            return None, None # Retorna falha (buffer, nome)

    except ValueError:
        print(f"Erro: Mês '{mes}' não é um número inteiro válido.")
        return None, None
    except Exception as e:
        print(f"Erro nos parâmetros: {e}")
        return None, None

    # --- 2. Baixar e Carregar o DataFrame ---
    df = baixar_em_memoria(tipo, ano)
    
    if df is None:
        print("Download falhou. Abortando.")
        return None, None

    # --- 3. Filtrar o DataFrame ---
    df_filtrado = None
    try:
        print(f"Filtrando por UF == '{uf}' e Mês == {mes_int}...")
        coluna_uf = 'SG_UF_MUN'
        coluna_mes = 'CO_MES'
        
        if coluna_uf not in df.columns or coluna_mes not in df.columns:
            print("Erro: Colunas esperadas (SG_UF_MUN, CO_MES) não encontradas.")
            return None, None

        condicao_uf = (df[coluna_uf] == uf)
        condicao_mes = (df[coluna_mes] == mes_int) # Usa o int
        
        df_filtrado = df[condicao_uf & condicao_mes]

        if df_filtrado.empty:
            print("Aviso: Nenhum dado encontrado para os filtros.")
            return None, None # Nada para salvar
    
    except Exception as e:
        print(f"Erro durante a filtragem: {e}")
        return None, None

    # --- 4. Salvar em Excel (NA MEMÓRIA) ---
    if not df_filtrado.empty:
        nome_excel = f"SAE_{tipo}_{ano}_{uf}_{mes_int:02d}.xlsx"
        
        try:
            print(f"Salvando arquivo na memória: {nome_excel}")
            
            # Cria um "arquivo" em memória
            output_buffer = io.BytesIO()
            
            # Salva o Excel no buffer
            df_filtrado.to_excel(output_buffer, index=False)
            
            # "Rebobina" o buffer para o início
            output_buffer.seek(0) 
            
            print("Sucesso: Buffer criado.")
            return output_buffer, nome_excel # SUCESSO!
        
        except Exception as e:
            print(f"Erro ao salvar o Excel na memória: {e}")
            return None, None
    
    return None, None # Caso algo falhe

# O 'if __name__ == "__main__":' foi removido
# pois este arquivo agora é uma biblioteca.