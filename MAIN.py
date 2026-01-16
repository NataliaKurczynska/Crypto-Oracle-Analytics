import numpy as np
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

class CryptoOracleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Crypto Oracle Analytics")
        self.root.geometry("1200x650")

        # -------------------
        # Główna ramka
        # -------------------
        main_frame = ttk.Frame(root, padding=10)
        main_frame.pack(fill="both", expand=True)

        # -------------------
        # Tytuł
        # -------------------
        title = ttk.Label(
            main_frame,
            text="🔮 Crypto Oracle Analytics",
            font=("Arial", 22, "bold")
        )
        title.pack(pady=10)

        # -------------------
        # Ramka tabela + wykres
        # -------------------
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True)
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=2)
        content_frame.rowconfigure(0, weight=1)

        # -------------------
        # Tabela po lewej
        # -------------------
        self._create_table(content_frame)

        # -------------------
        # Wykres po prawej
        # -------------------
        self._create_plot(content_frame)
        self.crypto_name = "Wykres danych"

        # -------------------
        # Przyciski i Entry
        # -------------------
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        load_btn = ttk.Button(button_frame, text="Wczytaj dane", command=self.load_data)
        load_btn.pack(side="left", padx=10)
        
        predict_btn = ttk.Button(button_frame, text="Predykcja (t+1)", command=self.predict_next)
        predict_btn.pack(side="left", padx=10)
        
        self.predicted = 0  # licznik predykcji

        window_label = ttk.Label(button_frame, text="Ile ostatnich punktów na wykresie:")
        window_label.pack(side="left", padx=5)

        self.window_entry = ttk.Entry(button_frame, width=6)
        self.window_entry.insert(0, "200")  # domyślna wartość
        self.window_entry.pack(side="left", padx=5)
        
        refresh_btn = ttk.Button(button_frame, text="Odśwież wykres", command=self.refresh_plot)
        refresh_btn.pack(side="left", padx=10)
        
        
    # ===============================
    # Funkcja tworząca tabelę
    # ===============================
    def _create_table(self, parent):
        table_frame = ttk.Frame(parent)
        table_frame.grid(row=0, column=0, sticky="nsew", padx=5)

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical")
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal")

        self.table = ttk.Treeview(
            table_frame,
            columns=("Time", "Value"),
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        self.table.heading("Time", text="Time")
        self.table.heading("Value", text="Value")
        self.table.column("Time", width=150)
        self.table.column("Value", width=100)

        scroll_y.config(command=self.table.yview)
        scroll_x.config(command=self.table.xview)

        self.table.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

    # ===============================
    # Funkcja tworząca wykres
    # ===============================
    def _create_plot(self, parent):
        plt.style.use("ggplot")
        self.plot_frame = ttk.Frame(parent)
        self.plot_frame.grid(row=0, column=1, sticky="nsew", padx=5)

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Wykres danych")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ===============================
    # Wczytywanie danych
    # ===============================
    def load_data(self):
        file_path = filedialog.askopenfilename(
            title="Wybierz plik CSV",
            filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*"))
        )
        if not file_path:
            return
        
        self.crypto_name = os.path.splitext(os.path.basename(file_path))[0]

        df = pd.read_csv(file_path, sep=';')
        time_col = df.columns[0]
        value_col = df.columns[1]

        # ---- aktualizacja tabeli ----
        self.table.delete(*self.table.get_children())
        for _, row in df.iterrows():
            self.table.insert("", "end", values=(row[time_col], row[value_col]))
        self.table.update()
        
        # ---- reset predykcji ----
        self.predicted = 0
        
        # ---- odśwież wykres ----
        self.refresh_plot()
        
    # ===============================
    # Predykcja
    # ===============================
    
    def predict(self):
        values = [float(self.table.item(item)["values"][1]) 
              for item in self.table.get_children()]

        # minimalna liczba obserwacji
        if len(values) < 20:
            return values[-1]

        series = pd.Series(values)

        try:
            model = ARIMA(series, order=(5, 1, 0))
            model_fit = model.fit()

            forecast = model_fit.forecast(steps=1)
            predicted_value = forecast.iloc[0]

            return predicted_value

        except Exception as e:
            print("Błąd ARIMA:", e)
            return values[-1]
        
    
    def predict_next(self):
        if not self.table.get_children():
            tk.messagebox.showwarning("Brak danych", "Najpierw wczytaj dane!")
            return

        last_time_str = self.table.item(self.table.get_children()[-1])["values"][0]
        last_time = datetime.strptime(last_time_str, "%d.%m.%Y")
        next_time = last_time + timedelta(days=1)
        next_time_str = next_time.strftime("%d.%m.%Y")

        self.table.insert("", "end", values=(next_time_str, round(self.predict(), 4)))
        self.predicted += 1

        # ---- odśwież wykres po predykcji ----
        self.refresh_plot()

    # ===============================
    # Odśwież wykres
    # ===============================
    def refresh_plot(self):
        if not self.table.get_children():
            return

        try:
            window_size = int(self.window_entry.get())
            if window_size < 10:
                window_size = 10
        except ValueError:
            window_size = 200

        time_col = [self.table.item(item)["values"][0] for item in self.table.get_children()]
        value_col = [float(self.table.item(item)["values"][1]) for item in self.table.get_children()]

        time_window = time_col[-window_size:] if len(time_col) > window_size else time_col
        value_window = value_col[-window_size:] if len(value_col) > window_size else value_col

        self.ax.clear()
        dates_window = [datetime.strptime(d, "%d.%m.%Y") for d in time_window]

        original_len = len(dates_window) - min(self.predicted, len(dates_window))
        if original_len > 0:
            self.ax.plot(dates_window[:original_len], value_window[:original_len], color='blue', linestyle='-')

        if self.predicted > 0:
            pred_date = dates_window[-1]
            pred_value = value_window[-1]

            label = f"Predykcja \n{pred_value:.4f}"

            self.ax.annotate(
                label,
                xy=(pred_date, pred_value),
                xytext=(15, 15),                # przesunięcie tekstu
                textcoords="offset points",
                bbox=dict(
                    boxstyle="round,pad=0.4",
                    fc="#cbe7ff",
                    ec="red",
                    lw=1
                    ),
                arrowprops=dict(
                    arrowstyle="->",
                    color="red"
                    ),
                fontsize=9
                )
            
            self.ax.plot(dates_window[original_len:], value_window[original_len:], color='red', marker='o', markersize=6, linestyle='')
            self.ax.plot(dates_window[original_len-1:], value_window[original_len-1:], color='red', marker='', markersize=6, linestyle='-')

        self.ax.set_title(f"{self.crypto_name}")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")
        self.ax.grid(True)

        self.ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        self.fig.autofmt_xdate(rotation=45)

        self.canvas.draw()


# ===============================
# Start aplikacji
# ===============================
if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoOracleApp(root)
    root.mainloop()
