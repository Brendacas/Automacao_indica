import pandas as pd
import tabula 
import requests
import os
import re
import unicodedata
from bs4 import BeautifulSoup
import io

def extracao(ano, mes):
    """
    Monta a URL de download e o nome do arquivo.
    """
    base_url_saf = "https://www.sefaz.ba.gov.br/docs/financas-publicas/arrecadacao/"
    link = f"{base_url_saf}arrec{ano}{mes}.pdf"
    nome_arquivo = f"{ano}_{mes}_SAF.pdf"
    print(f"Preparando para baixar de: {link}")
    return link, nome_arquivo

def download(link):
    """
    Baixa o arquivo em memória e retorna um objeto BytesIO.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    }
    
    try:
        with requests.get(link, stream=True, headers=headers, timeout=60) as resposta:
            resposta.raise_for_status()
            
            # Cria um "arquivo" em memória
            pdf_em_memoria = io.BytesIO()
            
            # Escreve os pedaços (chunks) do download na memória
            for chunk in resposta.iter_content(chunk_size=8192):
                if chunk:
                    pdf_em_memoria.write(chunk)
            
            print(f"Download concluído com sucesso (em memória).")
            
            # "Rebobina" o arquivo em memória para o início,
            # para que outras bibliotecas possam lê-lo
            pdf_em_memoria.seek(0)
            
            return pdf_em_memoria
            
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar o arquivo: {e}")
        return None

# ---  FUNÇÕES PARA PROCESSAR PDF SAF ---
def transformar_pdf_em_dataframe(pdf_buffer):
    """
    Lê tabelas do PDF (em memória) usando Tabula.
    """
    print(f"Lendo tabelas do PDF em memória (usando Tabula)...")
    try:
        # Tabula pode ler diretamente do buffer BytesIO
        lista_de_dataframes = tabula.read_pdf(
            pdf_buffer, 
            pages='all', 
            multiple_tables=True, 
            pandas_options={'header': None}  
        )
        
        if not lista_de_dataframes or len(lista_de_dataframes) == 0:
            print("Erro: Nenhuma tabela encontrada no PDF.")
            return None
        else:
            print(f"{len(lista_de_dataframes)} tabelas foram extraídas do PDF.")
            return lista_de_dataframes
    except Exception as e:
        print(f"Erro ao ler o PDF com Tabula: {e}")
        print("Verifique se o Java (JDK) está instalado e acessível no PATH do sistema.")
        return None

def tratar_tabelas(lista_de_dataframes):
    """
    Limpa e concatena as tabelas extraídas do PDF.
    """
    nomes_colunas = ['MUNICÍPIOS', 'ICMS', 'IPVA', 'ITD', 'TAXAS', 'NO_MÊS', 'TOTAL_ATÉ_O_MÊS']
    tabelas_tratadas = []

    for i, df in enumerate(lista_de_dataframes, start=1):
        print(f"\n--- Processando tabela {i} ---")
        df.dropna(axis='columns', how='all', inplace=True)
        
        # Garante que a tabela tenha 7 colunas
        while df.shape[1] < 7:
            df[f'col_{df.shape[1]+1}'] = None
        
        # Seleciona apenas as 7 primeiras colunas
        df = df.iloc[:, :7]
        df.columns = nomes_colunas
        
        # Remove linhas de cabeçalho repetidas ou vazias
        df = df[df['MUNICÍPIOS'].notna() & (df['MUNICÍPIOS'] != 'MUNICÍPIOS')].copy()
        tabelas_tratadas.append(df)
        print(f"Tabela {i} processada com {df.shape[0]} linhas válidas.")

    df_final = pd.concat(tabelas_tratadas, ignore_index=True)
    print(f"\nShape final após concatenação: {df_final.shape}")
    return df_final

def remover_linhas_indesejadas(df_final):
    """
    Remove linhas de totais e subtotais.
    """
    linhas_remover = ['VALOR PRINCIPAL','CORREÇÃO MONETÁRIA','ACRÉS. MORAT. E/OU JUROS', 'MULTA', 
                      'RECEITAS PREVIDENCIÁRIAS', 'TOTAL GERAL' ]
    df_final = df_final[~df_final.iloc[:, 0].isin(linhas_remover)]
    for termo in ['MULTA','CORREÇÃO MONETÁRIA','VALOR PRINCIPAL','ACRÉS. MORAT. E/OU JUROS','Arrecadação','TOTAIS -']:
        df_final = df_final[~df_final['MUNICÍPIOS'].astype(str).str.contains(termo, case=False, na=False)]
  
    return df_final

def separar_todos_numeros(texto):
    """
    Função 'apply' para separar o nome do município do valor de ICMS
    que às vezes vêm na mesma célula.
    """
    texto = str(texto)
    numeros = re.findall(r'[\d.,]+', texto)
    if numeros:
        numero_str = ''.join(numeros)
        nome = re.sub(r'[\d.,]+', '', texto).strip()
        try:
            numero_float = float(numero_str.replace('.', '').replace(',', '.'))
            return pd.Series([nome, numero_float])
        except ValueError:
            return pd.Series([texto, None]) 
    else:
        return pd.Series([texto, None])

def processar_df(df_final):
    """
    Corrigir colunas que foram deslocadas durante a extração do PDF,
    onde valores de ICMS podem ter "vazado" para a coluna MUNICÍPIOS.
    """
    df_final['IPVA_COPIA'] = ''
    df_final['ITD_COPIA'] = ''
    df_final['TAXAS_COPIA'] = ''
    df_final['NO_MES_COPIA'] = ''
    df_final['TOTAL_MES_COPIA'] = ''

    df_final['ICMS'] = df_final['ICMS'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)

    # Identifica linhas onde as colunas estão deslocadas (TOTAL_ATÉ_O_MÊS está nulo)
    mask_deslocado = df_final['TOTAL_ATÉ_O_MÊS'].isna()

    # Move os dados para as colunas de cópia
    df_final.loc[mask_deslocado, 'IPVA_COPIA'] = df_final.loc[mask_deslocado, 'ICMS']
    df_final.loc[mask_deslocado, 'ITD_COPIA'] = df_final.loc[mask_deslocado, 'IPVA']
    df_final.loc[mask_deslocado, 'TAXAS_COPIA'] = df_final.loc[mask_deslocado, 'ITD']
    df_final.loc[mask_deslocado, 'NO_MES_COPIA'] = df_final.loc[mask_deslocado, 'TAXAS']
    df_final.loc[mask_deslocado, 'TOTAL_MES_COPIA'] = df_final.loc[mask_deslocado, 'NO_MÊS']

    # Move os dados das colunas de cópia para as colunas corretas
    df_final.loc[mask_deslocado, 'ICMS'] = df_final.loc[mask_deslocado, 'ICMS_COPIA']
    df_final.loc[mask_deslocado, 'IPVA'] = df_final.loc[mask_deslocado, 'IPVA_COPIA']
    df_final.loc[mask_deslocado, 'ITD'] = df_final.loc[mask_deslocado, 'ITD_COPIA']
    df_final.loc[mask_deslocado, 'TAXAS'] = df_final.loc[mask_deslocado, 'TAXAS_COPIA']
    df_final.loc[mask_deslocado, 'NO_MÊS'] = df_final.loc[mask_deslocado, 'NO_MES_COPIA']
    df_final.loc[mask_deslocado, 'TOTAL_ATÉ_O_MÊS'] = df_final.loc[mask_deslocado, 'TOTAL_MES_COPIA']

    # Lógica adicional para linhas onde 'IPVA' está nulo
    mask_ipva_nulo = df_final['IPVA'].isna()
    df_final.loc[mask_ipva_nulo, 'IPVA_COPIA'] = df_final.loc[mask_ipva_nulo, 'ICMS']
    mask_icms_ipva_iguais = df_final['ICMS'] == df_final['IPVA_COPIA']
    df_final.loc[mask_icms_ipva_iguais, 'ICMS'] = pd.NA

    df_final.loc[df_final['ICMS'].isna(), 'ICMS'] = df_final.loc[df_final['ICMS'].isna(), 'ICMS_COPIA']
    df_final.loc[df_final['IPVA'].isna(), 'IPVA'] = df_final.loc[df_final['IPVA'].isna(), 'IPVA_COPIA']
    
    return df_final


# ---  FUNÇÕES IBGE ---
def download_codigos_ibge():
    """
    Faz web scraping da página do IBGE para pegar os códigos
    dos municípios da Bahia.
    """
    print("Baixando códigos de municípios do IBGE (BA)...")
    url = "https://www.ibge.gov.br/explica/codigos-dos-municipios.php#BA"
    try:
        r = requests.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Encontra a tabela específica da Bahia
        cabecalho = soup.find('thead', {'id': 'BA'})
        if not cabecalho:
            print("Erro: Cabeçalho 'BA' não encontrado na página do IBGE.")
            return None
            
        tabela = cabecalho.find_parent('table')
        corpo = tabela.find('tbody') if tabela else None
        
        dados = []
        if corpo:
            for tr in corpo.find_all('tr'):
                tds = tr.find_all('td')
                if tds:
                    dados.append([td.text.strip() for td in tds])
        
        colunas = [th.text.strip() for th in cabecalho.find_all('th')]
        df_ibge = pd.DataFrame(dados, columns=colunas)
        
        # Prepara a coluna para o merge
        df_ibge['Municípios da Bahia'] = df_ibge['Municípios da Bahia'].str.upper()
        print("Códigos do IBGE baixados com sucesso.")
        return df_ibge
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a página do IBGE: {e}")
        return None

def limpar_texto(texto):
    """
    Normaliza o texto: remove acentos e converte para maiúsculas
    para facilitar o merge.
    """
    if not isinstance(texto, str):
        return texto
    # Remove acentos
    texto_normalizado = unicodedata.normalize('NFD', texto)
    texto_sem_acentos = texto_normalizado.encode('ascii', 'ignore').decode('utf-8')
    texto_com_espaco = texto_sem_acentos.replace("'", " ")
    
    # 4. Remove qualquer outra pontuação que tenha sobrado
    # (Mantém letras, números e espaços)
    texto_sem_pontuacao = re.sub(r'[^\w\s]', '', texto_com_espaco)
    
    # 5. Normaliza espaços:
    # Remove múltiplos espaços e espaços no início/fim
    texto_final = re.sub(r'\s+', ' ', texto_sem_pontuacao).strip()
    
    return texto_final

def merge_com_ibge(df_saf, df_ibge):
    """
    Faz o merge dos dados da SEFAZ com os códigos do IBGE.
    """
    print("Iniciando merge com dados do IBGE...")
    
    # Cria chaves de merge normalizadas (sem acento, maiúsculas)
    df_saf['chave_merge'] = df_saf['MUNICÍPIOS'].apply(limpar_texto).str.upper()
    df_ibge['chave_merge'] = df_ibge['Municípios da Bahia'].apply(limpar_texto).str.upper()
    
    df_final = pd.merge(df_saf, df_ibge, how='left', on='chave_merge')
    
    print("Merge concluído.")
    return df_final

def tratamento_final(df_final):
    """
    Limpa as colunas temporárias usadas no processo.
    """
    # Remove colunas indesejadas
    colunas_para_remover = [
        'ICMS_COPIA', 'IPVA_COPIA', 'ITD_COPIA', 'TAXAS_COPIA', 'NO_MES_COPIA', 'TOTAL_MES_COPIA',
        'chave_merge', 'Municípios da Bahia'
    ]
    df_final = df_final.drop(columns=colunas_para_remover, axis=1, errors='ignore')
    
    df_final.rename(columns={'Códigos': 'Código_IBGE'}, inplace=True)
    df_final = df_final.dropna(subset=['Código_IBGE'])
    
    return df_final

# NOVO MAPA: Converte o mês "1" (do formulário) para "jan" (do script)
MES_MAP_NUM_TO_STR = {
    '1': 'jan', '2': 'fev', '3': 'mar', '4': 'abr', '5': 'mai', '6': 'jun',
    '7': 'jul', '8': 'ago', '9': 'set', '10': 'out', '11': 'nov', '12': 'dez'
}

# --- FUNÇÃO PRINCIPAL (Chamada pelo Flask) ---
# Substitui a 'automacao_saf()'
def processar_saf(ano_full, mes_num):
    """
    processo de download, extração e tratamento.
    """
    print("\n--- Iniciando Automação SAF (SEFAZ-BA) ---")
    
    # --- 1. Conversão de Inputs ---
    try:
        ano_str = str(ano_full).strip()
        mes_num_str = str(mes_num).strip()
        
        # Converte "2024" para "24"
        if len(ano_str) == 4:
            ano_param = ano_str[-2:]
        else:
            ano_param = ano_str # Assume que já está "24"

        # Converte "1" para "jan"
        mes_param = MES_MAP_NUM_TO_STR.get(mes_num_str)
        if not mes_param:
            print(f"Erro: Mês inválido '{mes_num_str}'")
            return None, None
        
        print(f"Processando para: Ano={ano_param}, Mês={mes_param}")

    except Exception as e:
        print(f"Erro na conversão de inputs: {e}")
        return None, None

    # --- 2. Lógica Principal (copiada de automacao_saf) ---
    link_info = extracao(ano_param, mes_param) # Corrigido
    url, nome_arquivo_pdf = link_info # Corrigido
    
    pdf_em_memoria = download(url)
    
    if not pdf_em_memoria:
        print("Download falhou. Abortando.")
        return None, None
        
    lista_de_dataframes = transformar_pdf_em_dataframe(pdf_em_memoria)
    
    if not lista_de_dataframes:
        print("Extração do PDF falhou. Abortando.")
        return None, None
        
    df_final = tratar_tabelas(lista_de_dataframes)
    df_final = remover_linhas_indesejadas(df_final)
    
    try:
        df_final[['MUNICÍPIOS', 'ICMS_COPIA']] = df_final['MUNICÍPIOS'].apply(separar_todos_numeros)
    except Exception as e:
        print(f"Aviso: Falha ao aplicar 'separar_todos_numeros'. {e}")
        df_final['ICMS_COPIA'] = pd.NA 
        
    df_final = processar_df(df_final)

    # --- 3. IBGE e merge ---
    df_ibge = download_codigos_ibge()
    if df_ibge is None:
        print("Não foi possível baixar os dados do IBGE.")
    else:
        df_final = merge_com_ibge(df_final, df_ibge)
    
    df_final_completo = tratamento_final(df_final)

    print("\n--- Processamento concluído ---")
    
    # --- 4. Salvar em Memória ---
    try:
        nome_excel = f"SAF_{ano_param}_{mes_param}.xlsx"
        output_buffer = io.BytesIO()
        df_final_completo.to_excel(output_buffer, index=False)
        output_buffer.seek(0)
        print(f"Buffer criado com sucesso: {nome_excel}")
        return output_buffer, nome_excel
    except Exception as e:
        print(f"Erro ao salvar Excel na memória: {e}")
        return None, None