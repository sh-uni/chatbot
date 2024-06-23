# import the required libraries
from flask import Flask, render_template, request
from accessories import *
from weather_training import *
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer, ChatterBotCorpusTrainer

# get API keys
set_API_keys()

# set the itinerary data and get list of keys
itinerary_location_keys = set_itinerary()

# initialise weather data - only update if longer than no. of minutes
print('Retrieving weather data. This may take a few seconds...')
forecast_dfs, forecast_temps, best_days, weather_summary, set_of_days, set_of_hours = initialise_weather_data(15)

# create weather training file
create_weather_test_file(itinerary_location_keys, forecast_dfs, forecast_temps,
                         best_days, weather_summary, set_of_days, set_of_hours)

# initialise bot
my_bot = ChatBot(
    name="Mr Bot",
    read_only=True,
    logic_adapters=["chatterbot.logic.MathematicalEvaluation",
                    "chatterbot.logic.BestMatch"]
)

# set list trainer
list_trainer = ListTrainer(my_bot)

# train with corpus
corpus_trainer = ChatterBotCorpusTrainer(my_bot)
corpus_trainer.train('chatterbot.corpus.english.ai',
                     'chatterbot.corpus.english.botprofile',
                     'chatterbot.corpus.english.computers',
                     'chatterbot.corpus.english.conversations',
                     'chatterbot.corpus.english.emotion',
                     'chatterbot.corpus.english.greetings',
                     'chatterbot.corpus.english.humor')

# train with created files
general_training = open('training_data/general_conversation.txt').read().splitlines()
weather_training_manual = open('training_data/weather_training_manual.txt').read().splitlines()
weather_training = open('training_data/weather_training.txt').read().splitlines()
for item in (general_training, weather_training_manual, weather_training):
    list_trainer.train(item)

# Standard code block to run Flask.
app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html",
                            bot_name=my_bot.name)


@app.route("/get")
def get_bot_response():
    user_input = request.args.get('msg')
    bot_response = my_bot.get_response(user_input)
    print(f"You: {user_input}")
    print(f"{my_bot.name}: {bot_response}")
    return str(bot_response)


if __name__ == "__main__":
    app.run()