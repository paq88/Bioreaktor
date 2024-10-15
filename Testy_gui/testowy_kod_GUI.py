import wx
import os
import time
import pandas as pd
import requests
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

class MyFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MyFrame, self).__init__(*args, **kw)
        self.file_path = "back_up_values.txt"
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        notebook = wx.Notebook(panel)

        image_urls = [
            "https://github.com/paq88/Bioreaktor/raw/main/Testy_gui/logoo.png",
            "https://github.com/paq88/Bioreaktor/raw/main/Testy_gui/logobioadd.png",
            "https://github.com/paq88/Bioreaktor/raw/main/Testy_gui/logobinf.png"
        ]

        #Zakładki
        main_tab = wx.Panel(notebook)
        second_tab = wx.Panel(notebook)
        third_tab = wx.Panel(notebook)
        fourth_tab = wx.Panel(notebook)
        fifth_tab = wx.Panel(notebook)
        six_tab = wx.Panel(notebook)
        seven_tab = wx.Panel(notebook)
        notebook.AddPage(main_tab, "Main")
        notebook.AddPage(second_tab, "Temp outside")
        notebook.AddPage(third_tab, "Temp inside")
        notebook.AddPage(fourth_tab, "PH")
        notebook.AddPage(fifth_tab, "OXYGEN")
        notebook.AddPage(six_tab, "RPM")
        notebook.AddPage(seven_tab, "Event Plot")
        
        #Layout głównej zakładki
        grid = wx.FlexGridSizer(0, 4, 10, 10)
        self.config = {
            'Temp': {'min': 0, 'max': 100, 'step': 0.01},
            'pH': {'min': 0, 'max': 14, 'step': 0.01},
            'Stirr. RPM': {'min': 0, 'max': 1000, 'step': 1},
            'Antifoam': {'min': 0, 'max': 60, 'step': 1},
            'Air RPM': {'min': 0, 'max': 100, 'step': 1},
            'Sample Signal': {'min': 0, 'max': 1000, 'step': 0.1},
        }

        self.text_controls = {}
        for label, cfg in self.config.items():
            lbl = wx.StaticText(main_tab, label=label)
            grid.Add(lbl, flag=wx.ALIGN_CENTER)

            txt = wx.TextCtrl(main_tab, value=str(0))
            grid.Add(txt, flag=wx.EXPAND)
            self.text_controls[label] = txt

            up_button = wx.Button(main_tab, label="▲")
            down_button = wx.Button(main_tab, label="▼")
            grid.Add(up_button)
            grid.Add(down_button)

            up_button.Bind(wx.EVT_BUTTON, lambda evt, lbl=label: self.change_value(evt, lbl, 1))
            down_button.Bind(wx.EVT_BUTTON, lambda evt, lbl=label: self.change_value(evt, lbl, -1))

        #Stoper
        self.start_time = 0
        self.paused_time = 0
        self.timer_running = False
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_timer, self.timer)

        main_tab.SetSizer(grid)

        #Pole tekstowe dla licznika
        self.timer_box = wx.TextCtrl(panel, style=wx.TE_READONLY | wx.TE_CENTER)
        self.timer_box.SetMinSize((80, 25))
        self.timer_box.SetValue("00:00:00")
        timer_label = wx.StaticText(panel, label="Working time:")

        #Checkbox do back upu
        self.last_values_checkbox = wx.CheckBox(panel, label="Last Values")
        self.save_values_button = wx.Button(panel, label="Save Values")
        
        self.last_values_checkbox.Bind(wx.EVT_CHECKBOX, self.load_values_from_file)
        self.save_values_button.Bind(wx.EVT_BUTTON, self.save_values_to_file)

        #Layout dla stopera
        hbox_timer = wx.BoxSizer(wx.HORIZONTAL)
        hbox_timer.AddSpacer(10)
        hbox_timer.Add(timer_label, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        hbox_timer.Add(self.timer_box, flag=wx.ALIGN_LEFT | wx.ALL, border=5)

        #Dodanie całego układu do panelu
        vbox.Add(hbox_timer, flag=wx.ALIGN_LEFT, border=10)
        vbox.Add(notebook, 1, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.last_values_checkbox, flag=wx.ALL, border=10)
        vbox.Add(self.save_values_button, flag=wx.ALL, border=10)
        

        #Okno
        self.SetTitle("Bioreaktor GUI")
        self.SetSize((600, 400))
        self.Centre()

        #Przyciski Running Signal i Stop Signal
        self.running_button = wx.Button(main_tab, label="Start / Pause", size=(120, 25))
        self.stop_button = wx.Button(main_tab, label="Stop", size=(120, 25))
        grid.Add(self.running_button, flag=wx.ALIGN_CENTER)
        grid.Add(self.stop_button, flag=wx.ALIGN_CENTER)
        
        self.running_button.Bind(wx.EVT_BUTTON, self.toggle_timer)
        self.stop_button.Bind(wx.EVT_BUTTON, self.stop_process)

        #Rysowanie wykresów u temp_outside na razie tylko
        self.load_temp_button = wx.Button(second_tab, label="Load Temperature Data")
        self.load_temp_button.Bind(wx.EVT_BUTTON, self.load_temperature_data)

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(second_tab, -1, self.figure)

        #Layout dla zakładki Temp outside
        second_vbox = wx.BoxSizer(wx.VERTICAL)
        second_vbox.Add(self.load_temp_button, flag=wx.ALL | wx.CENTER, border=5)
        second_vbox.Add(self.canvas, 1, flag=wx.EXPAND | wx.ALL)
        second_tab.SetSizer(second_vbox)

        # Layout dla zakładki Temp inside
        self.load_temp_inside_button = wx.Button(third_tab, label="Load Temp Inside Data")
        self.load_temp_inside_button.Bind(wx.EVT_BUTTON, self.load_temp_inside_data)

        self.figure_temp_inside, self.ax_temp_inside = plt.subplots()
        self.canvas_temp_inside = FigureCanvas(third_tab, -1, self.figure_temp_inside)

        third_vbox = wx.BoxSizer(wx.VERTICAL)
        third_vbox.Add(self.load_temp_inside_button, flag=wx.ALL | wx.CENTER, border=5)
        third_vbox.Add(self.canvas_temp_inside, 1, flag=wx.EXPAND | wx.ALL)
        third_tab.SetSizer(third_vbox)

        # Layout dla zakładki pH
        self.load_ph_button = wx.Button(fourth_tab, label="Load PH Data")
        self.load_ph_button.Bind(wx.EVT_BUTTON, self.load_ph_data)

        self.figure_ph, self.ax_ph = plt.subplots()
        self.canvas_ph = FigureCanvas(fourth_tab, -1, self.figure_ph)

        fourth_vbox = wx.BoxSizer(wx.VERTICAL)
        fourth_vbox.Add(self.load_ph_button, flag=wx.ALL | wx.CENTER, border=5)
        fourth_vbox.Add(self.canvas_ph, 1, flag=wx.EXPAND | wx.ALL)
        fourth_tab.SetSizer(fourth_vbox)

        # Layout dla zakładki OXYGEN
        self.load_oxygen_button = wx.Button(fifth_tab, label="Load OXYGEN Data")
        self.load_oxygen_button.Bind(wx.EVT_BUTTON, self.load_oxygen_data)

        self.figure_oxygen, self.ax_oxygen = plt.subplots()
        self.canvas_oxygen = FigureCanvas(fifth_tab, -1, self.figure_oxygen)

        fifth_vbox = wx.BoxSizer(wx.VERTICAL)
        fifth_vbox.Add(self.load_oxygen_button, flag=wx.ALL | wx.CENTER, border=5)
        fifth_vbox.Add(self.canvas_oxygen, 1, flag=wx.EXPAND | wx.ALL)
        fifth_tab.SetSizer(fifth_vbox)

        # Layout dla zakładki RPM
        self.load_rpm_button = wx.Button(six_tab, label="Load RPM Data")
        self.load_rpm_button.Bind(wx.EVT_BUTTON, self.load_rpm_data)

        self.figure_rpm, self.ax_rpm = plt.subplots()
        self.canvas_rpm = FigureCanvas(six_tab, -1, self.figure_rpm)

        six_vbox = wx.BoxSizer(wx.VERTICAL)
        six_vbox.Add(self.load_rpm_button, flag=wx.ALL | wx.CENTER, border=5)
        six_vbox.Add(self.canvas_rpm, 1, flag=wx.EXPAND | wx.ALL)
        six_tab.SetSizer(six_vbox)

        
        # Dodawanie obrazów do panelu w układzie poziomym
        hbox_images = wx.BoxSizer(wx.HORIZONTAL)  

        for url in image_urls:
            image = self.load_image_from_url(url)
            if image:
                bitmap = wx.StaticBitmap(panel, -1, image)
                hbox_images.Add(bitmap, flag=wx.ALL, border=10)

        vbox.Add(hbox_images, flag=wx.ALIGN_RIGHT | wx.ALL, border=10)

        # Ustawienie layoutu i okna
        panel.SetSizer(vbox)
        self.SetTitle("Bioreaktor GUI")
        self.SetSize((1500, 850))
        self.Centre()

    def load_image_from_url(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()  # Sprawdzamy, czy pobieranie się powiodło
            image_data = BytesIO(response.content)
            image = wx.Image(image_data).Scale(125, 125, wx.IMAGE_QUALITY_HIGH)  # Skaluje obraz
            return wx.Bitmap(image)
        except requests.RequestException as e:
            wx.MessageBox(f"Nie udało się pobrać obrazu: {e}", "Błąd", wx.OK | wx.ICON_ERROR)
            return None



    def change_value(self, event, label, direction):
        """Zmiana wartości w polu tekstowym o zadany krok."""
        cfg = self.config[label]
        step = cfg['step'] * direction
        
        #Pobranie obecnej wartości
        current_value = float(self.text_controls[label].GetValue())
        #Obliczenie nowej wartości z uwzględnieniem ograniczeń
        new_value = current_value + step
        if new_value < cfg['min']:
            new_value = cfg['min']
        elif new_value > cfg['max']:
            new_value = cfg['max']
        #Ustawienie nowej wartości w polu tekstowym
        self.text_controls[label].SetValue(str(round(new_value, 2)))

    def update_timer(self, event):
        """Aktualizuje wyświetlany czas pracy."""
        if self.timer_running:
            elapsed_time = int(time.time() - self.start_time)
            self.timer_box.SetValue(time.strftime('%H:%M:%S', time.gmtime(elapsed_time)))
        else:
            self.timer_box.SetValue(time.strftime('%H:%M:%S', time.gmtime(self.paused_time)))

    def toggle_timer(self, event):
        """Rozpoczyna lub pauzuje timer i proces."""
        if not self.timer_running:
            self.start_time = time.time() - self.paused_time  #Zachowujemy czas pauzy
            self.timer.Start(1000)  #Timer aktualizuje co sekundę
            self.timer_running = True
            wx.MessageBox("Proces został wystartowany / wznowiony.", "Informacja", wx.OK | wx.ICON_INFORMATION)
            print("Process started / resumed")
        else:
            self.paused_time = time.time() - self.start_time
            self.timer.Stop()
            self.timer_running = False
            wx.MessageBox("Proces został wstrzymany.", "Informacja", wx.OK | wx.ICON_INFORMATION)
            print("Process paused")

    def stop_process(self, event):
        """Zatrzymuje proces i resetuje timer."""
        self.timer.Stop()
        self.timer_running = False
        self.start_time = 0
        self.paused_time = 0
        self.timer_box.SetValue("00:00:00")
        wx.MessageBox("Proces został zakończony.", "Informacja", wx.OK | wx.ICON_INFORMATION)
        print("Process stopped")

    def save_values_to_file(self, event):
        """Zapisuje bieżące wartości z pól tekstowych do pliku."""
        with open(self.file_path, 'w') as f:
            for label, txt_ctrl in self.text_controls.items():
                value = txt_ctrl.GetValue()
                f.write(f"{label}:{value}\n")
        wx.MessageBox("Wartości zostały zapisane do pliku.", "Zapisano", wx.OK | wx.ICON_INFORMATION)

    def load_values_from_file(self, event):
        """Ładuje wartości z pliku do pól tekstowych, jeśli checkbox jest zaznaczony."""
        if self.last_values_checkbox.IsChecked():
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    for line in f:
                        label, value = line.strip().split(':')
                        if label in self.text_controls:
                            self.text_controls[label].SetValue(value)
                wx.MessageBox("Wartości zostały załadowane z pliku.", "Załadowano", wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox("Plik nie istnieje. Nie można załadować wartości.", "Błąd", wx.OK | wx.ICON_ERROR)

    def load_temperature_data(self, event):
        """Ładuje dane temperatury z pliku i rysuje wykres."""
        with wx.FileDialog(self, "Otwórz plik CSV", wildcard="CSV files (*.csv)|*.csv",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_OK:
                path = file_dialog.GetPath()
                self.plot_temperature_data(path)

    def plot_temperature_data(self, path):
        """Rysuje dane temperatury z wybranego pliku."""
        try:
            df = pd.read_csv(path)
            temp_outside_data = df['temp_outside']

            #Czyszczenie obecnego wykresu
            self.ax.clear()
            self.ax.plot(temp_outside_data, label='Temperatura', color='b')
            self.ax.set_title('Temperatura na zewnątrz')
            self.ax.set_xlabel('Czas')
            self.ax.set_ylabel('Temperatura (°C)')
            self.ax.legend()
            self.canvas.draw()
            wx.MessageBox("Dane temperatury załadowane i narysowane.", "Sukces", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"Błąd ładowania danych: {str(e)}", "Błąd", wx.OK | wx.ICON_ERROR)

    def load_temp_inside_data(self, event):
        with wx.FileDialog(self, "Otwórz plik CSV", wildcard="CSV files (*.csv)|*.csv",
                        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_OK:
                path = file_dialog.GetPath()
                self.plot_temp_inside_data(path)

    def plot_temp_inside_data(self, path):
        try:
            df = pd.read_csv(path)
            temp_inside_data = df['temp_inside']

            self.ax_temp_inside.clear()
            self.ax_temp_inside.plot(temp_inside_data, label='Temperatura wewnątrz', color='g')
            self.ax_temp_inside.set_title('Temperatura wewnątrz')
            self.ax_temp_inside.set_xlabel('Czas')
            self.ax_temp_inside.set_ylabel('Temperatura (°C)')
            self.ax_temp_inside.legend()
            self.canvas_temp_inside.draw()
            wx.MessageBox("Dane temperatury wewnętrznej załadowane i narysowane.", "Sukces", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"Błąd ładowania danych: {str(e)}", "Błąd", wx.OK | wx.ICON_ERROR)

    def load_ph_data(self, event):
        with wx.FileDialog(self, "Otwórz plik CSV", wildcard="CSV files (*.csv)|*.csv",
                        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_OK:
                path = file_dialog.GetPath()
                self.plot_ph_data(path)

    def plot_ph_data(self, path):
        try:
            df = pd.read_csv(path)
            ph_data = df['pH']

            self.ax_ph.clear()
            self.ax_ph.plot(ph_data, label='pH', color='r')
            self.ax_ph.set_title('pH')
            self.ax_ph.set_xlabel('Czas')
            self.ax_ph.set_ylabel('pH')
            self.ax_ph.legend()
            self.canvas_ph.draw()
            wx.MessageBox("Dane pH załadowane i narysowane.", "Sukces", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"Błąd ładowania danych: {str(e)}", "Błąd", wx.OK | wx.ICON_ERROR)

    def load_oxygen_data(self, event):
        with wx.FileDialog(self, "Otwórz plik CSV", wildcard="CSV files (*.csv)|*.csv",
                        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_OK:
                path = file_dialog.GetPath()
                self.plot_oxygen_data(path)

    def plot_oxygen_data(self, path):
        try:
            df = pd.read_csv(path)
            oxygen_data = df['OXYGEN']

            self.ax_oxygen.clear()
            self.ax_oxygen.plot(oxygen_data, label='Tlen', color='c')
            self.ax_oxygen.set_title('Tlen')
            self.ax_oxygen.set_xlabel('Czas')
            self.ax_oxygen.set_ylabel('Stężenie tlenu (%)')
            self.ax_oxygen.legend()
            self.canvas_oxygen.draw()
            wx.MessageBox("Dane stężenia tlenu załadowane i narysowane.", "Sukces", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"Błąd ładowania danych: {str(e)}", "Błąd", wx.OK | wx.ICON_ERROR)

    def load_rpm_data(self, event):
        with wx.FileDialog(self, "Otwórz plik CSV", wildcard="CSV files (*.csv)|*.csv",
                        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_OK:
                path = file_dialog.GetPath()
                self.plot_rpm_data(path)

    def plot_rpm_data(self, path):
        try:
            df = pd.read_csv(path)
            rpm_data = df['RPM']

            self.ax_rpm.clear()
            self.ax_rpm.plot(rpm_data, label='RPM', color='m')
            self.ax_rpm.set_title('RPM')
            self.ax_rpm.set_xlabel('Czas')
            self.ax_rpm.set_ylabel('Obroty na minutę (RPM)')
            self.ax_rpm.legend()
            self.canvas_rpm.draw()
            wx.MessageBox("Dane RPM załadowane i narysowane.", "Sukces", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"Błąd ładowania danych: {str(e)}", "Błąd", wx.OK | wx.ICON_ERROR)


class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None)
        frame.Show(True)
        return True

if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()
