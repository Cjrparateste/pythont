
    <script>
        // Função para lidar com o clique do botão de acesso
        document.querySelector('.access-btn').addEventListener('click', async function() {
            let apiId = document.querySelector('input[placeholder="API ID"]').value;
            let apiHash = document.querySelector('input[placeholder="API HASH"]').value;
            let phoneNumber = document.querySelector('input[placeholder="Número de Telefone"]').value;
    
            // Verificação dos campos obrigatórios
            if (!apiId || !apiHash || !phoneNumber) {
                alert('Por favor, preencha todos os campos corretamente.');
                return;
            }
    
            try {
                console.log("Enviando código para:", phoneNumber);
                // Enviar solicitação para o backend enviar o código de verificação
                let sendCodeResponse = await eel.send_code(apiId, apiHash, phoneNumber)();
                console.log("Resposta do backend ao enviar código:", sendCodeResponse);
    
                alert(sendCodeResponse.message);  // Notificação ao usuário sobre o status do envio do código
    
                // Verifica se o código foi enviado com sucesso
                if (sendCodeResponse.status) {
                    let phoneCodeHash = sendCodeResponse.phone_code_hash;  // Obter o hash do código
                    console.log("Código de verificação enviado, hash recebido:", phoneCodeHash);
    
                    let code = prompt(`Digite o código de verificação enviado para ${phoneNumber}:`);
                    if (code) {
                        console.log("Autenticando com código:", code);
                        // Autenticar o código fornecido pelo usuário
                        let authResponse = await eel.authenticate(apiId, apiHash, phoneNumber, code, phoneCodeHash)();
                        console.log("Resposta da autenticação:", authResponse);
    
                        alert(authResponse.message);  // Notificação ao usuário sobre o status da autenticação
                    } else {
                        alert("Código de verificação não fornecido.");
                    }
                }
            } catch (error) {
                console.error("Erro ao enviar o código ou autenticar:", error);
                alert("Ocorreu um erro durante o processo de autenticação. Por favor, tente novamente.");
            }
        });
    
        // Função opcional para lidar com eventos de teclado (pressionar Enter para enviar)
        document.querySelectorAll('input').forEach(input => {
            input.addEventListener('keypress', function(event) {
                if (event.key === "Enter") {
                    document.querySelector('.access-btn').click();
                }
            });
        });
    </script>
