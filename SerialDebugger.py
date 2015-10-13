#!/usr/bin/env python

import serial
import sys
import glob
from os import linesep
import threading

# Python 2.7, etc.
if sys.version_info[0] < 3:
    import Tkinter as tk
    import ScrolledText as tkst
    from Tkinter import StringVar
# Python 3.x
else:
    import tkinter as tk
    import tkinter.scrolledtext as tkst
    from tkinter import StringVar



class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.master = master
        self.grid()
        self.master.wm_title('Serial Debugger')
        self._serial_lock = threading.Lock()
        self._baudrate_prev = '9600'
        self._encoding_prev = sys.getdefaultencoding()
        self._baudrate_list = [str(600 * 2**x) for x in range(9)]
        self._baudrate_list.append('Other...')
        self._create_widgets()
        
        
    def _create_serial_options(self):
        self._serial_label = tk.Label(self, text='Serial Port:').grid(row=0, sticky=tk.W)
        
        self._serial_variable = StringVar(self)

        self._serial_variable.set('None')
        self._available_ports = _get_serial_ports()
        self._serial_options = tk.OptionMenu(self, self._serial_variable, *self._available_ports if self._available_ports else ['None'])
        self._serial_options.grid(row=0, column=1, sticky='ew')
        self._serial_options.configure(anchor='w')
        
    def _create_baudrate_options(self):
        self._baudrate_label = tk.Label(self, text='Baudrate:').grid(row=1, sticky=tk.W)
        
        self._baudrate_variable = StringVar(self)
        self._baudrate_variable.set('9600')
        self._baudrate_variable.trace('w', self._baudrate_callback)
        self._baudrate_options = tk.OptionMenu(self, self._baudrate_variable, *self._baudrate_list)
        self._baudrate_options.grid(row=1, column=1, sticky='ew')
        self._baudrate_options.configure(anchor='w')
        
    def _create_databits_options(self):
        self._databits_label = tk.Label(self, text='Data Bits:').grid(row=2, sticky=tk.W)
        self._databits_variable = tk.IntVar(self)
        self._databits_variable.set(8)
        self._databits_options = tk.OptionMenu(self, self._databits_variable, 8,7,6,5)
        self._databits_options.grid(row=2, column=1, sticky='ew')
        self._databits_options.configure(anchor='w')
        
    def _create_parity_options(self):
        self._parity_label = tk.Label(self, text='Parity:').grid(row=3, sticky=tk.W)
        self._parity_variable = tk.StringVar(self)
        self._parity_variable.set('None')
        self._parity_options = tk.OptionMenu(self, self._parity_variable, 'None', 'Even', 'Odd', 'Mark', 'Space')
        self._parity_options.grid(row=3, column=1, sticky='ew')
        self._parity_options.configure(anchor='w')
        
    def _create_stopbits_options(self):
        self._stopbits_label = tk.Label(self, text='Stop Bits:').grid(row=4, sticky=tk.W)
        self._stopbits_variable = tk.IntVar(self)
        self._stopbits_variable.set(1)
        self._stopbits_options = tk.OptionMenu(self, self._stopbits_variable, 1, 2)
        self._stopbits_options.grid(row=4, column=1, sticky='ew')
        self._stopbits_options.configure(anchor='w')
        
    def _create_timeout_entry(self):
        self._timeout_label = tk.Label(self, text='Timeout (sec):').grid(row=5, sticky=tk.W)
        self._timeout_entry = tk.Entry(self)
        self._timeout_entry.insert(0, '-1')
        self._timeout_entry.grid(row=5, column=1, sticky='ew')  
        
    def _create_encoding_options(self):
        self._encoding_label = tk.Label(self, text='Encoding:').grid(row=6, sticky=tk.W)
        self._encoding_variable = tk.StringVar(self)
        self._encoding_variable.set(sys.getdefaultencoding())
        self._encoding_variable.trace('w', self._encoding_callback)
        self._encoding_options = tk.OptionMenu(self, self._encoding_variable, self._encoding_variable.get(), 'Other...')
        self._encoding_options.grid(row=6, column=1, sticky='ew')
        self._encoding_options.configure(anchor='w')
                
    def _create_scrolltext(self):
        self._serial_scrolltext = tkst.ScrolledText(self,
                                                    wrap   = tk.WORD,
                                                    width  = 40,
                                                    height = 10)
        self._serial_scrolltext.grid(row=7, column=0, columnspan=2, ipadx=10, ipady=10)
        
    def _create_button_reset(self):
        self._button_reset = tk.Button(self, text='Reset')
    def _create_button_cancel(self):
        self._button_cancel = tk.Button(self, text='Cancel', command = self._cleanup)
        self._button_cancel.grid(row=11, column=0, sticky='ew')
        
    def _create_button_ok(self):
        self._button_ok = tk.Button(self, text='OK', command = self._start_serial_view_launcher)
        self._button_ok.grid(row=11, column=1, sticky='ew')
        
    def _cleanup(self):
        try:
            if self._thread.is_alive():
                self._thread._stop()
        except:
            pass
        self.master.destroy()
        
        
    def _create_widgets(self):
        self._create_serial_options()
        self._create_baudrate_options()
        self._create_databits_options()
        self._create_parity_options()
        self._create_stopbits_options()
        self._create_timeout_entry()
        self._create_encoding_options()
        self._create_scrolltext()
        self._create_button_cancel()
        self._create_button_ok()
        
    def _start_serial_view_launcher(self):
        self._thread = threading.Thread(target=self._start_serial_view)
        self._thread.start()
        
    def _start_serial_view(self):
        _timeout = int(self._timeout_entry.get())
        self._serial = serial.Serial(
                            port     = self._serial_variable.get(),
                            baudrate = int(self._baudrate_variable.get()),
                            bytesize = self._databits_variable.get(),
                            parity   = self._parity_variable.get()[0],
                            stopbits = self._stopbits_variable.get(),
                            timeout  = _timeout if _timeout != -1 else None
                            )
         
        while 1:
            try:
                t = self._serial.readline().decode(self._encoding_variable.get().strip()).replace('''\r\n''', '')
                self._serial_scrolltext.insert(tk.END, t + linesep)
                self._serial_scrolltext.see(tk.END)
            except:
                exit()
            
    def _baudrate_callback(self, *args):
        self._baudrate = self._baudrate_options.cget('text')
        if self._baudrate == 'Other...':
            self.w = PopupWindow(self, 'Custom Baudrate:')
            self.master.wait_window(self.w.top)
            try:
                if self._ret_value == 'ERR':
                    self._baudrate_variable.set(self._baudrate_prev)
                else:
                    self._baudrate_variable.set(self._ret_value)
                    self._baudrate_prev = self._ret_value
            except:
                self._baudrate_variable.set(self._baudrate_prev)
            self._baudrate_options.destroy()
            self._baudrate_options = tk.OptionMenu(self, self._baudrate_variable, *self._baudrate_list)
            self._baudrate_options.grid(row=1, column=1, sticky='ew')
            self._baudrate_options.configure(anchor='w')
        else:
            self._baudrate_prev = self._baudrate_options.cget('text')
            
    
    def _encoding_callback(self, *args):
        self._encoding = self._encoding_options.cget('text')
        if self._encoding == 'Other...':
            self.w = PopupWindow(self, 'Custom Encoding:')
            self.master.wait_window(self.w.top)
            try:
                if self._ret_value == 'ERR':
                    self._encoding_variable.set(self._encoding_prev)
                else:
                    self._encoding_variable.set(self._ret_value)
                    self._encoding_prev = self._ret_value
            except:
                self._encoding_variable.set(self._encoding_prev)
            self._encoding_options.destroy()
            self._encoding_options = tk.OptionMenu(self, self._encoding_variable, sys.getdefaultencoding(), 'Other...')
            self._encoding_options.grid(row=6, column=1, sticky='ew')
            self._encoding_options.configure(anchor='w')

                
