#!/usr/bin/python3

import wx
import os
import time
import pandas as pd
import requests
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from comms import start_read_thread, write_thread, stop_write_thread, update_params, pause_write_thread, resume_write_thread, start_session, send_sample_signals, send_antifoam_signal


class MyFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MyFrame, self).__init__(*args, **kw)
        self.file_path = "back_up_values.txt"
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        notebook = wx.Notebook(panel)


        #Zakładki
        main_tab = wx.Panel(notebook)
        readings = wx.Panel(notebook)
        second_tab = wx.Panel(notebook)
        third_tab = wx.Panel(notebook)
        fourth_tab = wx.Panel(notebook)
        fifth_tab = wx.Panel(notebook)
        six_tab = wx.Panel(notebook)
        seven_tab = wx.Panel(notebook)
        notebook.AddPage(main_tab, "Controls")
        notebook.AddPage(readings, "Readings")
        notebook.AddPage(second_tab, "Temp outside")
        notebook.AddPage(third_tab, "Temp inside")
        notebook.AddPage(fourth_tab, "PH")
        notebook.AddPage(fifth_tab, "OXYGEN")
        notebook.AddPage(six_tab, "RPM")
        notebook.AddPage(seven_tab, "Event Plot")
        
        #Layout głównej zakładki
        grid_main = wx.FlexGridSizer(9, 4, 10, 10)
        self.config = {
            'Temp': {'min': 0, 'max': 100, 'step': 1},
            'pH': {'min': 0, 'max': 14, 'step': 0.1},
            'Stirr. RPM': {'min': 0, 'max': 1000, 'step': 1},
            'Air RPM': {'min': 0, 'max': 255, 'step': 1}
        }
        
        self.readings_params = {'Temp. inside' : {0},
                                'Temp. outside': {0},
                                'pH': {0},
                                'Stirr. RPM': {0},
                                'Air RPM': {0}
        }


        self.text_controls = {}
        for label, cfg in self.config.items():
            if label == "Stirr. RPM":
                lbl = wx.StaticText(main_tab, label=label)
                grid_main.Add(lbl, flag=wx.ALIGN_CENTER)

                stir_rpm_choices = [400, 800, 1200, 1600, 2000]
                self.stir_rpm_choice = wx.Choice(main_tab, choices=[str(x) for x in stir_rpm_choices])
                self.stir_rpm_choice.SetSelection(0)
                grid_main.Add(self.stir_rpm_choice, flag=wx.EXPAND)

                self.stir_rpm_choice.Bind(wx.EVT_CHOICE, self.stir_on_rpm_choice)
                
            elif label == 'Air RPM':
                lbl = wx.StaticText(main_tab, label=label)
                grid_main.Add(lbl, flag=wx.ALIGN_CENTER)

                air_rpm_choices = [400, 800, 1200, 1600, 2000]
                self.air_rpm_choice = wx.Choice(main_tab, choices=[str(x) for x in air_rpm_choices])
                self.air_rpm_choice.SetSelection(0)
                grid_main.Add(self.air_rpm_choice, flag=wx.EXPAND)

                self.air_rpm_choice.Bind(wx.EVT_CHOICE, self.air_on_rpm_choice)

            else:
                lbl = wx.StaticText(main_tab, label=label)
                grid_main.Add(lbl, flag=wx.ALIGN_CENTER)

                txt = wx.TextCtrl(main_tab, value=str(0))
                grid_main.Add(txt, flag=wx.EXPAND)
                self.text_controls[label] = txt

                up_button = wx.Button(main_tab, label="▲")
                down_button = wx.Button(main_tab, label="▼")
                grid_main.Add(up_button)
                grid_main.Add(down_button)

                up_button.Bind(wx.EVT_BUTTON, lambda evt, lbl=label: self.change_value(evt, lbl, 1))
                down_button.Bind(wx.EVT_BUTTON, lambda evt, lbl=label: self.change_value(evt, lbl, -1))

        grid_readings = wx.FlexGridSizer(6, 2, 10, 10)
        self.text_readings = {}
        for label, cfg in self.readings_params.items():
            lbl = wx.StaticText(readings, label=label)
            grid_readings.Add(lbl, flag=wx.ALIGN_CENTER)
            
            txt = wx.TextCtrl(readings, value=str(0))
            grid_readings.Add(txt, flag=wx.EXPAND)
            self.readings_params[label] = txt
    
        readings.SetSizer(grid_readings)
        
        #Stoper
        self.start_time = 0
        self.paused_time = 0
        self.timer_running = False
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_timer, self.timer)

        main_tab.SetSizer(grid_main)

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

        #Antifoam and Draw Sample buttons
        self.antifoam = wx.Button(main_tab, label="Anti Foam", size=(120,25))
        self.drawsample = wx.Button(main_tab, label="Draw Sample", size=(120,25))
        grid_main.Add(self.antifoam, flag=wx.ALIGN_CENTER)
        grid_main.Add(self.drawsample, flag=wx.ALIGN_CENTER)
        
        #Przyciski Running Signal i Stop Signal
        self.drawsample.Bind(wx.EVT_BUTTON, self.draw_sample)
        self.antifoam.Bind(wx.EVT_BUTTON, self.antifoam_action)
        self.running_button = wx.Button(main_tab, label="Start", size=(120, 25))
        self.stop_button = wx.Button(main_tab, label="Stop", size=(120, 25))
        grid_main.Add(self.running_button, flag=wx.ALIGN_CENTER)
        grid_main.Add(self.stop_button, flag=wx.ALIGN_CENTER)
        
        self.running_button.Bind(wx.EVT_BUTTON, self.on_start_pause)
        self.stop_button.Bind(wx.EVT_BUTTON, self.on_stop)
        self.is_paused = True

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

        

        # Ustawienie layoutu i okna
        panel.SetSizer(vbox)
        self.SetTitle("Bioreaktor GUI")
        self.SetSize((1500, 850))
        self.Centre()

    def stir_on_rpm_choice(self, event):
        """Aktualizuje wartość Stirr. RPM na podstawie wyboru z listy rozwijanej."""
        selected_value = int(self.stir_rpm_choice.GetString(self.stir_rpm_choice.GetSelection()))
        self.text_controls['Stirr. RPM'] = selected_value
        self.update_params_from_gui()
        
    def air_on_rpm_choice(self, event):
        """Aktualizuje wartość Air RPM na podstawie wyboru z listy rozwijanej."""
        selected_value = int(self.air_rpm_choice.GetString(self.air_rpm_choice.GetSelection()))
        self.text_controls['Air RPM'] = selected_value
        self.update_params_from_gui()

    def change_value(self, event, label, direction):
        """Change the value in the text field and update the global params."""
        cfg = self.config[label]
        step = cfg['step'] * direction
        
        current_value = float(self.text_controls[label].GetValue())
        
        new_value = current_value + step
        if new_value < cfg['min']:
            new_value = cfg['min']
        elif new_value > cfg['max']:
            new_value = cfg['max']
        
        self.text_controls[label].SetValue(str(round(new_value, 2)))
        self.update_params_from_gui()

    def update_params_from_gui(self):
        """Update global parameters which are then sent to Arduino"""
        params = {
            "temp": float(self.text_controls['Temp'].GetValue()),
            "pH": float(self.text_controls['pH'].GetValue()),
            "Stirr_RPM": int(self.stir_rpm_choice.GetString(self.stir_rpm_choice.GetSelection())),
            "Air_RPM": int(self.air_rpm_choice.GetString(self.air_rpm_choice.GetSelection())),
        }
        update_params(params)

    def update_timer(self, event):
        """Aktualizuje wyświetlany czas pracy."""
        if self.timer_running:
            elapsed_time = int(time.time() - self.start_time)
            self.timer_box.SetValue(time.strftime('%H:%M:%S', time.gmtime(elapsed_time)))
        else:
            self.timer_box.SetValue(time.strftime('%H:%M:%S', time.gmtime(self.paused_time)))
    
    def draw_sample(self, event):
        send_sample_signals()
        
    def antifoam_action(self, event):
        send_antifoam_signal()

       
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
        stop_write_thread()
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
            
    def on_start_pause(self, event):
        if self.is_paused:
            if self.running_button.GetLabel() == "Start":
                start_session()
                self.update_params_from_gui() 
                write_thread() 
                start_read_thread(self.update_gui_with_data)
            else:
                resume_write_thread() 

            self.toggle_timer(wx.EVT_BUTTON) 
            self.running_button.SetLabel("Pause") 
            self.is_paused = False
        else:
            pause_write_thread()
            self.toggle_timer(wx.EVT_BUTTON)
            self.running_button.SetLabel("Resume")
            self.is_paused = True
        
    def on_stop(self, event):
        self.stop_process(wx.EVT_BUTTON)
        stop_write_thread()
        self.running_button.SetLabel("Start")
        self.is_paused = True

    def update_gui_with_data(self, data):
        wx.CallAfter(self.readings_params['Temp. inside'].SetValue, str(data['temp_inside']))
        wx.CallAfter(self.readings_params['Temp. outside'].SetValue, str(data['temp_outside']))
        wx.CallAfter(self.readings_params['pH'].SetValue, str(data['ph']))
        wx.CallAfter(self.readings_params['Stirr. RPM'].SetValue, str(data['stirr_rpm']))
        wx.CallAfter(self.readings_params['Air RPM'].SetValue, str(data['air_rpm']))
        


class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None)
        frame.Show(True)
        return True

if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()
