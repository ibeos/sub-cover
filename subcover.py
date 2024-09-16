import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import font
import tkinter.messagebox as messagebox
from tkinter.colorchooser import askcolor
import time
import pysrt
import os
import pyperclip
import json


class Window(tk.Toplevel):

    width = 0
    height = 0
    x_offset = 0
    y_offset = 0

    play_button = None
    prev_button = None
    next_button = None
    quit_button = None
    label = None
    afters = []
    subs = []

    subtitle_frame = None
    buttons_frame = None

    current_start_time = 0
    current_sub = -1
    is_gap = False
    copy_subs = False

    def __init__(self, parent):
        super().__init__(parent)

        self.width = int(self.winfo_screenwidth() / 5 * 3)
        self.height = int(self.winfo_screenheight() / 4)
        self.x_offset = int(self.winfo_screenwidth() / 5)
        self.y_offset = int(self.winfo_screenheight() / 4 * 3)

        self.wm_overrideredirect(True)
        self.config(bg='black') 
        self.geometry("{0}x{1}+{2}+{3}".format(self.width, self.height, self.x_offset, self.y_offset))
        self.attributes('-topmost', 'true')

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.subtitle_frame = tk.Frame(self, bg='black')
        self.subtitle_frame.grid(row=0, column=0, columnspan=3, sticky=tk.E+tk.W+tk.N+tk.S)

        self.label=tk.Label(self.subtitle_frame, text='', font=("Noto Serif JP", 30), foreground='white', background='black', anchor=tk.CENTER)
        self.label.pack() 

        self.buttons_frame = tk.Frame(self, bg='black')
        self.buttons_frame.grid(row=1, column=0, sticky=tk.EW) 
        self.buttons_frame.columnconfigure(0, weight=1)
        self.buttons_frame.columnconfigure(1, weight=1)
        self.buttons_frame.columnconfigure(2, weight=1)

        self.prev_button = tk.Button(self.buttons_frame, text='<<', command=self.prev_sub, background='black', foreground='white')
        self.prev_button.grid(column=1, row=0, sticky=tk.SW, padx=5, pady=5)

        self.play_button = tk.Button(self.buttons_frame, text='play', command=self.intro, background='black', foreground='white')
        self.play_button.grid(column=1, row=0, sticky=tk.S, padx=5, pady=5)

        self.next_button = tk.Button(self.buttons_frame, text='>>', command=self.next_sub, background='black', foreground='white')
        self.next_button.grid(column=1, row=0, sticky=tk.SE, padx=5, pady=5)

        self.quit_button = tk.Button(self.buttons_frame, text='x', command=self.window_exit, background='black', foreground='white')
        self.quit_button.grid(column=2, row=0, sticky=tk.SE, padx=5, pady=5)

        self.bind("<Enter>", lambda evt : self.show_buttons())
        self.bind("<Leave>", lambda evt : self.hide_buttons())

    def time_to_ms(self, time_obj):
        return int(time_obj.hours * 3600 + time_obj.minutes * 60 + time_obj.seconds + time_obj.milliseconds / 1000) * 1000
    
    def set_subs(self, subs):
        self.subs = subs

    def set_clipboard_copy(self, copy):
        self.copy_subs = copy

    def show_buttons(self):
        self.buttons_frame.grid()

    def hide_buttons(self):
        self.buttons_frame.grid_remove()

    def set_width(self, width):
        self.width = width
        self.x_offset = (self.winfo_screenwidth() - self.width) / 2
        self.geometry("{0}x{1}+{2}+{3}".format(int(self.width), int(self.height), int(self.x_offset), int(self.y_offset)))
    
    def set_height(self, height, offset):
        self.height = height
        self.y_offset = (self.winfo_screenheight() - self.height) - offset
        self.geometry("{0}x{1}+{2}+{3}".format(int(self.width), int(self.height), int(self.x_offset), int(self.y_offset)))

    def set_offset(self, offset):
        self.y_offset = (self.winfo_screenheight() - self.height) - offset
        self.geometry("{0}x{1}+{2}+{3}".format(int(self.width), int(self.height), int(self.x_offset), int(self.y_offset)))

    def set_background_color(self, color):
        self.config(bg=color)
        self.subtitle_frame.config(bg=color)
        self.buttons_frame.config(bg=color)
        self.label.config(background=color)
        self.play_button.config(background=color)
        self.prev_button.config(background=color)
        self.next_button.config(background=color)
        self.quit_button.config(background=color)

    def set_text_color(self, color):
        self.label.config(foreground=color)
        self.play_button.config(foreground=color)
        self.prev_button.config(foreground=color)
        self.next_button.config(foreground=color)
        self.quit_button.config(foreground=color)

    def set_font(self, font, size):
        self.label.config(font=(font, size))

    def intro(self, is_start=True, time_played=0):
        self.label.config(text='3')
        self.afters.append(self.label.after(1000, lambda : self.label.config(text='2')))
        self.afters.append(self.label.after(2000, lambda : self.label.config(text='1')))
        self.afters.append(self.label.after(3000, lambda : self.label.config(text='')))
        if (is_start):
            self.afters.append(self.label.after(3000, lambda : self.start()))
        else:
            self.afters.append(self.label.after(3000, lambda : self.resume(time_played)))

    def start(self):
        self.current_start_time = int(time.time() * 1000)
        self.play_button.config(text='pause', command=lambda : self.pause())
        start_time = self.time_to_ms(self.subs[0].start)
        self.afters.append(self.label.after(start_time, lambda : self.show_sub(0)))

    def pause(self):
        pause_time = int(time.time() * 1000)
        self.cancel_all_afters()
        time_played = pause_time - self.current_start_time
        self.play_button.config(text='play', command=lambda : self.intro(False, time_played))

    def resume(self, time_played):
        self.play_button.config(text='pause', command=self.pause)
        if self.is_gap:
            self.show_gap(self.current_sub, time_played)
        else:
            self.show_sub(self.current_sub, time_played)

    def next_sub(self):
        self.cancel_all_afters()
        self.show_sub(self.current_sub+1)

    def prev_sub(self):
        self.cancel_all_afters()
        self.show_sub(self.current_sub-1)

    def show_sub(self, i, time_played = 0):
        self.current_start_time = int(time.time() * 1000)
        self.current_sub = i
        self.is_gap = False

        start_time = self.time_to_ms(self.subs[i].start)
        end_time = self.time_to_ms(self.subs[i].end)
        sub_duration = end_time - (start_time + time_played)

        self.label.config(text=self.subs[i].text)
        if self.copy_subs:
            pyperclip.copy(self.subs[i].text)
        self.afters.append(self.label.after(sub_duration, lambda : self.show_gap(i)))

    def show_gap(self, i, time_played = 0):
        self.current_start_time = int(time.time() * 1000)
        self.current_sub = i
        self.is_gap = True

        start_time = self.time_to_ms(self.subs[i].end)
        end_time = self.time_to_ms(self.subs[i+1].start)
        gap_duration = end_time - (start_time + time_played)

        self.label.config(text='')
        self.afters.append(self.label.after(gap_duration, lambda : self.show_sub(i+1)))

    def cancel_all_afters(self):
        for after in self.afters:
            self.label.after_cancel(after)

    def window_exit(self):
        close = messagebox.askyesno("Close overlay?", "Are you sure you want to close the overlay?")
        if close:
            self.destroy()

