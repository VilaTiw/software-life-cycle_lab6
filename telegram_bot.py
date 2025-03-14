from __future__ import annotations
import json
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from EmotionAnalysis.sentiment_analysis.sentiment_analysis import *
from EmotionAnalysis.toxicity_analysis.toxicity_analysis import *
from abc import ABC, abstractmethod
from Data.db_connector import MongoDB

sentiment_flag = False
isActive_flag = True

responses = {}
channel_posts = []
group_posts = {}

TOKEN: Final = "6748414644:AAF7nahcptbIaTTg8xjik1zXxfaHkdniD4o"
BOT_USERNAME: Final = "@classification_text_bot"

class MessageMemento:
    def __init__(self, message_text):
        #self.message_id = message_id
        self.message_text = message_text

class CareTaker:
    def __init__(self):
        self.__mementos = []
        self.index = 1

    def add_memento(self, memento: MessageMemento):
        self.__mementos.append(memento)

    def get_memento(self, index):
        if self.__mementos:
            i = len(self.__mementos) - index
            print(len(self.__mementos))
            print(index)
            if i > 0:
                return self.__mementos[i], index
            elif i == 0:
                return self.__mementos[i], index
            else:
                print('Incorrect index: ', i)
                return None, 0
        else:
            return None

class TelegramBot:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, token, bot_username, command_invoker, mongo):
        self.token = token
        self.bot_username = bot_username
        self.app = None
        self.mongo = mongo
        self.command_invoker = command_invoker
        self.observers = []
        self.__caretaker = CareTaker()
        self.index = 1

    def create_memento(self, message_text):
        return MessageMemento(message_text)

    def save_message(self, message_text):
        memento = self.create_memento(message_text)
        self.__caretaker.add_memento(memento)
        self.index = 1

    def restore_message(self):
        memento, self.index = self.__caretaker.get_memento(self.index)
        print('restore', self.index)
        if self.index > 0:
            self.index = self.index + 1
        elif self.index == 0:
            self.index = 1
        elif self.index < 0:
            self.index = 1

        if memento:
            print(f'Memento: {memento}, text: {memento.message_text}')
            return memento.message_text
        else:
            print('None')
            return None

    def add_observer(self, observer: SentimentFlagObserver):
        self.observers.append(observer)

    def remove_observer(self, observer: SentimentFlagObserver):
        self.observers.remove(observer)

    def notify_observer(self):
        for observer in self.observers:
            observer.update()

    def start(self):
        print('Starting bot...')
        self.app = Application.builder().token(TOKEN).build()

        observer = SentimentFlagObserver()
        self.add_observer(observer)

        # Commands
        self.app.add_handler(CommandHandler('start', lambda update, context: self.command_invoker.execute_command('start', update, context)))
        self.app.add_handler(CommandHandler('help', lambda update, context: self.command_invoker.execute_command('help', update, context)))
        self.app.add_handler(CommandHandler('sentiment_analysis', lambda update, context: self.command_invoker.execute_command('sentiment_analysis', update, context)))
        self.app.add_handler(CommandHandler('message_processing', lambda update, context: self.command_invoker.execute_command('message_processing', update, context)))
        self.app.add_handler(CommandHandler('restore_message', lambda update, context: self.command_invoker.execute_command('restore_message', update, context)))
        self.app.add_handler(CommandHandler('get_posts_responses', lambda update, context: self.command_invoker.execute_command('get_posts_responses', update, context)))
        self.app.add_handler(CommandHandler('get_messages', lambda update, context: self.command_invoker.execute_command('get_messages', update, context)))
        self.app.add_handler(CommandHandler('exit', lambda update, context: self.command_invoker.execute_command('exit', update, context)))

        # Messages
        self.app.add_handler(MessageHandler(filters.TEXT, handle_message))

        # Errors
        self.app.add_error_handler(error)

        # Polls the bot
        print('Polling...')
        self.app.run_polling(poll_interval=3)


class Observer(ABC):
    @abstractmethod
    def update(self):
        pass

class SentimentFlagObserver(Observer):
    def update(self):
        global sentiment_flag
        sentiment_flag = True

class Command(ABC):
    @abstractmethod
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass

