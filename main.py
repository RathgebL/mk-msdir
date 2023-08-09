import tkinter
from tkinter import ttk

window = tkinter.Tk()
window.title("Data Entry Form")

frame = tkinter.Frame(window)
frame.pack()

#Saving media title information
media_title_frame = tkinter.LabelFrame(frame, text = "Media title")
media_title_frame.grid(row = 0, column = 0, sticky = "news", padx = 20, pady = 20)

media_title_lable = tkinter.Label(media_title_frame, text = "Title")
media_title_lable.grid(row = 0, column = 0)

media_title_entry = tkinter.Entry(media_title_frame)
media_title_entry.grid(row = 1, column = 0)

#Saving composer information
composer_frame = tkinter.LabelFrame(frame, text = "Composer")
composer_frame.grid(row = 1, column = 0, padx = 20, pady = 20)

from_one_composer_label = tkinter.Label(composer_frame, text = "Is the whole media from one composer?")
from_one_composer_label.grid(row = 0, column = 0)

from_one_composer_combobox = ttk.Combobox(composer_frame, values = ["y", "n"])
from_one_composer_combobox.grid(row = 1, column = 0)

number_of_composers_label = tkinter.Label(composer_frame, text = "Are there more than 4 composers?")
number_of_composers_label.grid(row = 0, column = 1)

number_of_composers_combobox = ttk.Combobox(composer_frame, values = ["y", "n"])
number_of_composers_combobox.grid(row = 1, column = 1)

first_name_label = tkinter.Label(composer_frame, text = "First Name")
first_name_label.grid(row = 2, column = 0)

middle_name_label = tkinter.Label(composer_frame, text = "Middle Name")
middle_name_label.grid(row = 2, column = 1)

last_name_label = tkinter.Label(composer_frame, text = "Last Name")
last_name_label.grid(row = 2, column = 2)

first_name_entry = tkinter.Entry(composer_frame)
middle_name_entry = tkinter.Entry(composer_frame)
last_name_entry = tkinter.Entry(composer_frame)
first_name_entry.grid(row = 3, column = 0)
middle_name_entry.grid(row = 3, column = 1)
last_name_entry.grid(row = 3, column = 2)
 
for widget in composer_frame.winfo_children():
    widget.grid_configure(padx=10, pady=5)

window.mainloop()