class App(tk.Tk):

    
    subs = []
    path = 'D:/Desktop/Subtitles/'
    file_label = None

    sub_window_open = False
    sub_window = None
    background_color_button = None
    background_color_label = None
    text_color_button = None
    text_color_label = None
    open_overlay_button = None

    background_color = 'black'
    text_color = 'white'
    sub_font = None
    font_size = None
    copy_subs = True
    window_width = 0
    window_height = 0
    window_offset = 0

    def save(self):
        dict = {
            "sub_file": self.path,
            "background_color": self.background_color,
            "text_color": self.text_color,
            "sub_font": self.sub_font.get(),
            "font_size": self.font_size.get(),
            "copy_subs": self.copy_subs,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "window_offset": self.window_offset,
        }
        file = open("subcover_save.json", "w")
        json.dump(dict, file)
        file.close()

    def load(self):
        if os.path.exists('subcover_save.json'):
            file = open('subcover_save.json')
            data = json.load(file)
            self.path = data["sub_file"]
            self.background_color = data["background_color"]
            self.text_color = data["text_color"]
            self.sub_font.set(data["sub_font"])
            self.font_size.set(data["font_size"])
            self.copy_subs = data["copy_subs"]
            self.window_width = data["window_width"]
            self.window_height = data["window_height"]
            self.window_offset = data["window_offset"]
        else:
            self.save()

    def __init__(self):
        super().__init__()

        self.sub_font = tk.StringVar(value="Arial")
        self.font_size = tk.StringVar(value=40)

        self.window_width = int(self.winfo_screenwidth() / 5 * 3)
        self.window_height = int(self.winfo_screenheight() / 4)

        self.load()

        #self.geometry('300x200')
        self.title('Hard Subs Cover') 

        tk.Label(self, text='Subtitle File').grid(column=0, row=0, columnspan=2, sticky=tk.SW, padx=5)

        button = tk.Button(self, text='Load', command=self.select_file)
        button.grid(column=0, row=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        self.file_label = tk.Label(self, text=self.path, width=30, anchor=tk.W)
        self.file_label.grid(column=1, row=1, sticky=tk.W, padx=5, pady=5)

        tk.Label(self, text='Background Color').grid(column=0, row=3, columnspan=2, sticky=tk.SW, padx=5)

        self.background_color_button = tk.Button(self, text='Choose', command=self.change_background_color)
        self.background_color_button.grid(column=0, row=4, sticky=tk.W+tk.E, padx=5, pady=5)
        self.background_color_label = tk.Label(self, bg=self.background_color, width=30)
        self.background_color_label.grid(column=1, row=4, padx=5, pady=5)

        tk.Label(self, text='Text Color').grid(column=0, row=5, columnspan=2, sticky=tk.SW, padx=5)

        self.text_color_button = tk.Button(self, text='Choose', command=self.change_text_color)
        self.text_color_button.grid(column=0, row=6, sticky=tk.W+tk.E, padx=5, pady=5)
        self.text_color_label = tk.Label(self, bg=self.text_color, width=30)
        self.text_color_label.grid(column=1, row=6, padx=5, pady=5)

        tk.Label(self, text='Font Family and Font Size').grid(column=0, row=7, columnspan=2, sticky=tk.SW, padx=5)

        fonts=list(font.families())
        fonts.sort()

        tk.OptionMenu(self, self.sub_font, *fonts, command=self.change_font).grid(column=0, row=8, columnspan=2, sticky=tk.SW, padx=5)
        spin_box = ttk.Spinbox(self, from_=5, to=60,textvariable=self.font_size,width=3, command=lambda: self.change_font(self.sub_font))
        spin_box.grid(column=1, row=8, sticky=tk.E, padx=5)

        tk.Label(self, text='Overlay Size and Position').grid(column=0, row=9, columnspan=2, sticky=tk.SW, padx=5)

        frame = tk.Frame(self)
        frame.grid(column=0, row=10, columnspan=2)

        tk.Label(frame, text='Width').pack(side=tk.LEFT, padx=10, pady=5)
        tk.Button(frame, text='-', width=1, command=lambda: self.change_width(-10)).pack(side=tk.LEFT)
        tk.Button(frame, text='+', width=1, command=lambda: self.change_width(10)).pack(side=tk.LEFT)
        tk.Label(frame, text='Height').pack(side=tk.LEFT, padx=10, pady=5)
        tk.Button(frame, text='-', width=1, command=lambda: self.change_height(-10)).pack(side=tk.LEFT)
        tk.Button(frame, text='+', width=1, command=lambda: self.change_height(10)).pack(side=tk.LEFT)
        tk.Label(frame, text='Offset').pack(side=tk.LEFT, padx=10, pady=5)
        tk.Button(frame, text='-', width=1, command=lambda: self.change_offset(-10)).pack(side=tk.LEFT)
        tk.Button(frame, text='+', width=1, command=lambda: self.change_offset(10)).pack(side=tk.LEFT)

        copy = tk.Checkbutton(self, text='Copy current subtitle to clipboard',variable=self.copy_subs, onvalue=True, offvalue=False, command=self.change_clipboard_copy)
        copy.grid(column=0, row=11, columnspan=2, sticky=tk.W, padx=5, pady=5)

        self.open_overlay_button = tk.Button(self, text='Open the overlay', command=self.open_window)
        self.open_overlay_button.grid(column=0, row=12, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)

    def window_closed(self, event):
        self.sub_window_open = False
        self.open_overlay_button.config(text='Open the overlay')

    def open_window(self):
        if self.sub_window_open:
            # showinfo(title='Warning', message='Window already open')
            self.open_overlay_button.config(text='Open the overlay')
            self.sub_window.destroy()
            self.sub_window_open = False
        else:
            self.open_overlay_button.config(text='Close the overlay')
            self.sub_window = Window(self)
            self.sub_window.bind('<Destroy>', self.window_closed)
            self.sub_window_open = True
            self.sub_window.set_subs(self.subs)
            self.sub_window.set_clipboard_copy(self.copy_subs)
            if self.background_color:
                self.sub_window.set_background_color(self.background_color)
            if self.text_color:
                self.sub_window.set_text_color(self.text_color)
            self.sub_window.set_width(self.window_width)
            self.sub_window.set_height(self.window_height, self.window_offset)
            self.sub_window.set_offset(self.window_offset)
            #subs_window.grab_set()

    def select_file(self):
        filetypes = (
            ('SRT files', '*.srt'),
            ('All files', '*.*')
        )

        filename = fd.askopenfilename(
            title='Open a subtitle (*.srt) file',
            initialdir=self.path,
            filetypes=filetypes)

        if os.path.exists(filename):
            self.path = filename
            self.file_label.config(text=filename)
            self.subs = pysrt.open(filename)
        # else:
        #     showinfo(title='Warning', message=filename + " is not a valid filename")
        self.save()

    def change_background_color(self):
        colors = askcolor(title="Choose Background Color")
        self.background_color = colors[1]
        self.background_color_label.config(bg=self.background_color)
        if self.sub_window_open:
            self.sub_window.set_background_color(self.background_color)
        self.save()

    def change_text_color(self):
        colors = askcolor(title="Choose Text Color")
        self.text_color = colors[1]
        self.text_color_label.config(bg=self.text_color)
        if self.sub_window_open:
            self.sub_window.set_text_color(self.text_color)
        self.save()

    def change_font(self, font):
        font = self.sub_font.get()
        size = self.font_size.get()
        if self.sub_window_open:
            self.sub_window.set_font(font, size)
        self.save()

    def change_width(self, pixels):
        self.window_width = min(self.winfo_screenwidth(), self.window_width + pixels)
        if self.sub_window_open:
            self.sub_window.set_width(self.window_width)
        self.save()
    
    def change_height(self, pixels):
        self.window_height = min(self.winfo_screenheight() - self.window_offset, self.window_height + pixels)
        if self.sub_window_open:
            self.sub_window.set_height(self.window_height, self.window_offset)
        self.save()
    
    def change_offset(self, pixels):
        self.window_offset = min(self.winfo_screenheight() - self.window_height, self.window_offset + pixels)
        if self.sub_window_open:
            self.sub_window.set_offset(self.window_offset)
        self.save()

    def change_clipboard_copy(self):
        if self.sub_window_open:
            self.sub_window.set_clipboard_copy(self.copy_subs)
        self.save()


if __name__ == "__main__":
    app = App()
    app.mainloop()