class StartCommand(Command):
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        global isActive_flag
        isActive_flag = True
        await update.message.reply_text('Hello! How can I help you ?')
        bot.save_message('Hello! How can I help you ?')



class HelpCommand(Command):
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('You can send a text message and I will do a sentiment analysis.')
        bot.save_message('You can send a text message and I will do a sentiment analysis.')

class SentimentAnalysisCommand(Command):
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot.notify_observer()
        await update.message.reply_text('Ok. Enter text, comment, feedback, etc. - what needs to be processed: ')
        bot.save_message('Ok. Enter text, comment, feedback, etc. - what needs to be processed: ')

class GetMessageCommand(Command):
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            posts = list(mongo.get_all_posts())

            if not (len(posts) > 0):
                await context.bot.send_message(chat_id=update.message.chat_id, text='There are no posts yet...')
                return

            messages = []
            for post in posts:
                post_message = f"\nPOST ID: {post['POST_ID']}, POST MESSAGE: {post['POST_MESSAGE']}\nCOMMENTS UNDER POST:\n"
                comments = [comment.strip() for comment in post['COMMENTS_UNDER_POST']]
                comment_message = "\n".join(comments)
                mood_message = f"\nThe general emotional mood under this post: {post['GENERAL_EMOTIONAL_MOOD']['CATEGORY']}, {post['GENERAL_EMOTIONAL_MOOD']['RATING']}"
                message = post_message + comment_message + mood_message
                print(message)
                messages.append(message)
            await context.bot.send_message(chat_id=update.message.chat_id, text="\n".join(messages))
            bot.save_message("\n".join(messages))
        except Exception as e:
            print(f"Error occurred: {e}")



class MessageProcessingCommand(Command):
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            await context.bot.send_message(chat_id=update.message.chat_id, text='The message has been processed and saved in the database!')
            post_keys = []
            posts = list(mongo.get_all_posts())
            for post in posts:
                post_keys.append(post["POST_ID"])
            print(post_keys)

            for key in group_posts:
                if key in responses:

                    size = len(responses[key])
                    sum_sentiment = 0
                    sum_toxicity = 0

                    comments = []
                    for values in responses[key]:
                        res = f"{values['message']} : {values['sentiment_analysis']} : {values['toxicity_analysis']}\n"
                        comments.append(res)
                        sum_sentiment += float(values['sentiment_analysis'])
                        sum_toxicity += float(values['toxicity_analysis'])

                    average_toxicity = sum_toxicity / size
                    average_emotion = sum_sentiment / size
                    mood_category = self.determine_mood_category(average_emotion)

                    post_data = {
                        "POST_ID": str(key),
                        "POST_MESSAGE": group_posts[key]["message"],
                        "COMMENTS_UNDER_POST": comments[:],
                        "GENERAL_EMOTIONAL_MOOD": {"CATEGORY": mood_category, "RATING": average_emotion, "TOXICITY": average_toxicity}
                    }

                    if len(post_keys) > 0:
                        if str(key) in post_keys:
                            mongo.db['posts'].update_one({"POST_ID": str(key)}, {"$set": {"COMMENTS_UNDER_POST": comments[:],"GENERAL_EMOTIONAL_MOOD": {"CATEGORY": mood_category,"RATING": average_emotion, "TOXICITY": average_toxicity}}})
                        else:
                            mongo.insert_post(post_data)

                    else:
                        mongo.insert_post(post_data)

                else:
                    post_data = {
                        "POST_ID": str(key),
                        "POST_MESSAGE": group_posts[key]["message"],
                        "COMMENTS_UNDER_POST": ["NO COMMENTS YET..."],
                        "GENERAL_EMOTIONAL_MOOD": {"CATEGORY": "Neutral", "RATING": 0, "TOXICITY": 0}
                    }

                    if len(post_keys) > 0:
                        if str(key) not in post_keys:
                            mongo.insert_post(post_data)
                    else:
                        mongo.insert_post(post_data)

        except Exception as e:
            print(f"Error occurred: {e}")

    def determine_mood_category(self, average_emotion):
        if average_emotion <= -1:
            return "Super negative"
        elif -1 < average_emotion <= -0.8:
            return "Very negative"
        elif -0.8 < average_emotion <= -0.6:
            return "Negative"
        elif -0.6 < average_emotion <= -0.4:
            return "Slightly Negative"
        elif -0.4 < average_emotion <= -0.2:
            return "A little Negative"
        elif -0.2 < average_emotion <= 0.2:
            return "Neutral"
        elif 0.2 < average_emotion <= 0.4:
            return "Slightly positive"
        elif 0.4 < average_emotion <= 0.6:
            return "Positive"
        elif 0.6 < average_emotion <= 0.8:
            return "Very positive"
        elif 0.8 < average_emotion:
            return "Super positive"

