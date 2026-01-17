# -------------------
# Import paczek
# -------------------

import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime, timedelta
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
#import pmdarima as pm #do ARIMA szacujacego p,d,q
from statsmodels.tsa.arima.model import ARIMA
import os
import matplotlib.pyplot as plt
plt.style.use("ggplot")

# -------------------
# Kod aplikacji
# -------------------
  
class CryptoOracleApp:
    def __init__(self, root):    # Konstruktor klasy: self - atrybuty stałe; root - główne okno Tkinter
        self.root = root
        self.root.title("Crypto Oracle Analytics")
        self.root.geometry("1200x650")  # Wymiar okna

        # -------------------
        # Główna ramka
        # -------------------
        main_frame = ttk.Frame(root, padding=10)  # padding = wewnętrzny margines
        main_frame.pack(fill="both", expand=True) # fill="both" = ramka rozciąga się w poziomie i pionie
                                                  #expand=True = ramka zajmuje całą dostępną przestrzeń, nawet po resize okna
        # -------------------
        # Tytuł
        # -------------------
        title = ttk.Label(
            main_frame,
            text="🔮 Crypto Oracle Analytics",
            font=("Arial", 22, "bold")
        )
        title.pack(pady=10) # Dodanie label do ramki; pady = odstęp od krawedzi

        # -------------------
        # Ramka tabela + wykres
        # -------------------
        content_frame = ttk.Frame(main_frame)         # Utworzenie ramki
        content_frame.pack(fill="both", expand=True)  # fill="both" = ramka rozciąga się w poziomie i pionie
                                                      # expand=True = ramka zajmuje całą dostępną przestrzeń, nawet po resize okna
        content_frame.columnconfigure(0, weight=1)    # Konfiguracja siatki kolumn (kolumna 0 - tabela; kolumna 1 - wykres. Tabela mniejsza od wykresu)
        content_frame.columnconfigure(1, weight=2)
        content_frame.rowconfigure(0, weight=1)       # Zostawiamy jeden wiersz siatki (nie mamy porzeby umieszczać więcej elementów)

        # -------------------
        # Tabela po lewej
        # -------------------
        self._create_table(content_frame)

        # -------------------
        # Wykres po prawej
        # -------------------
        self._create_plot(content_frame)
        self.crypto_name = "Wykres danych"  # Początkowa nazwa nad wykresem (zostanie zaktualizowana nazwą kryptowaluty)

        # -------------------
        # Przyciski i Entry
        # -------------------
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        load_btn = ttk.Button(button_frame, text="Wczytaj dane", command=self.load_data) # po nacinięciu uruchamia laod_data()
        load_btn.pack(side="left", padx=10)  #pozycjonowanie przycisku
        
        predict_btn = ttk.Button(button_frame, text="Predykcja (t+1)", command=self.predict_next) # po nacinięciu uruchamia predict_next()
        predict_btn.pack(side="left", padx=10)  #pozycjonowanie przycisku
        
        self.predicted = 0  # licznik predykcji

        window_label = ttk.Label(button_frame, text="Ile ostatnich punktów na wykresie:") # Dodanie napisu w polu przycisków
        window_label.pack(side="left", padx=5)  #pozycjonowanie tekstu

        self.window_entry = ttk.Entry(button_frame, width=6)  # dodane miejsca na wpisanie liczby
        self.window_entry.insert(0, "200")  # 200 - domyślna wartość
        self.window_entry.pack(side="left", padx=5)
        
        refresh_btn = ttk.Button(button_frame, text="Odśwież wykres", command=self.refresh_plot)  # po nacinięciu uruchamia refresh_plot()
        refresh_btn.pack(side="left", padx=10)  #pozycjonowanie przycisku
        
        
    # ===============================
    # Funkcja tworząca tabelę
    # ===============================
    def _create_table(self, parent):
        table_frame = ttk.Frame(parent) # parent -> content_frame(); tworzymy tabele w naszym oknie content_frame()
        table_frame.grid(row=0, column=0, sticky="nsew", padx=5) # frame grid rozciąga się w kierunkach nsew i znajduje sie w 1 kolumnie i 1 wierszu siatki aplikacji 

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical")
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal")

        self.table = ttk.Treeview(
            table_frame,                # tabela wewnatrz table_frame
            columns=("Time", "Value"),  # ID kolumna,  nie nazwy
            show="headings",            # chowa kolumne #0
            yscrollcommand=scroll_y.set,# podpięcie scrollbarów do tabeli
            xscrollcommand=scroll_x.set)

        self.table.heading("Time", text="Time")     # nazwanie kolumny z ID 'Time' jako 'Time'
        self.table.heading("Value", text="Value")
        self.table.column("Time", width=150)
        self.table.column("Value", width=100)

        scroll_y.config(command=self.table.yview)
        scroll_x.config(command=self.table.xview)

        self.table.grid(row=0, column=0, sticky="nsew")  # ustawnie elementów w siatce i okrelenie kierunków dostosowania przy resize
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)    # pozwala tabeli rozciągać się pionowo przy zmianie rozmiaru okna
        table_frame.columnconfigure(0, weight=1) # pozwala tabeli rozciągać się poziomo przy zmianie rozmiaru okna

    # ===============================
    # Funkcja tworząca wykres
    # ===============================
    def _create_plot(self, parent):
        plt.style.use("ggplot")
        self.plot_frame = ttk.Frame(parent)
        self.plot_frame.grid(row=0, column=1, sticky="nsew", padx=5) # frame grid rozciąga się w kierunkach nsew i znajduje sie w 2 kolumnie i 1 wierszu siatki aplikacji

        self.fig = Figure(figsize=(5, 4), dpi=100) # tworzy obiekt wykresu (rozmiar + jakość)
        self.ax = self.fig.add_subplot(111) # dodaje jedną oś (1x1, pierwszy wykres)
        self.ax.set_title("Wykres danych")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
            # Łączy wykres matplotlib (self.fig) z Tkinterem i osadza go w ramce plot_frame
        self.canvas.draw()
            # Rysuje wykres (pierwsze renderowanie figury)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
            # Pobiera widget (obiekt z wykresem) Tkintera z canvasu i rozciąga go na całą dostępną przestrzeń

    # ===============================
    # Wczytywanie danych
    # ===============================
    def load_data(self):
        file_path = filedialog.askopenfilename(
            title="Wybierz plik CSV",    # tytuł okna wyboru pliku
            filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*"))
        )
        if not file_path:
            return  # jeśli użytkownik kliknie "Anuluj" (czyli nie wybierze pliku), przerywamy funkcję
        
        self.crypto_name = os.path.splitext(os.path.basename(file_path))[0]  # bierze nazwę pliku bez rozszerzenia i zapisuje ją w self.crypto_name

        df = pd.read_csv(file_path, sep=';')
        time_col = df.columns[0]
        value_col = df.columns[1]

        # ---- aktualizacja tabeli ----
        self.table.delete(*self.table.get_children()) # czysci tabele
        for _, row in df.iterrows():  
            # iterujemy po wszystkich wierszach DataFrame (index ignorujemy, bierzemy tylko row)
            self.table.insert("", "end", values=(row[time_col], row[value_col]))  
                # dodajemy nowy wiersz do tabeli Treeview
                # "" -> brak rodzica (najwyższy poziom w drzewie danych; u nas wszystkie wiersze nie maja rodzicow)
                # "end" -> wstaw na końcu tabeli
                # values=() -> wartości kolumn w tym wierszu (czas i wartość)
        self.table.update() # wymusza natychmiastowe odświeżenie widoku w GUI
        
        # ---- reset predykcji ----
        self.predicted = 0
        
        # ---- odśwież wykres ----
        self.refresh_plot()
        
    # ===============================
    # Predykcja
    # ===============================
    
    def predict(self):
        # pobieramy wszystkie wartości z kolumny "Value" tabeli i zamieniamy na float
        values = [float(self.table.item(item)["values"][1]) 
              for item in self.table.get_children()]

        # minimalna liczba obserwacji potrzebna do modelu ARIMA
        if len(values) < 20:
            return values[-1]  # jeśli za mało danych, zwracamy ostatnią wartość

        series = pd.Series(values)  # zamieniamy listę wartości na pandas Series (wymagane przez ARIMA)

        try:
            # tworzymy model ARIMA z parametrami (p=5, d=1, q=0)
            model = ARIMA(series, order=(5, 1, 0))
            model_fit = model.fit()                 # dopasowujemy model do danych

            forecast = model_fit.forecast(steps=1)  # prognoza na 1 krok do przodu
            predicted_value = forecast.iloc[0]      # pobieramy prognozowaną wartość

            return predicted_value

        except Exception as e:
            # jeśli coś pójdzie nie tak (np. brak danych, problem z dopasowaniem), zwracamy ostatnią wartość
            print("Błąd ARIMA:", e)
            return values[-1]
        
    
    def predict_next(self):
        # sprawdzenie, czy tabela nie jest pusta
        if not self.table.get_children():
            tk.messagebox.showwarning("Brak danych", "Najpierw wczytaj dane!")
            return
        
        last_time_str = self.table.item(self.table.get_children()[-1])["values"][0]  # pobranie ostatniej daty z tabeli
        last_time = datetime.strptime(last_time_str, "%d.%m.%Y")
        next_time = last_time + timedelta(days=1)     # dodajemy 1 dzień
        next_time_str = next_time.strftime("%d.%m.%Y")

        self.table.insert("", "end", values=(next_time_str, round(self.predict(), 4))) # wstawienie daty i prognozowanej wartości
        self.predicted += 1

        # ---- odśwież wykres po predykcji ----
        self.refresh_plot()

    # ===============================
    # Odśwież wykres
    # ===============================
    def refresh_plot(self):
        # jeśli tabela jest pusta, nie rysujemy nic
        if not self.table.get_children():
            return
        
        # pobranie liczby punktów do wyświetlenia z Entry
        try:
            window_size = int(self.window_entry.get())
            if window_size < 10:
                window_size = 10
        except ValueError:
            window_size = 200  # jeśli wpisano coś nieprawidłowego ustawiamy 200
            
        # pobieramy wszystkie wartości z tabeli
        time_col = [self.table.item(item)["values"][0] for item in self.table.get_children()]
        value_col = [float(self.table.item(item)["values"][1]) for item in self.table.get_children()]

        # wybieramy tylko ostatnie 'window_size' punktów, jeśli mamy ich więcej
        time_window = time_col[-window_size:] if len(time_col) > window_size else time_col
        value_window = value_col[-window_size:] if len(value_col) > window_size else value_col
        
        # czyścimy aktualny wykres
        self.ax.clear()
        
        # konwertujemy stringi dat na obiekty datetime dla Matplotlib
        dates_window = [datetime.strptime(d, "%d.%m.%Y") for d in time_window]
        
        # obliczamy ile punktów to dane oryginalne (niepredykcyjne)
        original_len = len(dates_window) - min(self.predicted, len(dates_window))
        # rysujemy niebieską linię dla danych oryginalnych
        if original_len > 0:
            self.ax.plot(dates_window[:original_len], value_window[:original_len], color='blue', linestyle='-')

        if self.predicted > 0:
            # ---- ostatnia data i wartość predykcji ----
            pred_date = dates_window[-1]
            pred_value = value_window[-1]
            
            # ---- tekst do wyświetlenia przy predykcji ----
            label = f"Predykcja \n{pred_value:.4f}"

            # ---- dodanie adnotacji z wartością predykcji ----
            self.ax.annotate(
                label,                           # tekst adnotacji
                xy=(pred_date, pred_value),      # punkt, do którego strzałka będzie wskazywać
                xytext=(15, 15),                 # przesunięcie tekstu względem punktu
                textcoords="offset points",      # mówi Matplotlib, że przesunięcie (15, 15) jest w punktach (points), a nie np. w jednostkach danych osi X/Y
                bbox=dict(                       # obramowanie tekstu
                    boxstyle="round,pad=0.4",
                    fc="lightyellow",            # kolor tła
                    ec="red",                    # kolor obramowania
                    lw=1
                    ),
                arrowprops=dict(                 # strzałka wskazująca punkt
                    arrowstyle="->",
                    color="red"
                    ),
                fontsize=9                       # rozmiar czcionki
                )
            

            # ---- czerwone kropki dla wszystkich predykcji (bez łączenia z poprzednią linią) ----
            self.ax.plot(dates_window[original_len:], value_window[original_len:], color='red', marker='o', markersize=6, linestyle='')
            # ---- linia łącząca ostatni punkt danych oryginalnych z pierwszą predykcją ----
            self.ax.plot(dates_window[original_len-1:], value_window[original_len-1:], color='red', marker='', markersize=6, linestyle='-')

        # ---- reszta wykresu ----
        self.ax.set_title(f"{self.crypto_name}")  # tytuł wykresu
        self.ax.set_xlabel("Time")                # etykieta osi X
        self.ax.set_ylabel("Value")               # etykieta osi Y
        self.ax.grid(True)

        self.ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))  # Ustawia, co ile mają być główne ticki na osi X (daty)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))  # Formatuje etykiety ticków, czyli jak będą wyglądać daty na osi X.
        self.fig.autofmt_xdate(rotation=45)                               # Automatycznie obraca i dopasowuje etykiety osi X, żeby się nie nakładały.

        self.canvas.draw()  # Odświeża Tkinterowy widget wykresu, żeby pokazał wszystkie zmiany


# ===============================
# Start aplikacji
# ===============================
if __name__ == "__main__":      # Sprawdza, czy ten plik jest uruchamiany bezpośrednio, a nie importowany jako moduł.
    root = tk.Tk()              # Tworzy główne okno Tkinter.
    app = CryptoOracleApp(root) # Utworzenie obiektu (odpala się __init__)
    root.mainloop()             # Uruchamia pętlę główną Tkinter.
