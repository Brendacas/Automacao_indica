# Automação de Coleta e Tratamento de Dados – Projeto INDICA

Este repositório contém scripts desenvolvidos para a **automação da coleta, tratamento e organização de dados** utilizados no **Projeto de Extensão INDICA (UESC)**, com o objetivo de otimizar processos manuais e apoiar a análise de dados e a tomada de decisão.

## 🎯 Objetivo do Projeto
Automatizar etapas repetitivas de coleta e processamento de dados, garantindo maior **eficiência**, **confiabilidade** e **padronização** das informações utilizadas nos dashboards e análises do projeto.

## 🛠️ Tecnologias Utilizadas
- **Python**
- **Pandas**
- **Requests**
- **BeautifulSoup**
- **Expressões Regulares (Regex)**
- **Manipulação de arquivos (CSV / Excel)**

## ⚙️ Funcionalidades
- Coleta automatizada de dados a partir de fontes externas  
- Tratamento e limpeza de dados (remoção de inconsistências, padronização e ajustes de formato)  
- Organização dos dados para posterior análise  
- Geração de arquivos estruturados para uso em ferramentas de BI (ex.: Power BI)  

## 📂 Estrutura do Repositório
```bash
Automacao_indica/
│── scripts/              # Scripts de automação
│── static/               # View - Estilos e comportamento
│── Templates/            # View - Estrutura
│── app_init.py           # Inicialização da Aplicação
│── Dockerfile            # Configuração do Ambiente de conteinerização
│── requirements.txt      # Dependências do projeto
│── README.md             # Documentação do projeto
│── routes.py             # Controller (gerenciamento de rotas)
│── run.py                # Ponto de Entrada da aplicação
```

## ▶️ Como Executar o Projeto
1. Clone o repositorio
```bash
git clone https://github.com/Brendacas/Automacao_indica.git
```
2. Acesse o diretorio
```bash
cd Automacao_indica
```
3. Instale as dependências
```bash
pip install -r requirements.txt
```
4. Execute o script principal
```bash
python run.py
```
## Resultados
O principal indicador de sucesso do projeto é a redução drástica no tempo necessário para a obtenção dos relatórios econômicos. Segundo medições realizadas em ambiente de produção, esse ciclo manual consumia entre 2 a 3 horas (120 a 180 minutos) para ser concluído integralmente. Com a utilização da ferramenta desenvolvida, o mesmo fluxo, englobando conexão, extração, limpeza (ETL) e geração dos arquivos finais, passou a ser executado em um intervalo de 4 a 15 minutos.

## 👩‍💻 Autora
Brenda Castro

Formanda em Ciência da Computação – UESC

## 📄 Observações
Este projeto foi desenvolvido com fins acadêmicos e extensionistas, podendo ser adaptado para outros contextos que envolvam automação e análise de dados.
