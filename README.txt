Project Title:
Chatbot Assignment for COS60016 Programming for Development

Project Description:
This project implements a chatbot with weather data for a set itinerary of travel locations.
The chatbot can retrieve weather data for each location given a variety of questions.

How to Install and Run the Project:
1. Add this project to a folder in your PC.
2. Open the project in pyCharm or equivalent.
    NOTE: the ChatterBot library is not currently supported by versions beyond python 3.7.9
    If you have a newer version of Python:
        - Uninstall python and reinstall python3.7.9
    OR
        - Install python 3.7.9 and open the project in a virtual environment.
3. Add your own Open Weather API key to <insertAPIkey> in to static/text/API_keys.txt
    A free API key will work.
4. Install the following via terminal:
    pip3 install ChatterBot==1.0.5
    pip3 install ChatterBot_corpus
    pip3 install flask
    pip3 install pandas
5. You are ready to try running the project.
    Run main.py


How to Use:
When the project initialises from running main.py, click the link or navigate to 'http://127.0.0.1:5000'.
Chat to the bot!
Try the following for itinerary weather data:
    1. 'When should I visit Watergate Bay?'
    2. 'Is Corfe Castle cold today?'
    3. 'Should I visit Stonehenge this week?'
    4. 'What will the weather be in Birmingham on Tuesday morning?'
    This last option may still be a bit buggy but give it a try.