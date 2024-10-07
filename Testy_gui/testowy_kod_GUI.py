import wx
import os
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

class MyFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MyFrame, self).__init__(*args, **kw)
        self.file_path = "back_up_values.txt"
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        notebook = wx.Notebook(panel)
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
        panel.SetSizer(vbox)

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
            data = []
            with open(path, 'r') as file:
                for line in file:
                    data.append(float(line.strip()))
            #Czyszczenie obecnego wykresu
            self.ax.clear()
            self.ax.plot(data, label='Temperatura', color='b')
            self.ax.set_title('Temperatura na zewnątrz')
            self.ax.set_xlabel('Czas')
            self.ax.set_ylabel('Temperatura (°C)')
            self.ax.legend()
            self.canvas.draw()
            wx.MessageBox("Dane temperatury załadowane i narysowane.", "Sukces", wx.OK | wx.ICON_INFORMATION)
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
