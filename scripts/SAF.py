import pandas as pd
import tabula
import requests
import os
import re
import unicodedata
from bs4 import BeautifulSoup
import io


# =========================
# DOWNLOAD SAF
# =========================
def extracao(ano, mes):
    base_url_saf = "https://www.sefaz.ba.gov.br/docs/financas-publicas/arrecadacao/"
    link = f"{base_url_saf}arrec{ano}{mes}.pdf"
    nome_arquivo = f"{ano}_{mes}_SAF.pdf"
    print(f"Preparando para baixar de: {link}")
    return link, nome_arquivo


def download(link):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        )
    }

    try:
        with requests.get(link, stream=True, headers=headers, timeout=60) as r:
            r.raise_for_status()
            buffer = io.BytesIO()
            for chunk in r.iter_content(8192):
                if chunk:
                    buffer.write(chunk)
            buffer.seek(0)
            print("Download concluído com sucesso (em memória).")
            return buffer
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar o arquivo: {e}")
        return None


# =========================
# PDF → DATAFRAME
# =========================
def transformar_pdf_em_dataframe(pdf_buffer):
    print("Lendo tabelas do PDF (Tabula)...")
    try:
        dfs = tabula.read_pdf(
            pdf_buffer,
            pages="all",
            multiple_tables=True,
            pandas_options={"header": None},
            silent=True
        )

        if not dfs:
            print("Nenhuma tabela encontrada no PDF.")
            return None

        print(f"{len(dfs)} tabelas extraídas.")
        return dfs
    except Exception as e:
        print(f"Erro ao ler PDF com Tabula: {e}")
        return None


def tratar_tabelas(lista_dfs):
    nomes = [
        "MUNICÍPIOS", "ICMS", "IPVA",
        "ITD", "TAXAS", "NO_MÊS", "TOTAL_ATÉ_O_MÊS"
    ]

    tratadas = []

    for df in lista_dfs:
        df.dropna(axis="columns", how="all", inplace=True)

        while df.shape[1] < 7:
            df[f"col_{df.shape[1]+1}"] = None

        df = df.iloc[:, :7]
        df.columns = nomes
        df = df[df["MUNICÍPIOS"].notna() & (df["MUNICÍPIOS"] != "MUNICÍPIOS")]
        tratadas.append(df)

    return pd.concat(tratadas, ignore_index=True)


def remover_linhas_indesejadas(df):
    termos = [
        "VALOR PRINCIPAL",
        "CORREÇÃO MONETÁRIA",
        "ACRÉS. MORAT. E/OU JUROS",
        "MULTA",
        "RECEITAS PREVIDENCIÁRIAS",
        "TOTAL GERAL",
        "TOTAIS -",
        "ARRECADAÇÃO"
    ]

    for t in termos:
        df = df[~df["MUNICÍPIOS"].astype(str).str.contains(t, case=False, na=False)]

    return df



def processar_df(df):
    colunas_copia = [
        "ICMS_COPIA", "IPVA_COPIA", "ITD_COPIA",
        "TAXAS_COPIA", "NO_MES_COPIA", "TOTAL_MES_COPIA"
    ]

    for c in colunas_copia:
        if c not in df.columns:
            df[c] = pd.NA

    df["ICMS"] = (
        df["ICMS"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    df["ICMS"] = pd.to_numeric(df["ICMS"], errors="coerce")

    mask = df["TOTAL_ATÉ_O_MÊS"].isna()

    df.loc[mask, "ICMS_COPIA"] = df.loc[mask, "ICMS"]
    df.loc[mask, "IPVA_COPIA"] = df.loc[mask, "IPVA"]
    df.loc[mask, "ITD_COPIA"] = df.loc[mask, "ITD"]
    df.loc[mask, "TAXAS_COPIA"] = df.loc[mask, "TAXAS"]
    df.loc[mask, "NO_MES_COPIA"] = df.loc[mask, "NO_MÊS"]
    df.loc[mask, "TOTAL_MES_COPIA"] = df.loc[mask, "NO_MÊS"]

    df.loc[mask, "ICMS"] = df.loc[mask, "ICMS_COPIA"]
    df.loc[mask, "IPVA"] = df.loc[mask, "IPVA_COPIA"]
    df.loc[mask, "ITD"] = df.loc[mask, "ITD_COPIA"]
    df.loc[mask, "TAXAS"] = df.loc[mask, "TAXAS_COPIA"]
    df.loc[mask, "NO_MÊS"] = df.loc[mask, "NO_MES_COPIA"]
    df.loc[mask, "TOTAL_ATÉ_O_MÊS"] = df.loc[mask, "TOTAL_MES_COPIA"]

    return df


# =========================
# IBGE
# =========================
def download_codigos_ibge():
    url = "https://www.ibge.gov.br/explica/codigos-dos-municipios.php#BA"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        head = soup.find("thead", {"id": "BA"})
        table = head.find_parent("table")
        body = table.find("tbody")

        dados = []
        for tr in body.find_all("tr"):
            dados.append([td.text.strip() for td in tr.find_all("td")])

        cols = [th.text.strip() for th in head.find_all("th")]
        df = pd.DataFrame(dados, columns=cols)
        df["Municípios da Bahia"] = df["Municípios da Bahia"].str.upper()

        return df
    except Exception as e:
        print(f"Erro IBGE: {e}")
        return None


# =========================
# FUNÇÃO PRINCIPAL
# =========================
MES_MAP = {
    "1": "jan", "2": "fev", "3": "mar", "4": "abr",
    "5": "mai", "6": "jun", "7": "jul", "8": "ago",
    "9": "set", "10": "out", "11": "nov", "12": "dez"
}


def processar_saf(ano, mes):
    ano = str(ano)[-2:]
    mes = MES_MAP.get(str(mes))

    if not mes:
        return None, None

    url, _ = extracao(ano, mes)
    pdf = download(url)
    if not pdf:
        return None, None

    dfs = transformar_pdf_em_dataframe(pdf)
    if not dfs:
        return None, None

    df = tratar_tabelas(dfs)
    df = remover_linhas_indesejadas(df)
    df = processar_df(df)

    df_ibge = download_codigos_ibge()
    if df_ibge is not None:
        df["key"] = df["MUNICÍPIOS"].str.upper()
        df_ibge["key"] = df_ibge["Municípios da Bahia"].str.upper()
        df = df.merge(df_ibge, how="left", on="key")

    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    return output, f"SAF_{ano}_{mes}.xlsx"