class RestoreMessageCommand(Command):
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message_text = bot.restore_message()
        await update.message.reply_text(message_text)

class GetPostsResponsesCommand(Command):
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(group_posts)
        bot.save_message(group_posts)
        await update.message.reply_text(responses)
        bot.save_message(responses)

class ExitCommand(Command):
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        global isActive_flag
        isActive_flag = False
        await update.message.reply_text('Goodbye!')
        bot.save_message('Goodbye')


class CommandInvoker:
    def __init__(self):
        self.commands = {}

    def add_command(self, command_name, command):
        self.commands[command_name] = command

    async def execute_command(self, command_name, update: Update, context: ContextTypes.DEFAULT_TYPE):
        command = self.commands.get(command_name)
        if command_name == 'start':
            await command.execute(update, context)
        elif command:
            if isActive_flag == True:
                await command.execute(update, context)
            else:
                if command_name == 'exit':
                    print('Bot is already shutdown!')
                    await update.message.reply_text('Bot is already shutdown!')
                print('Bot is shutdown!')
                await update.message.reply_text('Bot is shutdown!')
        else:
            print(f'Error. Command {command_name} not found!')


def handle_response(text: str) -> str:
    if isActive_flag == True:
        processed_text: str = text.lower()

        if 'hello' in processed_text:
            return 'Hello!'
        if 'how are you' in processed_text:
            return 'Everything is stable'
        if 'who are you' in processed_text:
            return 'I am a chatbot!'
        if 'what can you do' in processed_text:
            return 'I can assist you with various tasks. Just ask!'
        if 'tell me a joke' in processed_text:
            return 'Why did the scarecrow win an award? Because he was outstanding in his field!'
        if 'what is the meaning of life' in processed_text:
            return 'The answer to the ultimate question of life, the universe, and everything is 42.'
        if 'goodbye' in processed_text:
            return 'Goodbye! Have a great day!'
        return 'I am not sure how to respond to that.\nIDK..'
    else:
        print('Bot is shutdown!')
        return('Bot is shutdown!')




