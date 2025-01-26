import mysql.connector
import requests

def connect_to_db():
    # Connection to the database
    return mysql.connector.connect(
        host="localhost",
        user="user",
        password="password",  # Replace with your MySQL password
        database="weather_db"
    )

def display_database(cursor):
    query = "SELECT * FROM weather_data"
    cursor.execute(query)
    rows = cursor.fetchall()
    if not rows:
        return []

    for row in rows:
        print(f"ID: {row[0]}, Date: {row[1]}, City: {row[2]}, Weather: {row[5]}, Temperature: {row[6]}°C, "
              f"Feels like: {row[7]}°C, Humidity: {row[8]}%, Wind speed: {row[9]} km/h, "
              f"Last update: {row[10]}")
    return rows

def update_database_entry(db_conn, api_key, entry_id, city, date):
    cursor = db_conn.cursor()

    # API request to fetch new data
    url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={city}&dt={date}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        day_data = data['forecast']['forecastday'][0]['day']
        condition = day_data['condition']['text']
        temp = day_data['avgtemp_c']
        feels_like = day_data['avgtemp_c']
        humidity = day_data['avghumidity']
        wind_speed = day_data['maxwind_kph']

        # Update the row in the database
        query = (
            "UPDATE weather_data "
            "SET weather_condition = %s, temperature = %s, feels_like = %s, "
            "humidity = %s, wind_speed = %s, last_updated = CURRENT_TIMESTAMP "
            "WHERE id = %s"
        )
        cursor.execute(query, (condition, temp, feels_like, humidity, wind_speed, entry_id))
        db_conn.commit()
        print(f"[DB] Row successfully updated for ID={entry_id}.")
    else:
        print(f"[API] Failed to update for city={city}, date={date}. Error: {response.status_code}")

def update_or_delete_entry(db_conn, api_key, entry_id, city, date):
    cursor = db_conn.cursor()

    while True:
        print("\nWhat would you like to do with this entry?")
        print("1. Update")
        print("2. Delete")
        choice = input("Your choice: ").strip()

        if choice == "1":
            # Update the entry
            update_database_entry(db_conn, api_key, entry_id, city, date)
            break
        elif choice == "2":
            # Ask for confirmation to delete
            confirm = input(f"Are you sure you want to delete the search for '{city}' on '{date}'? (yes/no): ").strip().lower()
            if confirm == "yes":
                delete_database_entry(cursor, entry_id)
                db_conn.commit()
                print(f"[DB] Entry with ID={entry_id} successfully deleted.")
            else:
                print("[DB] Deletion canceled.")
            break
        else:
            print("Please enter 1 to update or 2 to delete.")

def delete_database_entry(cursor, entry_id):
    query = "DELETE FROM weather_data WHERE id = %s"
    cursor.execute(query, (entry_id,))

def is_weather_in_db(cursor, city, date):
    query = "SELECT id FROM weather_data WHERE city = %s AND date = %s"
    cursor.execute(query, (city, date))
    result = cursor.fetchone()

    if result:
        return True
    else:
        return False

def get_weather_from_db(cursor, city_name, date):
    query = """
        SELECT 
            date, city, weather_condition, temperature, feels_like, humidity, wind_speed
        FROM 
            weather_data
        WHERE 
            city = %s AND date = %s
    """
    cursor.execute(query, (city_name, date))
    result = cursor.fetchone()

    if result:
        weather_data = {
            "date": result[0],
            "city": result[1],
            "condition": result[2],
            "temp": result[3],
            "feels_like": result[4],
            "humidity": result[5],
            "wind_speed": result[6],
        }
        return weather_data
    else:
        print(f"[DB] No data found for city={city_name}, date={date}.")
        return None

def save_weather_to_db(cursor, city, date, condition, temp, feels_like, humidity, wind_speed, lat, lon):
    query = (
        "INSERT INTO weather_data (city, date, weather_condition, temperature, feels_like, humidity, wind_speed, lat, lon) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE "
        "weather_condition = VALUES(weather_condition), "
        "temperature = VALUES(temperature), "
        "feels_like = VALUES(feels_like), "
        "humidity = VALUES(humidity), "
        "wind_speed = VALUES(wind_speed), "
        "last_updated = CURRENT_TIMESTAMP"
    )
    cursor.execute(query, (city, date, condition, temp, feels_like, humidity, wind_speed, lat, lon))
    print(f"[DB] Data inserted or updated for city={city}, date={date}.")
