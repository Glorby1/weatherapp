import requests
from datetime import datetime, timedelta
from opencage.geocoder import OpenCageGeocode
from weatherapp_db import *

def get_user_choice():
    while True:
        print("Choose an option:")
        print("1. Real-time weather")
        print("2. Forecast")
        print("3. Update saved searches")
        choice = input("Your choice: ")
        if choice in ["1", "2", "3"]:
            return choice
        print("Please enter 1, 2, or 3.")

def search_city(query, opencage_api_key):
    geocoder = OpenCageGeocode(opencage_api_key)
    results = geocoder.geocode(query)

    if not results:
        print(f"[OpenCage] No results found for '{query}'.")
        return []

    formatted_results = []
    for result in results:
        # Extract main data
        components = result.get('components', {})
        name = components.get('city') or components.get('town') or components.get('village') or components.get('suburb') or query
        country = components.get('country', 'Unknown')
        lat = result['geometry']['lat']
        lon = result['geometry']['lng']

        # Format like WeatherAPI
        formatted_results.append({
            'name': name,
            'country': country,
            'lat': lat,
            'lon': lon
        })

    print(f"[OpenCage] {len(formatted_results)} results found for '{query}'.")
    return formatted_results

def fetch_weather_realtime(lat, lon, city, api_key, db_conn):
    date = datetime.now().date()
    cursor = db_conn.cursor()

    # Check database for city/date
    if is_weather_in_db(cursor, city, date):
        weather_data = get_weather_from_db(cursor, city, date)
    else:
        # API request for data
        url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={lat},{lon}&aqi=no"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            current = data['current']
            weather_data = {
                'condition': current['condition']['text'],
                'temp': current['temp_c'],
                'feels_like': current['feelslike_c'],
                'humidity': current['humidity'],
                'wind_speed': current['wind_kph']
            }

            # Save data to database
            save_weather_to_db(cursor, city, date, weather_data['condition'], weather_data['temp'], weather_data['feels_like'], weather_data['humidity'], weather_data['wind_speed'], lat, lon)
            db_conn.commit()
        else:
            print("Error retrieving weather data.")
            return

    # Display weather data
    print(f"Date: {date}, Location: {city}, Condition: {weather_data['condition']}, "
          f"Temperature: {weather_data['temp']}°C, Feels like: {weather_data['feels_like']}°C, "
          f"Humidity: {weather_data['humidity']}%, Wind: {weather_data['wind_speed']} km/h")

def fetch_weather_dates(lat, lon, city_name, start_date, end_date, api_key, db_conn):
    cursor = db_conn.cursor()

    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    current_date = datetime.now().date()

    date = start_date
    while date <= end_date:
        if is_weather_in_db(cursor, city_name, date):
            weather_data = get_weather_from_db(cursor, city_name, date)
        else:
            # Determine which API endpoint to use
            if date < current_date:
                endpoint = "history"
            elif (date - current_date).days <= 14:
                endpoint = "forecast"
            else:
                endpoint = "future"  # Use the 'future' endpoint for dates more than 14 days ahead

            # API request
            url = f"http://api.weatherapi.com/v1/{endpoint}.json?key={api_key}&q={lat},{lon}&dt={date}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                day_data = data.get('forecast', {}).get('forecastday', [])[0]['day']
                weather_data = {
                    'condition': day_data['condition']['text'],
                    'temp': day_data['avgtemp_c'],
                    'feels_like': day_data['avgtemp_c'],
                    'humidity': day_data['avghumidity'],
                    'wind_speed': day_data['maxwind_kph']
                }

                # Save data to the database
                save_weather_to_db(cursor, city_name, date, weather_data['condition'], weather_data['temp'],
                                   weather_data['feels_like'], weather_data['humidity'], weather_data['wind_speed'], lat, lon)
                db_conn.commit()
            else:
                print(f"Error for date {date}.")
                date += timedelta(days=1)
                continue

        # Display weather data
        print(f"Date: {date}, City: {city_name}, Condition: {weather_data['condition']}, "
              f"Temperature: {weather_data['temp']}°C, Feels like: {weather_data['feels_like']}°C, "
              f"Humidity: {weather_data['humidity']}%, Wind: {weather_data['wind_speed']} km/h")

        date += timedelta(days=1)


def option1(api_key, db_conn):
    # Real-time weather
    city_name = input("Enter the city name: ")
    cities = search_city(city_name, "9c2dd9f3767f468bba40f04ea4b428ed")

    if not cities:
        print("No cities found.")
        return

    print("Available cities:")
    for idx, city in enumerate(cities):
        print(f"{idx + 1}. {city['name']}, {city['country']}")

    while True:
        try:
            selected_city = int(input("Choose a city (number): ")) - 1
            if 0 <= selected_city < len(cities):
                break
            print("Please enter a valid number.")
        except ValueError:
            print("Please enter a valid number.")

    city_data = cities[selected_city]
    city_name = f"{city_data['name']}, {city_data['country']}"
    lat, lon = city_data['lat'], city_data['lon']
    fetch_weather_realtime(lat, lon, city_name, api_key, db_conn)

def option2(api_key, db_conn):
    # Forecast
    city_name = input("Enter the city name: ")
    cities = search_city(city_name, "9c2dd9f3767f468bba40f04ea4b428ed")

    if not cities:
        print("No cities found.")
        return

    print("Available cities:")
    for idx, city in enumerate(cities):
        print(f"{idx + 1}. {city['name']}, {city['country']}")

    while True:
        try:
            selected_city = int(input("Choose a city (number): ")) - 1
            if 0 <= selected_city < len(cities):
                break
            print("Please enter a valid number.")
        except ValueError:
            print("Please enter a valid number.")

    city_data = cities[selected_city]
    city_name = f"{city_data['name']}, {city_data['country']}"
    lat, lon = city_data['lat'], city_data['lon']

    start_date = input("Enter the start date (YYYY-MM-DD): ")
    end_date = input("Enter the end date (YYYY-MM-DD): ")
    fetch_weather_dates(lat, lon, city_name, start_date, end_date, api_key, db_conn)

def option3(api_key, db_conn):
    # Update saved searches
    cursor = db_conn.cursor()
    while True:
        rows = display_database(cursor)
        if not rows:
            break

        user_input = input("Enter an ID to update or 'stop' to quit: ").strip()
        if user_input.lower() == "stop":
            print("Update completed.")
            break

        try:
            entry_id = int(user_input)
            selected_row = next((row for row in rows if row[0] == entry_id), None)
            if selected_row:
                city, date = selected_row[1], selected_row[2]
                update_or_delete_entry(db_conn, api_key, entry_id, city, date)
            else:
                print(f"No record found with ID={entry_id}.")
        except ValueError:
            print("Please enter a valid ID or 'stop'.")

def main():
    api_key = "8458eb9f719b47fbbbf184225252501"
    db_conn = connect_to_db()

    print("Welcome to the Weather App!")
    while True:
        choice = get_user_choice()

        if choice == "1":
            option1(api_key, db_conn)
        elif choice == "2":
            option2(api_key, db_conn)
        elif choice == "3":
            option3(api_key, db_conn)
        else:
            print("Invalid choice.")

        # Ask if the user wants to continue or quit
        user_continue = input("\nDo you want to continue? (Enter to continue, 'q' to quit): ").strip().lower()
        if user_continue == "q":
            print("Thank you for using the Weather App. Goodbye!")
            break

    db_conn.close()

if __name__ == "__main__":
    main()
