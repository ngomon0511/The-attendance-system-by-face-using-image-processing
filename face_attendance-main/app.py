from tkinter import *
from types import NoneType
from PIL import ImageTk, Image
import os
from utils import *
from threading import Thread, Event, Lock

class App:
    def __init__(self, root, menu_bar, img_program, img_start, img_mark, name, file_name, start_time, end_time):
        # Initialize the application
        self.root = root
        self.menu_bar = menu_bar
        self.img_program = img_program
        self.img_start = img_start
        self.img_mark = img_mark
        self.name = name
        self.file_name = file_name
        self.start_time = start_time
        self.end_time = end_time
        self.lock = Lock()
        self.stop_display_video = Event()

        # Set up the GUI elements
        self.background_label = Label(root, image=img_program)
        self.background_label.place(x=0, y=0)

        self.side_label = Label(root, image=img_start)
        self.side_label.place(x=808, y=44)

        self.btn_start_attendance = Button(root, text="START ATTENDANCE", font=("Arial", 15, "bold"), bg='#B28DFF', borderwidth=0, fg='white', command=self.start_attendance)
        self.btn_start_attendance.place(x=908, y=354)

        # Create the component "View" in menu bar
        self.file_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="View", menu=self.file_menu)
        self.file_menu.add_command(label="Image Database", command=lambda: os.startfile("img_db"))
        self.file_menu.add_command(label="Encode Database", command=lambda: os.startfile("encode_db.csv"))
        self.file_menu.add_command(label="Attendance Information", command=lambda: os.startfile("attendance_infor"))

        # Create the component "Edit Database" in menu bar
        self.file_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Edit Database", menu=self.file_menu)
        self.file_menu.add_command(label="Add Image Database", command=add_img_db)
        self.file_menu.add_command(label="Convert to Encode Database", command=self.convert_to_encode_db)
        self.file_menu.add_command(label="Delete from Image Database", command=delete_from_img_db)
        self.file_menu.add_command(label="Delete from Encode Database", command=delete_from_encode_db)

    def start_attendance(self):
        '''
        Start the attendance process
        '''
        self.btn_start_attendance.destroy()
        self.side_label.destroy()
        
        self.side_label = Label(self.root, image=self.img_mark)
        self.side_label.place(x=808, y=44)

        self.btn_mark_attendance = Button(self.root, text="MARK ATTENDANCE", font=("Arial", 15, "bold"), bg='#B28DFF', borderwidth=0, fg='white', command=self.mark_attendance)
        self.btn_mark_attendance.place(x=912, y=404)

        try:
            self.file_name, self.start_time, self.end_time = name_attendance_file()
        except:
            self.root.destroy()
            quit()
        self.capture_video()

    def mark_attendance(self):
        '''
        Mark attendance for the current session
        '''
        mark_attendance(self.name, self.file_name, self.start_time, self.end_time)

    def new_attendance(self):
        '''
        Start a new attendance session
        '''
        self.stop_display_video.set()
        self.process_thread.join()
        try:
            self.file_name, self.start_time, self.end_time = name_attendance_file()
        except:
            self.root.destroy()
            quit()
        self.stop_display_video.clear()
        self.capture_video()

    def is_menu_exists(self, label):
        '''
        Check if a menu item exists in the menu bar
        '''
        try:
            self.menu_bar.index(label)
            return True
        except:
            return False

    def capture_video(self):
        '''
        Capture video from the camera and update the video label
        '''
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 1280)
        self.cap.set(4, 720)

        self.video_label = Label(self.root)
        self.video_label.place(x=55, y=162)

        if not self.is_menu_exists("New attendance"):
            self.file_menu = Menu(self.menu_bar, tearoff=0)
            self.menu_bar.add_cascade(label="New attendance", menu=self.file_menu)
            self.file_menu.add_command(label="Start", command=self.new_attendance)

        self.processed_img = None 
        self.process_thread = Thread(target=self.process_video)
        self.process_thread.start()

        self.update_video()

    def update_video(self):
        '''
        Update the video label with the processed image
        '''
        if self.processed_img is not None:
            with self.lock:
                rgb_img = cv2.cvtColor(self.processed_img, cv2.COLOR_BGR2RGB)
                img = ImageTk.PhotoImage(image=Image.fromarray(rgb_img))
                self.video_label.configure(image=img)
                self.video_label.image = img
        if not self.stop_display_video.is_set():
            self.video_label.after(1, self.update_video)

    def process_video(self):
        '''
        Process the video frames, detect faces, and recognize attendees
        '''
        while not self.stop_display_video.is_set():
            success, img = self.cap.read()
            if type(img) == NoneType:
                messagebox.showerror("Error", "Not found camera in this device!")
                self.root.destroy()
                quit()
            if success:
                self.name, processed_img = cur_img_process(img)  
                with self.lock:
                    self.processed_img = processed_img

    def convert_to_encode_db(self):
        '''
        Convert the image database to an encoded database
        '''
        self.stop_display_video.set()
        try:
            self.process_thread.join()
        except:
            pass
        convert_to_encode_db()
        self.stop_display_video.clear()
        try:
            if self.process_thread is not None:
                self.capture_video()
        except:
            pass

def app():
    # Create a UI window
    root = Tk()
    root.geometry('1280x720')
    root.title("Face Attendance App")

    # Create and pass parameters for object App to run the application 
    menu_bar = Menu(root)
    root.config(menu=menu_bar)
    img_program = ImageTk.PhotoImage(Image.open("img_gui/program.jpg"))
    img_start = ImageTk.PhotoImage(Image.open("img_gui/start.jpg"))
    img_mark = ImageTk.PhotoImage(Image.open("img_gui/mark.jpg"))
    name = ''
    file_name = ''
    start_time = ''
    end_time = ''
    App(root, menu_bar, img_program, img_start, img_mark, name, file_name, start_time, end_time)
    root.mainloop()
