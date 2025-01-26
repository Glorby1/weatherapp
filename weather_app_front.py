import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from weather_app import *

class WeatherAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather App")
        
        self.api_key = "8458eb9f719b47fbbbf184225252501"
        self.db_conn = connect_to_db()
        
        self.main_menu()

    def main_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        label = tk.Label(self.root, text="Bienvenue dans l'application météo !", font=("Arial", 16))
        label.pack(pady=10)

        tk.Button(self.root, text="Temps Réel", command=self.realtime_menu).pack(pady=5)
        tk.Button(self.root, text="Prévisions", command=self.forecast_menu).pack(pady=5)
        tk.Button(self.root, text="Mettre à jour les recherches", command=self.update_menu).pack(pady=5)
        tk.Button(self.root, text="Quitter", command=self.root.quit).pack(pady=20)

    def realtime_menu(self):
        self._clear_widgets()

        tk.Label(self.root, text="Entrez le nom de la ville :", font=("Arial", 12)).pack(pady=5)
        city_entry = ttk.Entry(self.root, width=30)
        city_entry.pack(pady=5)

        def search_realtime():
            city_name = city_entry.get()
            if not city_name:
                messagebox.showerror("Erreur", "Veuillez entrer un nom de ville.")
                return

            cities = search_city(city_name, "9c2dd9f3767f468bba40f04ea4b428ed")

            if not cities:
                messagebox.showinfo("Résultat", "Aucune ville trouvée.")
                return

            self.display_city_selection(cities, "realtime")

        tk.Button(self.root, text="Rechercher", command=search_realtime).pack(pady=10)
        tk.Button(self.root, text="Retour", command=self.main_menu).pack(pady=20)

    def forecast_menu(self):
        self._clear_widgets()

        tk.Label(self.root, text="Entrez le nom de la ville :", font=("Arial", 12)).pack(pady=5)
        city_entry = ttk.Entry(self.root, width=30)
        city_entry.pack(pady=5)

        tk.Label(self.root, text="Sélectionnez la date minimale :", font=("Arial", 12)).pack(pady=5)
        start_calendar = Calendar(self.root, date_pattern="y-mm-dd")
        start_calendar.pack(pady=5)

        tk.Label(self.root, text="Sélectionnez la date maximale :", font=("Arial", 12)).pack(pady=5)
        end_calendar = Calendar(self.root, date_pattern="y-mm-dd")
        end_calendar.pack(pady=5)

        def search_forecast():
            city_name = city_entry.get()
            start_date = start_calendar.get_date()
            end_date = end_calendar.get_date()

            if not city_name:
                messagebox.showerror("Erreur", "Veuillez entrer un nom de ville.")
                return

            cities = search_city(city_name, "9c2dd9f3767f468bba40f04ea4b428ed")

            if not cities:
                messagebox.showinfo("Résultat", "Aucune ville trouvée.")
                return

            self.display_city_selection(cities, "forecast", start_date, end_date)

        tk.Button(self.root, text="Rechercher", command=search_forecast).pack(pady=10)
        tk.Button(self.root, text="Retour", command=self.main_menu).pack(pady=20)

    def update_menu(self):
        self._clear_widgets()

        cursor = self.db_conn.cursor()
        rows = display_database(cursor)

        if not rows:
            messagebox.showinfo("Information", "La base de données est vide.")
            self.main_menu()
            return

        tk.Label(self.root, text="Contenu de la base de données :", font=("Arial", 12)).pack(pady=5)

        columns = ("ID", "Ville", "Date", "Météo", "Température", "Ressentie", "Humidité", "Vent", "Dernière MAJ")
        tree = ttk.Treeview(self.root, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)

        for row in rows:
            tree.insert("", "end", values=row)

        tree.pack(pady=5)

        tk.Label(self.root, text="Entrez un ID pour mettre à jour ou supprimer :", font=("Arial", 12)).pack(pady=5)
        id_entry = ttk.Entry(self.root, width=10)
        id_entry.pack(pady=5)

        def process_entry():
            entry_id = id_entry.get()

            if not entry_id.isdigit():
                messagebox.showerror("Erreur", "Veuillez entrer un ID valide.")
                return

            entry_id = int(entry_id)
            selected_row = next((row for row in rows if row[0] == entry_id), None)

            if not selected_row:
                messagebox.showinfo("Erreur", f"Aucun enregistrement trouvé avec ID={entry_id}.")
                return

            choice = messagebox.askquestion("Action", "Souhaitez-vous mettre à jour ou supprimer l'entrée?", icon='question')
            if choice == "yes":
                city, date = selected_row[1], selected_row[2]
                update_database_entry(self.db_conn, self.api_key, entry_id, city, date)
                messagebox.showinfo("Succès", f"Entrée mise à jour pour ID={entry_id}.")
            else:
                confirm = messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer l'entrée ID={entry_id}?")
                if confirm:
                    delete_database_entry(cursor, entry_id)
                    self.db_conn.commit()
                    messagebox.showinfo("Succès", f"Entrée supprimée pour ID={entry_id}.")

            self.update_menu()  # Rafraîchir le tableau

        tk.Button(self.root, text="Valider", command=process_entry).pack(pady=10)
        tk.Button(self.root, text="Retour", command=self.main_menu).pack(pady=20)

    def display_city_selection(self, cities, mode, start_date=None, end_date=None):
        self._clear_widgets()

        tk.Label(self.root, text="Voici les villes disponibles :", font=("Arial", 12)).pack(pady=5)

        city_var = tk.StringVar()
        for idx, city in enumerate(cities):
            city_name = f"{city['name']}, {city['country']}"
            tk.Radiobutton(self.root, text=city_name, variable=city_var, value=idx).pack(anchor=tk.W)

        def confirm_selection():
            selected_idx = city_var.get()
            if selected_idx == "":
                messagebox.showerror("Erreur", "Veuillez sélectionner une ville.")
                return

            selected_city = cities[int(selected_idx)]
            city_name = f"{selected_city['name']}, {selected_city['country']}"
            lat, lon = selected_city['lat'], selected_city['lon']

            if mode == "realtime":
                weather_data = fetch_weather_realtime(lat, lon, city_name, self.api_key, self.db_conn)
                self.display_weather_results({datetime.now().date(): weather_data})
            elif mode == "forecast":
                weather_data = fetch_weather_dates(lat, lon, city_name, start_date, end_date, self.api_key, self.db_conn)
                self.display_weather_results(weather_data)

        tk.Button(self.root, text="Confirmer", command=confirm_selection).pack(pady=10)
        tk.Button(self.root, text="Retour", command=self.main_menu).pack(pady=20)

    def display_weather_results(self, data):
        print("Données reçues dans display_weather_results :", data)

        self._clear_widgets()

        if not data:
            tk.Label(self.root, text="Aucune donnée météo disponible pour cette plage de dates.", font=("Arial", 12)).pack(pady=5)
            return

        tk.Label(self.root, text="Résultats météo :", font=("Arial", 12)).pack(pady=5)

        columns = ("Date", "Lieu", "Condition", "Température", "Ressentie", "Humidité", "Vent")
        tree = ttk.Treeview(self.root, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)

        for date, info in data.items():
            frame = tk.Frame(self.root, borderwidth=1, relief="solid", padx=5, pady=5)
            frame.pack(pady=5, fill="x")

            tk.Label(frame, text=f"Date : {date}", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w")
            tk.Label(frame, text=f"Lieu : {info.get('city', '')}", font=("Arial", 12)).grid(row=1, column=0, sticky="w")
            tk.Label(frame, text=f"Condition : {info['condition']}", font=("Arial", 12)).grid(row=2, column=0, sticky="w")
            tk.Label(frame, text=f"Température : {info['temp']}°C (Ressentie : {info['feels_like']}°C)", font=("Arial", 12)).grid(row=3, column=0, sticky="w")
            tk.Label(frame, text=f"Humidité : {info['humidity']}%", font=("Arial", 12)).grid(row=4, column=0, sticky="w")
            tk.Label(frame, text=f"Vent : {info['wind_speed']} km/h", font=("Arial", 12)).grid(row=5, column=0, sticky="w")

        tree.pack(pady=5)

        tk.Button(self.root, text="Retour", command=self.main_menu).pack(pady=20)

    def _clear_widgets(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherAppGUI(root)
    root.mainloop()