class PopupWindow(tk.Frame):
    def __init__(self, base, text):
        tk.Frame.__init__(self)
        top = self.top=tk.Toplevel(base)
        self._label = tk.Label(top, text=text).grid(row=0)
        self._entry = tk.Entry(top)
        self._entry.grid(row=0, column=1, columnspan=2)
        self._button_ok = tk.Button(top, text='OK', command= lambda : self._cleanup(base, 'ok')).grid(row=1, column=1)
        self._button_cancel = tk.Button(top, text='Cancel', command= lambda : self._cleanup(base, 'cancel')).grid(row=1, column=2)
        
    def _cleanup(self, base, command):
        if command == 'ok':
            base._ret_value=self._entry.get()
        else:
            base._ret_value = 'ERR'
        self.top.destroy()
        

def _get_serial_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i+1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/tty[A-Za-z0-9]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')
    
    res = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            res.append(port)
        except:
            pass
    return res
        
def task():
    app._serial_lock.acquire()
    ports = _get_serial_ports()
    if app._available_ports != ports:
        app._available_ports = ports
        app._available_ports = _get_serial_ports()
        if app._serial_variable.get() not in app._available_ports:
            app._serial_variable.set('None')
        app._serial_options = tk.OptionMenu(app, app._serial_variable, *app._available_ports if app._available_ports else ['None'])
        app._serial_options.grid(row=0, column=1, sticky='ew')
        app._serial_options.configure(anchor='w')
    app._serial_lock.release()
    root.after(250, task)
    
def on_close():
    app._cleanup()

if __name__ == '__main__':
    root = tk.Tk()
    app = Application(root)
    root.protocol('WM_DELETE_WINDOW', on_close)
    root.after(500, task)
    app.mainloop()
