import tkinter

window = tkinter.Tk()
window.title("Data Entry Form")

frame = tkinter.Frame(window)
frame.pack()

#Saving user information
composer_frame = tkinter.LableFrame(frame, text = "Composer")
composer_frame.grid(row = 0, column = 0, padx = 20, pady = 20)

first_name_label = tkinter.label(composer_frame, text = "First Name")
first_name_label.grid(row = 0, column = 0)

middle_name_label = tkinter.label(composer_frame, text = "Middle Name")
middle_name_label.grid(row = 0, column = 1)

last_name_label = tkinter.label(composer_frame, text = "Last Name")
last_name_label.grid(row = 0, column = 2)

first_name_entry = tkinter.Entry(composer_frame)
middle_name_entry = tkinter.Entry(composer_frame)
last_name_entry = tkinter.Entry(composer_frame)
first_name_entry.grid(row = 1, column = 0)
middle_name_entry.grid(row = 1, column = 1)
last_name_entry.grid(row = 1, column = 2)
 

window.mainloop()