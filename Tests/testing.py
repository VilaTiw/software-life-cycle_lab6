import unittest
from EmotionAnalysis.sentiment_analysis.sentiment_analysis import ArticleBlobStrategy
from telegram_bot import TelegramBot, SentimentFlagObserver, SentimentAnalyser, TextBlobStrategy, CommandInvoker, CareTaker, MessageMemento, handle_response, StartCommand, HelpCommand, SentimentAnalysisCommand, MessageProcessingCommand, RestoreMessageCommand
from telegram import Update
from telegram.ext import ContextTypes
from unittest.mock import MagicMock

class TestCommands(unittest.TestCase):
    async def test_start_command(self):
        command = StartCommand()
        mock_message = MagicMock()
        mock_message.text = "Test message"
        update = Update(update_id=1, message=mock_message)
        context = ContextTypes.DEFAULT_TYPE
        command_result = await command.execute(update, context)
        self.assertEqual(command_result, "Hello! How can I help you ?")

    async def test_help_command(self):
        command = HelpCommand()
        mock_message = MagicMock()
        mock_message.text = "Test message"
        update = Update(update_id=1, message=mock_message)
        context = ContextTypes.DEFAULT_TYPE
        command_result = await command.execute(update, context)
        self.assertEqual(command_result, "You can send a text message and I will do a sentiment analysis.")

    async def test_sentiment_analysis_command(self):
        command = SentimentAnalysisCommand()
        mock_message = MagicMock()
        mock_message.text = "Test message"
        update = Update(update_id=1, message=mock_message)
        context = ContextTypes.DEFAULT_TYPE
        command_result = await command.execute(update, context)
        self.assertEqual(command_result, "Ok. Enter text, comment, feedback, etc. - what needs to be processed: ")

    async def test_message_processing_command(self):
        command = MessageProcessingCommand()
        mock_message = MagicMock()
        mock_message.text = "Test message"
        update = Update(update_id=1, message=mock_message)
        context = ContextTypes.DEFAULT_TYPE
        command_result = await command.execute(update, context)
        self.assertIsNone(command_result)  # Assuming MessageProcessingCommand doesn't return any value

    async def test_restore_message_command(self):
        command = RestoreMessageCommand()
        mock_message = MagicMock()
        mock_message.text = "Test message"
        update = Update(update_id=1, message=mock_message)
        context = ContextTypes.DEFAULT_TYPE
        command_result = await command.execute(update, context)
        self.assertIsNone(command_result)  # Assuming RestoreMessageCommand doesn't return any value

class TestHandleResponse(unittest.TestCase):
    def test_hello_response(self):
        response = handle_response("Hello")
        self.assertEqual(response, "Hello!")

    def test_how_are_you_response(self):
        response = handle_response("How are you?")
        self.assertEqual(response, "Everything is stable")

    def test_who_are_you_response(self):
        response = handle_response("Who are you?")
        self.assertEqual(response, "I am a chatbot!")

    def test_what_can_you_do_response(self):
        response = handle_response("What can you do?")
        self.assertEqual(response, "I can assist you with various tasks. Just ask!")

    def test_tell_me_a_joke_response(self):
        response = handle_response("Tell me a joke")
        self.assertEqual(response, "Why did the scarecrow win an award? Because he was outstanding in his field!")

    def test_meaning_of_life_response(self):
        response = handle_response("What is the meaning of life?")
        self.assertEqual(response, "The answer to the ultimate question of life, the universe, and everything is 42.")

    def test_unknown_response(self):
        response = handle_response("Random text")
        self.assertEqual(response, "I am not sure how to respond to that.\nIDK..")

class TestCareTaker(unittest.TestCase):
    def test_add_memento(self):
        caretaker = CareTaker()
        memento = MessageMemento("Test message")
        caretaker.add_memento(memento)
        self.assertEqual(len(caretaker._CareTaker__mementos), 1)

    def test_get_memento(self):
        caretaker = CareTaker()
        memento1 = MessageMemento("Test message 1")
        memento2 = MessageMemento("Test message 2")
        caretaker.add_memento(memento1)
        caretaker.add_memento(memento2)
        memento, index = caretaker.get_memento(1)
        self.assertEqual(memento.message_text, "Test message 2")
        self.assertEqual(index, 1)

class TestTelegramBot(unittest.TestCase):
    def setUp(self):
        self.command_invoker = CommandInvoker()
        self.mongo_mock = MagicMock()
        self.bot = TelegramBot("TOKEN", "BOT_USERNAME", self.command_invoker, self.mongo_mock)

    def test_bot_initialization(self):
        # Assert
        self.assertEqual(self.bot.token, "TOKEN")
        self.assertEqual(self.bot.bot_username, "BOT_USERNAME")
        self.assertIsNone(self.bot.app)
        self.assertEqual(len(self.bot.observers), 0)
        self.assertIsNotNone(self.bot._TelegramBot__caretaker)

    def test_add_remove_observer(self):
        # Arrange
        observer = SentimentFlagObserver()

        # Act
        self.bot.add_observer(observer)

        # Assert
        self.assertEqual(len(self.bot.observers), 1)
        self.assertIn(observer, self.bot.observers)

        # Act
        self.bot.remove_observer(observer)

        # Assert
        self.assertEqual(len(self.bot.observers), 0)
        self.assertNotIn(observer, self.bot.observers)

    def test_create_memento(self):
        # Arrange
        message_text = "Test message"

        # Act
        memento = self.bot.create_memento(message_text)

        # Assert
        self.assertEqual(memento.message_text, message_text)

    def test_save_restore_message(self):
        # Arrange
        message_text = "Test message"
        update = MagicMock()
        context = MagicMock()

        # Act
        self.bot.save_message(message_text)
        restored_message = self.bot.restore_message()

        # Assert
        self.assertEqual(restored_message, message_text)

    def test_notify_observer(self):
        # Arrange
        observer = SentimentFlagObserver()
        observer.update = MagicMock()
        self.bot.add_observer(observer)

        # Act
        self.bot.notify_observer()

        # Assert
        observer.update.assert_called_once()


class TestSentimentAnalyser(unittest.TestCase):
    def test_textblob_strategy(self):
        # Arrange
        strategy = TextBlobStrategy()
        analyser = SentimentAnalyser(strategy)
        text = "This is a positive sentence."

        # Act
        sentiment = analyser.analyze_sentiment(text)

        # Assert
        self.assertTrue(-1 <= sentiment <= 1)

    def test_articleblob_strategy(self):
        # Arrange
        strategy = ArticleBlobStrategy()
        analyser = SentimentAnalyser(strategy)
        url = "https://en.wikipedia.org/wiki/Artificial_intelligence"

        # Act
        sentiment = analyser.analyze_sentiment(url)

        # Assert
        self.assertTrue(-1 <= sentiment <= 1)

if __name__ == "__main__":
    unittest.main()
