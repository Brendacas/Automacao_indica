# Imports do Flask
from flask import (
    render_template, request, jsonify, 
    send_file, url_for, redirect
)
from scripts.SAE import processar_sae
from scripts.SAB import processar_sab
#from scripts.SMT import processar_smt
#from scripts.SAF import processar_saf

from app_init import app  

# --- Rota da Página Principal ---
@app.route('/')
def index():
    return render_template('index.html')

# --- Rota de Processamento do SAE ---
@app.route('/processar-sae', methods=['POST'])
def processar_download():
    
    if request.method == 'POST':
        ano = request.form.get('ano')
        mes = request.form.get('mes')
        uf = request.form.get('uf')
        tipo_opcao = request.form.get('tipo') 

        print(f"--- ROTA /processar-sae CHAMADA ---")
        print(f"Formulário: Ano={ano}, Mês={mes}, UF={uf}, Tipo={tipo_opcao}")

        try:
            buffer, nome_arquivo = processar_sae(
                tipo=tipo_opcao,
                ano=ano,
                mes=mes,
                uf=uf
            )
            
            if buffer is not None:
                print(f"Sucesso. Enviando arquivo: {nome_arquivo}")
                return send_file(
                    buffer,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=nome_arquivo
                )

            else:
                print("Falha no script (buffer is None).")
                return "Erro: Não foi possível gerar o arquivo. Verifique os filtros."
                
        except Exception as e:
            print(f"Erro catastrófico na rota: {e}")
            return "Erro interno do servidor."

    return redirect(url_for('index'))

# @app.route('/processar-saf', methods=['POST'])
# def processar_saf_route():
    
#     if request.method == 'POST':
#         ano = request.form.get('ano')
#         mes = request.form.get('mes')

#         print("--- ROTA /processar-saf CHAMADA ---")
#         print(f"Formulário: Ano={ano}, Mês={mes}")

#         try:
#             buffer, nome_arquivo = processar_saf(
#                 ano_full=ano,
#                 mes_num=mes
#             )
            
#             if buffer is not None:
#                 print(f"Sucesso. Enviando arquivo: {nome_arquivo}")
#                 response = send_file(
#                     buffer,
#                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
#                     as_attachment=True,
#                     download_name=nome_arquivo
#                 )
#                 response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
#                 return response
#             else:
#                 print("Falha no script SAF (buffer is None).")
#                 return "Erro: Não foi possível gerar o arquivo. Verifique os filtros, os logs e se o Java está instalado.", 500
                
#         except Exception as e:
#             print(f"Erro catastrófico na rota SAF: {e}")
#             return "Erro interno do servidor.", 500

#     return redirect(url_for('index'))

@app.route('/processar-sab', methods=['POST'])
def processar_sab_route():
    
    if request.method == 'POST':
        
        #Captura os dados do formulário SAB
        ano = request.form.get('ano')
        mes = request.form.get('mes')

        print("--- ROTA /processar-sab CHAMADA ---")
        print(f"Formulário: Ano={ano}, Mês={mes}")

        try:
            # Chama o script SAB
            buffer, nome_arquivo = processar_sab(
                ano=ano,
                mes=mes
            )
            
            #Verifica o resultado e envia o arquivo
            if buffer is not None:
                print(f"Sucesso. Enviando arquivo: {nome_arquivo}")
                
                response = send_file(
                    buffer,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=nome_arquivo
                )
                response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
                return response
            else:
                print("Falha no script SAB (buffer is None).")
                # Retorna um status de erro que o 'fetch' pode pegar
                return "Erro: Não foi possível gerar o arquivo. Verifique os filtros ou os logs.", 500
                
        except Exception as e:
            print(f"Erro catastrófico na rota SAB: {e}")
            return "Erro interno do servidor.", 500

    return redirect(url_for('index'))

# @app.route('/processar-smt', methods=['POST'])
# def processar_smt_route():
    
#     if request.method == 'POST':
#         uf = request.form.get('uf')
#         ano = request.form.get('ano')
#         mes = request.form.get('mes')

#         print("--- ROTA /processar-smt CHAMADA ---")
#         print(f"Formulário: UF={uf}, Ano={ano}, Mês={mes}")

#         try:
#             #Chama o script SMT 
#             buffer, nome_arquivo = processar_smt(
#                 uf=uf,
#                 ano=ano,
#                 mes_num=mes
#             )
            
#             if buffer is not None:
#                 print(f"Sucesso. Enviando arquivo: {nome_arquivo}")
#                 response = send_file(
#                     buffer,
#                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
#                     as_attachment=True,
#                     download_name=nome_arquivo
#                 )
#                 response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
#                 return response
#             else:
#                 print("Falha no script SMT (buffer is None).")
#                 return "Erro: Não foi possível gerar o arquivo. Verifique os filtros ou os logs.", 500
                
#         except Exception as e:
#             print(f"Erro catastrófico na rota SMT: {e}")
#             return "Erro interno do servidor.", 500

#     return redirect(url_for('index'))