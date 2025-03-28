import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext, filters

def load_flow():
    with open('flow.json', 'r', encoding='utf-8') as f:
        return json.load(f)
def get_token():
    with open('token.json', 'r', encoding='utf-8') as f:
        token = json.load(f)
        return token.get("token")

async def start(update: Update, context: CallbackContext):
    flow_data = load_flow()
    context.user_data['responses'] = {}
    context.user_data['current_state'] = 'start'
    context.user_data['flow_data'] = flow_data
    current_state = context.user_data.get('current_state', 'start')
    state_data = flow_data[current_state]
    next_state = state_data.get('next_state')
    if 'variable' in state_data:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=state_data['message'])
    else: 
        await send_options(update,context)
        
#envia as opções

async def send_options(update: Update, context: CallbackContext):
    current_state = context.user_data.get('current_state', 'start')
    flow_data = context.user_data.get('flow_data', {})
    #fluxo para atribuir reescrever na mensagem e capturar variaveis
    if flow_data.get(current_state): 
        if flow_data[current_state].get('variable'):
            state_data = flow_data[current_state].get('variable')
            if state_data:
                if state_data['type'] == 'str':
                    user_input = update.message.text
                    context.user_data['responses'][state_data['name']] = user_input
                    next_state = flow_data[current_state].get('next_state')
                    context.user_data['current_state'] = next_state
                    current_state = context.user_data.get('current_state', 'start')
        responses_list = [{f"#{key}": value} for key, value in context.user_data['responses'].items()]
        for replaces in responses_list:
            for key, value in replaces.items():
                flow_data[current_state]['message'] = flow_data[current_state]['message'].replace(key, value)

    #fluxo para enviar a mensagem
    if current_state in flow_data:
        if not flow_data[current_state].get('variable'):
            state_data = flow_data[current_state]
            next_state = state_data.get('next_state')
            context.user_data['current_state'] = next_state
        else:
            state_data = flow_data[current_state]
        if 'options' in state_data:
            # Criar botões inline
            keyboard = [
                [InlineKeyboardButton(option['text'], callback_data=option['next_state']) for option in state_data['options']]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Verifica se é uma mensagem de texto ou um callback_query
            if update.message:
                return await update.message.reply_text(state_data['message'], reply_markup=reply_markup)
            elif update.callback_query:
                return await update.callback_query.message.reply_text(state_data['message'], reply_markup=reply_markup)
        else:
            if 'variable' in state_data:
                return await context.bot.send_message(chat_id=update.effective_chat.id, text=state_data['message'])
            elif update.message:
                await update.message.reply_text(state_data['message'])
            elif update.callback_query:
                # intertravamento para evitar de que evite chamar funcões anteriores
                if next_state is None:
                    context.user_data['flow_data'] = None
                await update.callback_query.message.reply_text(state_data['message'])
            if next_state == 'end':
                state_data = flow_data[next_state]
            # Avança para o próximo estado
            if next_state:
                context.user_data['current_state'] = next_state
                return await send_options(update, context)  # Chama recursivamente para avançar no fluxo

# Função que lida com o clique do botão
async def chooses(update: Update, context: CallbackContext):
    current_state = context.user_data.get('current_state', 'start')
    flow_data = context.user_data.get('flow_data', {})

    # Armazenar resposta do usuário se for uma mensagem de texto

    # Se a interação for por clique de botão (callback_query)
    if update.callback_query:
        query = update.callback_query
        await query.answer()  # Confirmar recebimento do botão

        next_state = query.data  # Capturar o próximo estado do callback_data
        context.user_data['current_state'] = next_state
        state_data = flow_data[next_state]

        # Criar os botões do próximo estado, se houver
        if 'options' in state_data:
            keyboard = [
                [InlineKeyboardButton(option['text'], callback_data=option['next_state']) for option in state_data['options']]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=state_data['message'], reply_markup=reply_markup)
        else:
            await query.delete_message()
            if 'variable' in state_data:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=state_data['message'])
            else:
                if next_state == 'end':
                    print('delete')
                    await query.message.reply_text(text=state_data['message'])
                    context.user_data['current_state'] = 'end'
                else:
                    context.user_data['current_state'] = next_state
                    await send_options(update, context)

# Função para configurar o bot
def main():
    # Token do bot
    token = get_token()


    # Configuração do Updater e Dispatcher
    application = Application.builder().token(token).build()

    # Comandos e manipuladores de mensagens
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    # Manipulador de mensagem
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, send_options)
    application.add_handler(message_handler)

    # Manipulador de callback de botão
    application.add_handler(CallbackQueryHandler(chooses))

    # Iniciar o bot
    application.run_polling()

if __name__ == '__main__':
    main()
