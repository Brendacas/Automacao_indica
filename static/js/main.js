// Espera o HTML inteiro ser carregado antes de rodar o script
document.addEventListener('DOMContentLoaded', function() {

    // --- CÓDIGO DO MENU EXPANSÍVEL ---
    var botoes = document.getElementsByClassName("botao-expansivel");
    for (var i = 0; i < botoes.length; i++) {
        botoes[i].addEventListener("click", function() {
            // Pega o próximo elemento (o div .conteudo)
            var conteudo = this.nextElementSibling;
            
            // Alterna a exibição (mostra ou esconde)
            if (conteudo.style.display === "block") {
                conteudo.style.display = "none";
            } else {
                conteudo.style.display = "block";
            }
        });
    }

    // Pega o spinner 
    const spinner = document.getElementById('loading-spinner');

    // --- LÓGICA DO FORMULÁRIO 1 (SAE) ---
    // Procura pelo formulário com id "form-sae"
    const formSAE = document.getElementById('form-sae');
    if (formSAE) { // Verifica se o formulário existe
        formSAE.addEventListener('submit', function(event) {
            // Chama a função de envio, passando a URL correta
            handleFormSubmit(event, formSAE, '/processar-sae');
        });
    }
    const formSAF = document.getElementById('form-saf');
    if (formSAF) {
        formSAF.addEventListener('submit', function(event) {
            handleFormSubmit(event, formSAF, '/processar-saf');
        });
    }

    // --- LÓGICA DO FORMULÁRIO 2 (SAB) ---
    // Procura pelo formulário com id "form-sab"
    const formSAB = document.getElementById('form-sab');
    if (formSAB) { // Verifica se o formulário existe
        formSAB.addEventListener('submit', function(event) {
            // Chama a função de envio, passando a URL correta
            handleFormSubmit(event, formSAB, '/processar-sab');
        });
    }
    // --- LÓGICA DO FORMULÁRIO 3 (SMT) ---
    // Procura pelo formulário com id "form-smt"
    const formSMT = document.getElementById('form-smt');
    if (formSMT) {
        formSMT.addEventListener('submit', function(event) {
            // Chama a função  de envio
            handleFormSubmit(event, formSMT, '/processar-smt');
        });
    }

    // --- FUNÇÃO PARA LIDAR COM O FETCH E O SPINNER ---
    // Esta função é chamada por qualquer um dos formulários
    function handleFormSubmit(event, formElement, url) {
        
        // Impede o envio HTML padrão (para a página não travar)
        event.preventDefault();

        // Mostra o spinner
        if (spinner) {
            spinner.style.display = 'flex';
        }

        // Coleta os dados do formulário que foi enviado
        const formData = new FormData(formElement);

        // Envia os dados com 'fetch' para a URL especificada
        fetch(url, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            // Se a resposta do servidor não for "OK" (ex: Erro 500)
            if (!response.ok) {
                // Tenta ler a mensagem de erro que enviamos do Flask
                return response.text().then(text => {
                    // Lança um erro com a mensagem do servidor
                    throw new Error(text || 'Erro ' + response.status);
                });
            }
            
            // Se deu "OK", processa o arquivo para download
            const header = response.headers.get('Content-Disposition');
            if (!header) {
                throw new Error('Cabeçalho Content-Disposition não encontrado.');
            }
            
            const parts = header.split(';');
            const filenamePart = parts.find(part => part.trim().startsWith('filename='));
            if (!filenamePart) {
                throw new Error('Nome do arquivo não encontrado no cabeçalho.');
            }

            // Limpa o nome do arquivo
            const filename = filenamePart.split('=')[1].replace(/"/g, '');
            // Retorna o arquivo (blob) e o nome dele
            return response.blob().then(blob => ({ blob, filename }));
        })
        .then(({ blob, filename }) => {
            // 5Cria um link de download em memória
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', filename); // Define o nome do arquivo
            document.body.appendChild(link);
            
            // "Clica" no link invisível para iniciar o download
            link.click();
            
            // Limpa o link da memória
            link.parentNode.removeChild(link);
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            // Se qualquer etapa falhar, mostra um alerta para o usuário
            console.error('Erro no fetch:', error);
            alert('Falha ao gerar o download: ' + error.message);
        })
        .finally(() => {
            // SEMPRE esconde o spinner no final (sucesso ou erro)
            if (spinner) {
                spinner.style.display = 'none';
            }
        });
    }
});