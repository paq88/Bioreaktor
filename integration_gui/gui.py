#!/usr/bin/python3

import wx
import time
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from comms import start_read_thread, write_thread, stop_write_thread, update_params, pause_write_thread, resume_write_thread, start_session, send_sample_signals, send_antifoam_signal, temp_inside_list, temp_outside_list, oxygen_list, ph_list, read_logs, update_working_time, update_cycle_time, save_plots, compare_ph_values


class MyFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MyFrame, self).__init__(*args, **kw)
        font = wx.Font(14,wx.NORMAL, wx.NORMAL,  wx.NORMAL)
        panel = wx.Panel(self)
        panel.SetFont(font)
        vbox = wx.BoxSizer(wx.VERTICAL)
        notebook = wx.Notebook(panel)
        self.ShowFullScreen(True)


        # Tabs declaration
        main_tab = wx.Panel(notebook)
        readings = wx.Panel(notebook)
        temp_plot_tab = wx.Panel(notebook)
        ph_plot_tab = wx.Panel(notebook)
        oxygen_plot_tab = wx.Panel(notebook)
        events_tab = wx.Panel(notebook)
        
        notebook.AddPage(main_tab, "Controls")
        notebook.AddPage(readings, "Readings")
        notebook.AddPage(temp_plot_tab, "Temperature")
        notebook.AddPage(ph_plot_tab, "pH")
        notebook.AddPage(oxygen_plot_tab, "Oxygen levels")
        notebook.AddPage(events_tab, "Event log")
        
        # Main window layout
        grid_main = wx.FlexGridSizer(9, 4, 10, 10)
        
        # Declare input and output params
        self.config = {
            'Temp': {'min': 0, 'max': 100, 'step': 1},
            'pH': {'min': 0, 'max': 14, 'step': 0.1},
            'Stirr. RPM': {'min': 0, 'max': 1000, 'step': 1},
            'Air RPM': {'min': 0, 'max': 255, 'step': 1}
        }
        
        self.readings_params = {'Temp. inside' : {0},
                                'Temp. outside': {0},
                                'pH': {0},
                                'Oxygen level': {0}
        }


        self.text_controls = {}
        
        # Create objects in main tab
        for label, cfg in self.config.items():
            if label == "Stirr. RPM":
                lbl = wx.StaticText(main_tab, label=label)
                lbl.SetFont(font)
                grid_main.Add(lbl, flag=wx.ALIGN_CENTER)

                stir_rpm_choices = [0, 100, 255]
                self.stir_rpm_choice = wx.Choice(main_tab, choices=[str(x) for x in stir_rpm_choices])
                self.stir_rpm_choice.SetSelection(0)
                self.stir_rpm_choice.SetFont(font)
                grid_main.Add(self.stir_rpm_choice, flag=wx.EXPAND)

                self.stir_rpm_choice.Bind(wx.EVT_CHOICE, self.stir_on_rpm_choice)
                
            elif label == 'Air RPM':
                lbl = wx.StaticText(main_tab, label=label)
                lbl.SetFont(font)
                grid_main.Add(lbl, flag=wx.ALIGN_CENTER)

                air_rpm_choices = [0, 100, 255]
                self.air_rpm_choice = wx.Choice(main_tab, choices=[str(x) for x in air_rpm_choices])
                self.air_rpm_choice.SetSelection(0)
                self.air_rpm_choice.SetFont(font)
                grid_main.Add(self.air_rpm_choice, flag=wx.EXPAND)

                self.air_rpm_choice.Bind(wx.EVT_CHOICE, self.air_on_rpm_choice)

            else:
                lbl = wx.StaticText(main_tab, label=label)
                lbl.SetFont(font)
                grid_main.Add(lbl, flag=wx.ALIGN_CENTER)

                txt = wx.TextCtrl(main_tab, style=wx.TE_CENTER, value=str(0), size=(120,120))
                txt.SetFont(font)
                grid_main.Add(txt, flag=wx.ALIGN_LEFT)
                self.text_controls[label] = txt

                up_button = wx.Button(main_tab, label="▲", size=(120,120))
                down_button = wx.Button(main_tab, label="▼", size=(120,120))
                up_button.SetFont(font)
                down_button.SetFont(font)
                grid_main.Add(up_button)
                grid_main.Add(down_button)

                up_button.Bind(wx.EVT_BUTTON, lambda evt, lbl=label: self.change_value(evt, lbl, 1))
                down_button.Bind(wx.EVT_BUTTON, lambda evt, lbl=label: self.change_value(evt, lbl, -1))

        main_tab.SetSizer(grid_main)
        
        # Create layout in readings tab
        grid_readings = wx.BoxSizer(wx.VERTICAL)
        self.text_readings = {}
        for label, cfg in self.readings_params.items():
            lbl = wx.StaticText(readings, label=label)
            lbl.SetFont(font)
            grid_readings.Add(lbl, flag=wx.EXPAND | wx.ALL, border=20)
            
            txt = wx.TextCtrl(readings, style=wx.TE_READONLY, value=str(0))
            txt.SetFont(font)
            grid_readings.Add(txt, flag=wx.EXPAND | wx.ALL, border=0)
            self.readings_params[label] = txt
    
        readings.SetSizer(grid_readings)
        grid_readings.Fit(self)
        
        #Timer
        self.countdown_time = 0
        self.countdown_paused = False
        self.countdown_running = False
        self.countdown_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_countdown_timer, self.countdown_timer)

        #Stopwatch
        self.start_time = 0
        self.paused_time = 0
        self.timer_running = False
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_timer, self.timer)

        countdown_label = wx.StaticText(panel, label="Cycle time:")
        countdown_label.SetFont(font)
        self.countdown_input = wx.TextCtrl(panel, value="00:00:20", style=wx.TE_CENTER, size=(120,50))
        self.countdown_input.SetFont(font)

        self.button_d_plus = wx.Button(panel, label="D+", size=(50,50))
        self.button_d_minus = wx.Button(panel, label="D-", size=(50,50))
        self.button_h_plus = wx.Button(panel, label="H+", size=(50,50))
        self.button_h_minus = wx.Button(panel, label="H-", size=(50,50))
        self.button_m_plus = wx.Button(panel, label="M+", size=(50,50))
        self.button_m_minus = wx.Button(panel, label="M-", size=(50,50))
        self.button_s_plus = wx.Button(panel, label="S+", size=(50,50))
        self.button_s_minus = wx.Button(panel, label="S-", size=(50,50))

        # Bind button events to functions
        self.button_d_plus.Bind(wx.EVT_BUTTON, self.on_d_plus)
        self.button_d_minus.Bind(wx.EVT_BUTTON, self.on_d_minus)
        self.button_h_plus.Bind(wx.EVT_BUTTON, self.on_h_plus)
        self.button_h_minus.Bind(wx.EVT_BUTTON, self.on_h_minus)
        self.button_m_plus.Bind(wx.EVT_BUTTON, self.on_m_plus)
        self.button_m_minus.Bind(wx.EVT_BUTTON, self.on_m_minus)
        self.button_s_plus.Bind(wx.EVT_BUTTON, self.on_s_plus)
        self.button_s_minus.Bind(wx.EVT_BUTTON, self.on_s_minus)
        
        # Set fonts for buttons
        self.button_d_plus.SetFont(font)
        self.button_d_minus.SetFont(font)
        self.button_h_plus.SetFont(font)
        self.button_h_minus.SetFont(font)
        self.button_m_plus.SetFont(font)
        self.button_m_minus.SetFont(font)
        self.button_s_plus.SetFont(font)
        self.button_s_minus.SetFont(font)
        
        # Layout for timer
        hbox_countdown = wx.BoxSizer(wx.HORIZONTAL)
        hbox_countdown.AddSpacer(10)
        hbox_countdown.Add(countdown_label, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        hbox_countdown.Add(self.countdown_input, flag=wx.ALL, border=5)
        hbox_countdown.Add(self.button_d_plus, flag=wx.ALL, border=5)
        hbox_countdown.Add(self.button_d_minus, flag=wx.ALL, border=5)
        hbox_countdown.Add(self.button_h_plus, flag=wx.ALL, border=5)
        hbox_countdown.Add(self.button_h_minus, flag=wx.ALL, border=5)
        hbox_countdown.Add(self.button_m_plus, flag=wx.ALL, border=5)
        hbox_countdown.Add(self.button_m_minus, flag=wx.ALL, border=5)
        hbox_countdown.Add(self.button_s_plus, flag=wx.ALL, border=5)
        hbox_countdown.Add(self.button_s_minus, flag=wx.ALL, border=5)
        

        vbox.Add(hbox_countdown, flag=wx.ALIGN_CENTER, border=10)

        # Textfield for timer
        self.timer_box = wx.TextCtrl(panel, style=wx.TE_READONLY | wx.TE_CENTER, size=(120,50))
        self.timer_box.SetMinSize((120, 50))
        self.timer_box.SetValue("00:00:00")
        timer_label = wx.StaticText(panel, label="Working time:")
        timer_label.SetFont(font)
        self.timer_box.SetFont(font)

        # Layout for stopwatch
        hbox_timer = wx.BoxSizer(wx.HORIZONTAL)
        hbox_timer.AddSpacer(10)
        hbox_timer.Add(timer_label, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        hbox_timer.Add(self.timer_box, flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        self.running_button = wx.Button(panel, label="Start", size=(240, 50))
        self.stop_button = wx.Button(panel, label="Stop", size=(240, 50))
        self.running_button.SetFont(font)
        self.stop_button.SetFont(font)
        hbox_timer.Add(self.running_button, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        hbox_timer.Add(self.stop_button, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        
        
        vbox.Add(hbox_timer, flag=wx.ALIGN_CENTER, border=10)
        vbox.Add(notebook, 1, flag=wx.EXPAND | wx.ALL, border=10)
               
        # Main window
        self.SetTitle("Bioreaktor GUI")
        self.SetSize((1280, 720))
        self.Centre()

        # Antifoam and Draw Sample buttons
        self.antifoam = wx.Button(main_tab, label="Anti Foam", size=(240,50))
        self.drawsample = wx.Button(main_tab, label="Draw Sample", size=(240,50))
        
        self.antifoam.SetFont(font)
        self.drawsample.SetFont(font)
        grid_main.Add(self.antifoam, flag=wx.ALIGN_CENTER)
        grid_main.Add(self.drawsample, flag=wx.ALIGN_CENTER)
        
        self.drawsample.Bind(wx.EVT_BUTTON, self.draw_sample)
        self.antifoam.Bind(wx.EVT_BUTTON, self.antifoam_action)

        # Start/Stop buttons bind
        self.running_button.Bind(wx.EVT_BUTTON, self.on_start_pause)
        self.stop_button.Bind(wx.EVT_BUTTON, self.on_stop)
        self.is_paused = True

        # Layout for temperature plot

        self.figure_temp_inside, self.ax_temp_inside = plt.subplots()
        self.canvas_temp_inside = FigureCanvas(temp_plot_tab, -1, self.figure_temp_inside)

        third_vbox = wx.BoxSizer(wx.VERTICAL)
        third_vbox.Add(self.canvas_temp_inside, 1, flag=wx.EXPAND | wx.ALL)
        temp_plot_tab.SetSizer(third_vbox)

        # Layout for pH plot
        self.figure_ph, self.ax_ph = plt.subplots()
        self.canvas_ph = FigureCanvas(ph_plot_tab, -1, self.figure_ph)

        fourth_vbox = wx.BoxSizer(wx.VERTICAL)
        fourth_vbox.Add(self.canvas_ph, 1, flag=wx.EXPAND | wx.ALL)
        ph_plot_tab.SetSizer(fourth_vbox)

        # Layout for oxygen levels plot

        self.figure_oxygen, self.ax_oxygen = plt.subplots()
        self.canvas_oxygen = FigureCanvas(oxygen_plot_tab, -1, self.figure_oxygen)

        fifth_vbox = wx.BoxSizer(wx.VERTICAL)
        fifth_vbox.Add(self.canvas_oxygen, 1, flag=wx.EXPAND | wx.ALL)
        oxygen_plot_tab.SetSizer(fifth_vbox)

        # Layout for events log tab
        events_vbox = wx.BoxSizer(wx.VERTICAL)
        self.text_ctrl = wx.TextCtrl(events_tab, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(1000, 1200))
        events_vbox.Add(self.text_ctrl, 1, flag=wx.EXPAND)
        

        panel.SetSizer(vbox)
        self.SetTitle("Bioreaktor GUI")
        self.SetSize((1500, 850))
        self.Centre()
        
    def update_time(self, hour_delta=0, minute_delta=0, second_delta=0):
        """ Helper function to update the time text control """
        current_time = self.countdown_input.GetValue()
        hours, minutes, seconds = map(int, current_time.split(":"))

        hours = max(0, min(999, hours + hour_delta))
        minutes = max(0, min(59, minutes + minute_delta))
        seconds = max(0, min(59, seconds + second_delta))

        new_time = f"{hours:02}:{minutes:02}:{seconds:02}"
        self.countdown_input.SetValue(new_time)

    def on_d_plus(self, event):
        self.update_time(hour_delta=24)

    def on_d_minus(self, event):
        self.update_time(hour_delta=-24)
        
    def on_h_plus(self, event):
        self.update_time(hour_delta=1)

    def on_h_minus(self, event):
        self.update_time(hour_delta=-1)

    def on_m_plus(self, event):
        self.update_time(minute_delta=1)

    def on_m_minus(self, event):
        self.update_time(minute_delta=-1)

    def on_s_plus(self, event):
        self.update_time(second_delta=1)

    def on_s_minus(self, event):
        self.update_time(second_delta=-1)
    def update_events(self, data):
        """Updates events in 'Events log' tab by reading them from session file."""
        wx.CallAfter(self.text_ctrl.SetValue, str(data))
        
    def start_countdown_timer(self, event):
        """Cycle timer logic"""
        if not self.countdown_running:
            input_time = self.countdown_input.GetValue()
            h, m, s = map(int, input_time.split(":"))
            self.countdown_time = h * 3600 + m * 60 + s
            if self.countdown_time > 0:
                self.countdown_running = True
                self.countdown_paused = False
                self.countdown_timer.Start(1000)
                self.update_countdown_timer(None)

    def pause_resume_countdown_timer(self, event):
        """Pause and resume functionality for cycle timer."""
        if self.countdown_running:
            if not self.countdown_paused:
                self.countdown_timer.Stop()
                self.countdown_paused = True
            else:
                self.countdown_timer.Start(1000)
                self.countdown_paused = False

    def update_countdown_timer(self, event):
        """Updates cycle timer values"""
        if self.countdown_running and not self.countdown_paused:
            if self.countdown_time > 0:
                self.countdown_time -= 1
                updated_time = time.strftime('%H:%M:%S', time.gmtime(self.countdown_time))
                update_cycle_time(updated_time)
                self.countdown_input.SetValue(updated_time)
            else:
                self.countdown_timer.Stop()
                self.countdown_running = False
                self.on_stop(None)

    def stir_on_rpm_choice(self, event):
        """Updates Stirr. RPM value based on selection from list"""
        selected_value = int(self.stir_rpm_choice.GetString(self.stir_rpm_choice.GetSelection()))
        self.text_controls['Stirr. RPM'] = selected_value
        self.update_params_from_gui()
        
    def air_on_rpm_choice(self, event):
        """Updates Air RPM value based on selection from list"""
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
        compare_ph_values(params["pH"])

    def update_timer(self, event):
        """Updates working timer values"""
        if self.timer_running:
            elapsed_time = int(time.time() - self.start_time)
            self.timer_box.SetValue(time.strftime('%H:%M:%S', time.gmtime(elapsed_time)))
            update_working_time(time.strftime('%H:%M:%S', time.gmtime(elapsed_time)))
        else:
            self.timer_box.SetValue(time.strftime('%H:%M:%S', time.gmtime(self.paused_time)))
    
    def draw_sample(self, event):
        """Draw sample functionality"""
        send_sample_signals()
        
    def antifoam_action(self, event):
        """Antifoam functionality"""
        send_antifoam_signal()
       
    def toggle_timer(self, event):
        """Pauses working timer"""
        if not self.timer_running:
            self.start_time = time.time() - self.paused_time  # Zachowujemy czas pauzy
            self.update_timer(None)  # Natychmiastowa aktualizacja wyświetlania czasu
            self.timer.Start(1000)  # Timer aktualizuje co sekundę
            self.timer_running = True

            print("Process started / resumed")
        else:
            self.paused_time = time.time() - self.start_time
            self.timer.Stop()
            self.timer_running = False
            print("Process paused")

    def stop_process(self, event):
        """Stops the current cycle, resets everything"""
        self.timer.Stop()
        self.timer_running = False
        self.countdown_timer.Stop()
        self.countdown_running = False
        self.start_time = 0
        self.paused_time = 0
        self.timer_box.SetValue("00:00:00")
        self.countdown_input.SetValue("01:30:00")
        stop_write_thread()
        wx.MessageBox("Cycle has ended.", "Info", wx.OK | wx.ICON_INFORMATION)
        print("Process stopped")
    
    def plot_temp_data(self, readings):
        """Plotting temperature data in real time"""
        temp_inside_list.append(readings[0])
        temp_outside_list.append(readings[1])
        
        self.ax_temp_inside.clear()
        self.ax_temp_inside.plot(temp_inside_list, label='Temperature inside', color='g')
        self.ax_temp_inside.plot(temp_outside_list, label='Temperature outside', color='r')
        self.ax_temp_inside.set_title('Temperature')
        self.ax_temp_inside.set_xlabel('Time [s]')
        self.ax_temp_inside.set_ylabel('Temperature (°C)')
        self.ax_temp_inside.legend()
        self.canvas_temp_inside.draw()

    def plot_ph_data(self, readings):
        """Plotting pH data in real time"""
        ph_list.append(readings)
        
        self.ax_ph.clear()
        self.ax_ph.plot(ph_list, label='pH', color='r')
        self.ax_ph.set_title('pH levels')
        self.ax_ph.set_xlabel('Time [s]')
        self.ax_ph.set_ylabel('pH')
        self.canvas_ph.draw()

    def plot_oxygen_data(self, readings):
        """Plotting oxygen data in real time"""
        oxygen_list.append(readings)
        
        self.ax_oxygen.clear()
        self.ax_oxygen.plot(oxygen_list, color='r')
        self.ax_oxygen.set_title('Oxygen levels')
        self.ax_oxygen.set_xlabel('Time [s]')
        self.ax_oxygen.set_ylabel('Oxygen')
        self.canvas_oxygen.draw()
          
    def on_start_pause(self, event):
        if self.is_paused:
            if self.running_button.GetLabel() == "Start":
                start_session()
                self.update_params_from_gui() 
                gui_ph_value = float(self.text_controls['pH'].GetValue())
                compare_ph_values(gui_ph_value)
                write_thread() 
                start_read_thread(self.update_gui_with_data)
                read_logs(self.update_events)
            else:
                resume_write_thread(1)

            if self.countdown_running and self.countdown_paused:
                self.countdown_timer.Start(1000)
                self.countdown_paused = False
            elif not self.countdown_running:
                self.start_countdown_timer(event)

            self.toggle_timer(wx.EVT_BUTTON)
            self.running_button.SetLabel("Pause") 
            self.is_paused = False
        else:
            pause_write_thread(1)
            self.toggle_timer(wx.EVT_BUTTON)
            
            if self.countdown_running and not self.countdown_paused:
                self.countdown_timer.Stop()
                self.countdown_paused = True

            self.running_button.SetLabel("Resume")
            self.is_paused = True

   
    def on_stop(self, event):
        self.stop_process(wx.EVT_BUTTON)
        stop_write_thread()
        save_plots(self.ax_temp_inside.figure, self.ax_ph.figure, self.ax_oxygen.figure)
        self.running_button.SetLabel("Start")
        self.is_paused = True

    def update_gui_with_data(self, data):
        # Update readings in "Readings" tab
        wx.CallAfter(self.readings_params['Temp. inside'].SetValue, str(data['temp_inside']))
        wx.CallAfter(self.readings_params['Temp. outside'].SetValue, str(data['temp_outside']))
        wx.CallAfter(self.readings_params['pH'].SetValue, str(data['ph']))
        wx.CallAfter(self.readings_params['Oxygen level'].SetValue, str(data['oxygen']))

        # Update readings plots in real time
        self.plot_temp_data([float(data['temp_inside']), float(data['temp_outside'])])
        self.plot_ph_data(float(data['ph']))
        self.plot_oxygen_data(float(data['oxygen']))

        


class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None)
        frame.Show(True)
        return True

if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()
