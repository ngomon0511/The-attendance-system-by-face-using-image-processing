from tkinter import *
from PIL import ImageTk, Image
from app import app

def change_window():
    '''
    Go to the application's workspace
    '''
    root.destroy()
    app()

root = Tk()
root.geometry('1280x640')
root.title("Final Term Project")

img = ImageTk.PhotoImage(Image.open("img_gui/introduce.jpg"))
background = Label(root, image=img)
background.grid(column=0, row=0)

btn_change_window = Button(root, text="START", borderwidth=10, font=("Arial", 20), bg='green', fg='white', command=change_window)
btn_change_window.place(width=120, height=50, x=975, y=560)

root.mainloop()
