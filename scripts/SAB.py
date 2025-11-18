import requests
import zipfile
import os
import pandas as pd
import io


def baixar_e_processar_zip_em_memoria(ano, mes):
    """
    Baixa o ZIP, extrai o CSV e processa o DataFrame (filtrando para BA), 
    tudo em memória.
    """
    mes_str = f"{mes:02d}"
    ano_SAB = f"{ano}{mes_str}"
    nome_zip = f"{ano_SAB}_ESTBAN.csv.zip"
    url_base = "https://www.bcb.gov.br/content/estatisticas/estatistica_bancaria_estban/municipio/"
    link_download = f"{url_base}{nome_zip}"

    print(f"Baixando e processando em memória: {link_download}...")
    
    try:
        resposta = requests.get(link_download, timeout=60) 
        
        if resposta.status_code != 200:
            print(f"Erro: Falha ao baixar o arquivo. Status: {resposta.status_code}")
            return None

        print("Download concluído. Abrindo ZIP em memória...")
        with zipfile.ZipFile(io.BytesIO(resposta.content), "r") as zip_ref:
            nome_csv = None
            for nome in zip_ref.namelist():
                if nome.lower().endswith('.csv'):
                    nome_csv = nome
                    break
            
            if not nome_csv:
                print("Erro: Nenhum arquivo .csv encontrado dentro do ZIP.")
                return None

            print(f"Encontrado {nome_csv}. Lendo CSV...")
            with zip_ref.open(nome_csv) as arquivo_csv_em_memoria:
                df = pd.read_csv(
                    arquivo_csv_em_memoria, 
                    encoding='latin-1', 
                    skiprows=2, 
                    sep=';'
                )

        print("Processando DataFrame...")
        df.columns = df.columns.str.strip()
        
        if 'UF' not in df.columns:
            print("Erro: Coluna 'UF' não encontrada.")
            return None
        

        df_filtrado = df[df['UF'] == 'BA']
        return df_filtrado

    except Exception as e:
        print(f"Ocorreu um erro inesperado em baixar_e_processar_zip_em_memoria: {e}")
        return None


def processar_sab(ano, mes):
    """
    Função principal que o Flask vai chamar.
    Recebe ano/mês, baixa, filtra (para BA) e retorna um buffer de Excel.
    """
    
    # --- 1. Validação de Inputs ---
    print(f"Processando SAB: ano={ano}, mes={mes}")
    try:
        ano_int = int(ano)
        mes_int = int(mes)
    except (ValueError, TypeError):
        print(f"Erro: Ano '{ano}' ou Mês '{mes}' não são números inteiros válidos.")
        return None, None # Retorna (buffer, nome)

    # --- 2. Baixar e Processar ---
    df_final = baixar_e_processar_zip_em_memoria(ano_int, mes_int)
    
    # --- 3. Salvar em Excel (NA MEMÓRIA) ---
    if df_final is not None and not df_final.empty:
        id_arquivo = f"{ano_int}{mes_int:02d}"
        nome_excel = f"ESTBAN_BA_{id_arquivo}.xlsx"
        
        try:
            print(f"Salvando arquivo na memória: {nome_excel}")
            output_buffer = io.BytesIO()
            df_final.to_excel(output_buffer, index=False)
            output_buffer.seek(0)
            
            print("Sucesso: Buffer SAB criado.")
            return output_buffer, nome_excel
        
        except Exception as e:
            print(f"Erro ao salvar o Excel na memória: {e}")
            return None, None
    
    elif df_final is not None:
        print("Processamento SAB concluído, mas sem dados para salvar.")
        return None, None
    else:
        print("Processamento SAB falhou (download/processamento).")
        return None, None