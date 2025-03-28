# Telegram Bot Flow Management - Code Overview

Este markdown descreve o código Python que cria e gerencia um bot no Telegram usando **Python-Telegram-Bot** e um fluxo dinâmico armazenado em arquivos JSON. Abaixo, apresentamos o funcionamento, principais funções e o fluxo lógico do código.

---

## Estrutura do Código

### **1. Importação de Bibliotecas**
```python
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext, filters
```
Essas bibliotecas permitem a criação de mensagens, botões inline e o gerenciamento de eventos e comandos no bot.

---

### **2. Carregamento do Fluxo e Token**
```python
def load_flow():
    with open('flow.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_token():
    with open('token.json', 'r', encoding='utf-8') as f:
        token = json.load(f)
        return token.get("token")
```
- **load_flow**: Carrega o arquivo `flow.json`, que contém o fluxo de diálogo.
- **get_token**: Obtém o token do bot a partir do arquivo `token.json`.

---

### **3. Função `start`: Início do Fluxo**
```python
async def start(update: Update, context: CallbackContext):
    flow_data = load_flow()
    context.user_data['responses'] = {}
    context.user_data['current_state'] = 'start'
    context.user_data['flow_data'] = flow_data
```
Esta função inicializa o fluxo de conversa, armazenando o estado atual, respostas do usuário e o fluxo completo em `context.user_data`.

- **Envio de mensagem ou opções de escolha**:
  ```python
  if 'variable' in state_data:
      await context.bot.send_message(chat_id=update.effective_chat.id, text=state_data['message'])
  else:
      await send_options(update, context)
  ```

---

### **4. Função `send_options`: Gerenciamento do Fluxo**
```python
async def send_options(update: Update, context: CallbackContext):
    current_state = context.user_data.get('current_state', 'start')
    flow_data = context.user_data.get('flow_data', {})
```
Esta função gerencia o envio de mensagens e opções, avançando o estado de acordo com o fluxo definido.

- **Substituição de variáveis dinâmicas**:
  ```python
  responses_list = [{f"#{key}": value} for key, value in context.user_data['responses'].items()]
  for replaces in responses_list:
      for key, value in replaces.items():
          flow_data[current_state]['message'] = flow_data[current_state]['message'].replace(key, value)
  ```

- **Criação de botões inline**:
  ```python
  keyboard = [
      [InlineKeyboardButton(option['text'], callback_data=option['next_state']) for option in state_data['options']]
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)
  ```

---

### **5. Função `chooses`: Lidando com Cliques em Botões**
```python
async def chooses(update: Update, context: CallbackContext):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        next_state = query.data
        context.user_data['current_state'] = next_state
```
Esta função captura interações do usuário ao clicar em botões inline e avança o fluxo para o próximo estado.

- **Manipulação de mensagens e estados finais**:
  ```python
  if next_state == 'end':
      print('delete')
      await query.message.reply_text(text=state_data['message'])
      context.user_data['current_state'] = 'end'
  ```

---

### **6. Função `main`: Configuração e Inicialização do Bot**
```python
def main():
    token = get_token()
    application = Application.builder().token(token).build()
```
- **Configuração de Handlers**:
  ```python
  start_handler = CommandHandler('start', start)
  application.add_handler(start_handler)

  message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, send_options)
  application.add_handler(message_handler)

  application.add_handler(CallbackQueryHandler(chooses))
  ```
  Aqui são configurados os handlers para comandos (`/start`), mensagens de texto e callbacks de botões.

- **Execução do bot**:
  ```python
  application.run_polling()
  ```

---

## Arquivos Utilizados
- **flow.json**: Define o fluxo de diálogo do bot.
- **token.json**: Armazena o token de autenticação do bot.

---

## Resumo do Fluxo
1. O usuário inicia o bot com `/start`.
2. O bot carrega o fluxo do arquivo JSON e envia a primeira mensagem ou opções.
3. As respostas do usuário são armazenadas e as mensagens dinâmicas são geradas.
4. O fluxo avança conforme definido no JSON, até atingir o estado final.

---

## Possíveis Melhorias
- **Tratamento de Erros**: Implementar handlers para capturar e tratar possíveis exceções.
- **Mensagens de Log**: Adicionar mensagens de log para facilitar o debug.
- **Validação de Dados**: Melhorar a validação das entradas do usuário.
- **Personalização do Fluxo**: Tornar o fluxo mais flexível com condições dinâmicas e variáveis opcionais.