async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global sentiment_flag, isActive_flag

    if isActive_flag == True:
        if update.channel_post is not None:
            message_id: int = update.channel_post.message_id
            message_type: str = update.channel_post.chat.type
            message_text: str = update.channel_post.text
            print(f'Chat ID ({update.channel_post.chat.id}) in {message_type}: "{message_text}" - channel_post')

            channel_posts.append(message_text)
            print(channel_posts)


        elif update.message is not None:
            message_id: int = update.message.message_id
            message_type: str = update.message.chat.type
            message_text: str = update.message.text

            # sentiment = bot_sentiment_analysis(message_text)
            # toxicity = bot_toxicity_analysis(message_text)

            print(f'Chat ID ({update.message.chat.id}) in {message_type}: "{message_text}" - message')

            if message_type == 'group':
                if BOT_USERNAME in message_text:
                    new_message_text: str = message_text.replace(BOT_USERNAME, ' ').strip()
                    sentiment = bot_sentiment_analysis(message_text)
                    toxicity = bot_toxicity_analysis(message_text)
                    responses[message_id] = [{'message': message_text, 'sentiment_analysis': sentiment, 'toxicity_analysis': toxicity}]
                    print(responses)
            elif message_type == 'private':
                if sentiment_flag == True:
                    sentiment = bot_sentiment_analysis(message_text)
                    toxicity = bot_toxicity_analysis(message_text)
                    if sentiment > 0:
                        await update.message.reply_text(f'Text is positive: {sentiment}. Toxicity: {toxicity}.')
                        bot.save_message(f'Text is positive: {sentiment}. Toxicity: {toxicity}.')
                    elif sentiment == 0:
                        await update.message.reply_text(f'Text is neutral: {sentiment}. Toxicity: {toxicity}.')
                        bot.save_message(f'Text is neutral: {sentiment}. Toxicity: {toxicity}.')
                    else:
                        await update.message.reply_text(f'Text is negative: {sentiment}. Toxicity: {toxicity}.')
                        bot.save_message(f'Text is negative: {sentiment}. Toxicity: {toxicity}.')
                    sentiment_flag = False
                else:
                    response: str = handle_response(message_text)
                    print('Bot: ', response)
                    await update.message.reply_text(response)
                    bot.save_message(response)
            elif message_type == 'supergroup':
                if update.message.reply_to_message is not None:
                    original_message = update.message.reply_to_message
                    print('response to the channel post')
                    print(f'original text: {original_message.text}, id: {original_message.id}, response text: {message_text}, id: {message_id}')

                    sentiment = bot_sentiment_analysis(message_text)
                    toxicity = bot_toxicity_analysis(message_text)
                    print(f'deb: {original_message.id}, keys_responses: {responses.keys()}, bool: {str({original_message.id}) in responses}')
                    print(responses)
                    if str(original_message.id) in responses:
                        existing_values = responses[str(original_message.id)]
                        existing_values.append({'message': message_text, 'sentiment_analysis': sentiment, 'toxicity_analysis': toxicity, 'id': message_id,'original_message_post': original_message.text})
                    else:
                        responses[str(original_message.id)] = [{'message': message_text, 'sentiment_analysis': sentiment, 'toxicity_analysis': toxicity, 'id': message_id,'original_message_post': original_message.text}]
                    print(responses)
                else:
                    if len(channel_posts) > 0:
                        if message_text == channel_posts[-1]:
                            sentiment = bot_sentiment_analysis(message_text)
                            toxicity = bot_toxicity_analysis(message_text)
                            group_posts[str(message_id)] = {'message': message_text, 'sentiment_analysis': sentiment, 'toxicity_analysis': toxicity}
                            print(group_posts)
                    else:
                        sentiment = bot_sentiment_analysis(message_text)
                        toxicity = bot_toxicity_analysis(message_text)
                        if 'random_comment' in responses:
                            existing_values = responses['random_comment']
                            existing_values.append({'message': message_text, 'sentiment_analysis': sentiment, 'toxicity_analysis': toxicity})
                            print(responses)
                        else:
                            responses['random_comment'] = [{'message': message_text, 'sentiment_analysis': sentiment, 'toxicity_analysis': toxicity}]
                            print(responses)

            with open('Data/posts_dict.txt', 'w') as file:
                json.dump(group_posts, file)

            with open('Data/resp_dict.txt', 'w') as file:
                json.dump(responses, file)

            with open('Data/posts_dict.txt', 'r') as file:
                data = json.load(file)
            group_posts.update(data)

            with open('Data/resp_dict.txt', 'r') as file:
                data = json.load(file)
            responses.update(data)
    else:
        await update.message.reply_text('Bot is shutdown!')




async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error{context.error}')

if __name__ == '__main__':
    with open('Data/posts_dict.txt', 'r') as file:
        data = json.load(file)
    group_posts.update(data)

    with open('Data/resp_dict.txt', 'r') as file:
        data = json.load(file)
    responses.update(data)

    command_invoker = CommandInvoker()
    command_invoker.add_command('start', StartCommand())
    command_invoker.add_command('help', HelpCommand())
    command_invoker.add_command('sentiment_analysis', SentimentAnalysisCommand())
    command_invoker.add_command('message_processing', MessageProcessingCommand())
    command_invoker.add_command('restore_message', RestoreMessageCommand())
    command_invoker.add_command('get_posts_responses', GetPostsResponsesCommand())
    command_invoker.add_command('get_messages', GetMessageCommand())
    command_invoker.add_command('exit', ExitCommand())

    mongo = MongoDB()
    bot = TelegramBot(TOKEN, BOT_USERNAME, command_invoker, mongo)
    bot.start()

    with open('Data/posts_dict.txt', 'w') as file:
        json.dump(group_posts, file)

    with open('Data/resp_dict.txt', 'w') as file:
        json.dump(responses, file)

