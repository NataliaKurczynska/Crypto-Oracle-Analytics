import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime, timedelta
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


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

        # -------------------
        # Przyciski
        # -------------------
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        load_btn = ttk.Button(button_frame, text="Wczytaj dane", command=self.load_data)
        load_btn.pack(side="left", padx=10)

        predict_btn = ttk.Button(button_frame, text="Predykcja (t+1)", command=self.predict_next)
        predict_btn.pack(side="left", padx=10)

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
        self.plot_frame = ttk.Frame(parent)
        self.plot_frame.grid(row=0, column=1, sticky="nsew", padx=5)

        # matplotlib Figure
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Wykres danych")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")

        # Canvas w Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ===============================
    # Funkcja wczytywania danych
    # ===============================
    def load_data(self):
        file_path = filedialog.askopenfilename(
            title="Wybierz plik CSV",
            filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*"))
        )
        if not file_path:
            return

        df = pd.read_csv(file_path, sep=';')
        time_col = df.columns[0]
        value_col = df.columns[1]

        # ---- Aktualizacja tabeli ----
        self.table.delete(*self.table.get_children())
        for _, row in df.iterrows():
            self.table.insert("", "end", values=(row[time_col], row[value_col]))
        self.table.update()

        # ---- Aktualizacja wykresu ----
        self.ax.clear()
        self.ax.plot(df[time_col], df[value_col],
             color='blue', linestyle='-')

        self.ax.set_title("Wykres danych")
        self.ax.set_xlabel(time_col)
        self.ax.set_ylabel(value_col)
        self.ax.grid(True)
        self.canvas.draw()
        self.canvas.get_tk_widget().update()
    
    def predict_next(self):
        # Sprawdzenie, czy tabela ma dane
        if not self.table.get_children():
            tk.messagebox.showwarning("Brak danych", "Najpierw wczytaj dane!")
            return
    
        # Pobranie ostatnich wartości z tabeli
        values = [float(self.table.item(item)["values"][1]) for item in self.table.get_children()]
        last_value = values[-1]
    
        # Pobranie ostatniej daty
        last_time_str = self.table.item(self.table.get_children()[-1])["values"][0]
        last_time = datetime.strptime(last_time_str, "%d.%m.%Y")
        next_time = last_time + timedelta(days=1)
        next_time_str = next_time.strftime("%d.%m.%Y")
    
        # ===============================
        # Losowa predykcja – random walk
        # ===============================
        np.random.seed()
        delta = np.random.normal(loc=0, scale=0.5)
        predicted_value = last_value + delta
    
        # Dodanie nowego wiersza do tabeli
        self.table.insert("", "end", values=(next_time_str, round(predicted_value, 4)))
    
        # Aktualizacja wykresu
        time_col = [self.table.item(item)["values"][0] for item in self.table.get_children()]
        value_col = [float(self.table.item(item)["values"][1]) for item in self.table.get_children()]
    
        self.ax.clear()
    
        # ---- niebieska linia dla istniejących punktów ----
        if len(value_col) > 1:
            self.ax.plot(time_col[:-1], value_col[:-1], color='blue', linestyle='-')
    
        # ---- czerwona kropka dla ostatniego punktu (predykcja) ----
        self.ax.plot(time_col[-1], value_col[-1], color='red', marker='o', markersize=8)
    
        self.ax.set_title("Wykres danych")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")
        self.ax.grid(True)
        self.canvas.draw()


# ===============================
# Start aplikacji
# ===============================
if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoOracleApp(root)
    root.mainloop()
