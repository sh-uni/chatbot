
# open weather_training text file and add new conversations
def create_weather_test_file(keys, dfs, forecast_temps, best_days, weather_summary, set_of_days, set_of_hours):

    # a few simple creations for each site
    file = open('training_data/weather_training.txt', 'w')
    file.write(str('Do you know the weather?'))
    file.write(str('\n'))
    file.write(str('Yes, I know the weather for the itinerary'))

    # automatic q/a creation for each site
    for key in keys:
        # temperatures for today
        question_variations = [str('What\'s the temperature in ' + str(key) + '?'),
                               str('What\'s today\'s temperature in ' + str(key) + '?'),
                               str('Is ' + str(key) + ' cold today?'),
                               str(str(key) + '\'s temperature today?')]
        for question in question_variations:
            q_line = question
            a_line = str(str(key) + ' will reach '+str(forecast_temps[key][0][1]['max'])
                         + '°C today, with a low of '+str(forecast_temps[key][0][1]['min']) + '°C')
            file.write(str('\n'))
            file.write(q_line)
            file.write(str('\n'))
            file.write(a_line)

        # best day to visit location
        question_variations = [str('When should I visit ' + str(key) + '?'),
                               str('What\'s the best day to visit ' + str(key) + '?'),
                               str('When will ' + str(key) + ' have nice weather?'),
                               str('Is ' + str(key) + ' nice?'),
                               str('Should I visit ' + str(key) + ' this week?'),
                               str('Should I visit ' + str(key) + '?')]
        for question in question_variations:
            q_line = question
            a_line = str('The best day to visit ' + str(key) + ' is ' + str(best_days[key]))
            file.write(str('\n'))
            file.write(q_line)
            file.write(str('\n'))
            file.write(a_line)

        # morning and afternoon data for next 5 days
        morning_time = 9  # 9am
        afternoon_time = 15 #3pm
        closest_to_morning = min(set_of_hours, key=lambda x: abs(x - morning_time))
        closest_to_afternoon = min(set_of_hours, key=lambda x: abs(x - afternoon_time))

        for time_of_day, time in zip(['morning', 'afternoon'], [closest_to_morning, closest_to_afternoon]):
            for day in set_of_days:
                question_variations = [str('What will the weather be in ' + str(key)
                                           + ' on ' + str(day) + ' ' + str(time_of_day) + '?'),
                                       str(str(day) + ' ' + str(time_of_day) + ' weather in ' + str(key) + '?')]
                for question in question_variations:
                    try:
                        q_line = question
                        a_line = str('The weather in ' + str(key) + ' on ' + str(day) + ' '
                                     + str(time_of_day) + ' will be '
                                     + str(weather_summary[key][day][time]['temp']) + '°C with '
                                     + str(weather_summary[key][day][time]['description']) + ', '
                                     + str(weather_summary[key][day][time]['humidity']) + ' % humidity and '
                                     + str(weather_summary[key][day][time]['wind']) + ' km/h winds. ')
                        file.write(str('\n'))
                        file.write(q_line)
                        file.write(str('\n'))
                        file.write(a_line)
                    except:
                        continue

    file.close()