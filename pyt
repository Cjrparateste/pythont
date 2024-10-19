import os
import json
import eel
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeExpiredError, PhoneCodeInvalidError
from telethon.sessions import StringSession
import asyncio

class TelegramAuth:
    def __init__(self, api_id, api_hash, phone_number, session=None):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.session = session
        self.client = TelegramClient(
            StringSession(self.session), self.api_id, self.api_hash
        ) if self.session else TelegramClient(StringSession(), self.api_id, self.api_hash)

    async def connect(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            return {"status": False, "message": "Usuário não autorizado"}
        return {"status": True, "message": "Conectado com sucesso"}

    async def send_code(self):
        try:
            await self.client.connect()
            # Log de envio do código
            print(f"Enviando código de verificação para: {self.phone_number}")
            result = await self.client.send_code_request(self.phone_number)
            return {
                "status": True, 
                "message": "Código de verificação enviado com sucesso.",
                "phone_code_hash": result.phone_code_hash
            }
        except Exception as e:
            # Log de erro
            print(f"Erro ao enviar código: {str(e)}")
            return {"status": False, "message": str(e)}
        finally:
            await self.client.disconnect()

    async def authenticate_code(self, code, phone_code_hash, password=None):
        try:
            await self.client.connect()

            # Verifica se o usuário já está autorizado
            if await self.client.is_user_authorized():
                return {"status": True, "message": "Usuário já está autenticado."}

            # Tenta autenticar com o código fornecido
            result = await self.attempt_login(code, phone_code_hash, password)

            if result["status"]:
                # Salva a sessão se o login for bem-sucedido
                self.session = self.client.session.save()
                return {"status": True, "message": "Autenticado com sucesso."}
            else:
                return result

        except Exception as e:
            print(f"Erro inesperado durante a autenticação: {str(e)}")
            return {"status": False, "message": f"Erro inesperado: {str(e)}"}

    async def attempt_login(self, code, phone_code_hash, password):
        try:
            # Tenta autenticar usando o código e phone_code_hash
            print(f"Tentando autenticar o número {self.phone_number} com o código: {code} e com a Hash: {phone_code_hash}")
            await self.client.sign_in(phone=self.phone_number, code=code, phone_code_hash=phone_code_hash)
            return {"status": True, "message": "Código aceito, autenticação concluída."}

        except SessionPasswordNeededError:
            if password:
                return await self.handle_2fa(password)
            else:
                print("Senha de dois fatores necessária")
                return {"status": False, "message": "Senha de dois fatores necessária."}

        except PhoneCodeExpiredError:
            print("Erro: O código de verificação expirou.")
            return {"status": False, "message": "O código de verificação expirou. Solicite um novo código."}

        except PhoneCodeInvalidError:
            print("Erro: O código de verificação está incorreto.")
            return {"status": False, "message": "O código de verificação está incorreto."}

        except Exception as e:
            print(f"Erro inesperado ao tentar autenticar: {str(e)}")
            return {"status": False, "message": f"Erro inesperado ao tentar autenticar: {str(e)}"}

    async def handle_2fa(self, password):
        try:
            # Tenta autenticar usando a senha de dois fatores
            print(f"Autenticando com 2FA para o número: {self.phone_number}")
            await self.client.sign_in(password=password)
            return {"status": True, "message": "Autenticado com sucesso com dois fatores."}
            
        except Exception as e:
            print(f"Erro durante a autenticação 2FA: {str(e)}")
            return {"status": False, "message": f"Erro inesperado na autenticação de dois fatores: {str(e)}"}

    async def save_session(self):
        try:
            account_dir = f'backend/accounts/{self.phone_number}'
            os.makedirs(account_dir, exist_ok=True)
            session_file_name = f'{self.phone_number}.session'
            session_file_path = os.path.join(account_dir, session_file_name)

            # Salvando a sessão
            print(f"Salvando a sessão para o número {self.phone_number}")
            with open(session_file_path, 'w') as f:
                f.write(self.client.session.save())

            # Criado arquivo JSON com os dados da conta
            json_file_path = os.path.join(account_dir, 'config.json')
            config_data = {
                'API_HASH': self.api_hash,
                'API_ID': self.api_id,
                'PHONE_NUMBER': self.phone_number,
                'SESSION_FILE_PATH': session_file_path
            }

            with open(json_file_path, 'w') as json_file:
                json.dump(config_data, json_file, indent=4)
            
            return {"status": True, "message": f"Conta {self.phone_number} autenticada com sucesso e sessão salva."}

        except Exception as e:
            print(f"Erro ao salvar sessão: {str(e)}")
            return {"status": False, "message": str(e)}
        finally:
            await self.client.disconnect()

# Função para rodar tarefas assíncronas no loop correto
def run_async_function(async_func, *args, **kwargs):
    try:
        loop = asyncio.get_event_loop()  # Pega o loop existente
    except RuntimeError:
        loop = asyncio.new_event_loop()  # Cria um novo loop se necessário
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(async_func(*args, **kwargs))

# Expor funções para o frontend via Eel
@eel.expose
def send_code(api_id, api_hash, phone_number):
    auth = TelegramAuth(api_id, api_hash, phone_number)
    print(f"Enviando código de verificação para o número: {phone_number}")  # Log para depuração
    response = run_async_function(auth.send_code)
    print(f"Resposta do envio do código: {response}")  # Log da resposta
    return response

@eel.expose
def authenticate(api_id, api_hash, phone_number, code, phone_code_hash, password=None):
    print(f"Tentando autenticar o número {phone_number} com o código: {code}")  # Log para depuração
    auth = TelegramAuth(api_id, api_hash, phone_number)
    response = run_async_function(auth.authenticate_code, code, phone_code_hash, password)
    
    # Log da resposta da autenticação
    print(f"Resposta da autenticação: {response}")
    return response
