import cv2
import numpy as np
from tkinter import messagebox
from tkinter.simpledialog import askstring
from datetime import datetime
import os
import csv
import face_recognition
from tkinter.filedialog import askopenfilename
import shutil

''' FUNCTION LIST '''
# crop_center_image
# augment_data
# str_to_list_arr
# set_time_attendance
# name_attendance_file
# mark_attendance
# convert_to_encode_db
# add_img_db
# delete_from_encode_db
# delete_from_img_db
# read_encode_db
# cur_img_process

def crop_center_image(img):
    '''
    Crop the center part of the original image.
    
    Args:
        img (numpy.ndarray): The original image.
    
    Returns:
        numpy.ndarray: The cropped image.
    '''
    height, width = img.shape[:2]
    crop_size = min(width, height)
    center_x = width // 2
    center_y = height // 2
    cropped_img = img[center_y - crop_size // 2:center_y + crop_size // 2, center_x - crop_size // 2:center_x + crop_size // 2]
    return cropped_img

def augment_data(img):
    '''
    Augment the input image with 8 different brightness levels.
    
    Args:
        img (numpy.ndarray): The input image.
    
    Returns:
        list: A list of augmented images.
    '''
    bright_factors = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]
    aug_img = [cv2.convertScaleAbs(img, alpha=factor, beta=0) for factor in bright_factors]
    return aug_img

def str_to_list_arr(row):
    '''
    Convert a row in a CSV file that contains encodes for a person
    to a list that contains encoded arrays for each different brightness level.
    
    Args:
        row (str): The row in the CSV file.
    
    Returns:
        list: A list of encoded arrays.
    '''
    row = row[1:-2].replace('array', '').replace('(', '')
    list_arr = [np.fromstring(arr[1:-1], sep=', ') for arr in list(row.split('), '))]
    return list_arr

def set_time_attendance():
    '''
    Set up the time interval for attendance.

    Returns:
        tuple: A tuple containing the start time and end time as datetime.time objects.
    '''
    while True:
        interval_time = askstring("Setup time", "Please enter the attendance time (e.g., 07:00 AM - 07:15 AM):")
        if not interval_time:
            answer = messagebox.askyesno('Confirm', 'Are you sure you want to quit the program?')
            if answer:
                return False
            else:
                continue
        try:
            start_time, end_time = map(lambda x: datetime.strptime(x, "%I:%M %p").time(), interval_time.split(" - "))
            break
        except ValueError:
            messagebox.showerror('Error', 'Please enter a valid time interval!')
    return start_time, end_time

def name_attendance_file():
    '''
    Generate the name for the attendance file based on the specified time range.

    Returns:
        tuple: A tuple containing the file name, start time, and end time.
    '''
    now = datetime.now()
    date_attendance = now.strftime('%Y-%m-%d')
    while True:
        try:
            start_time, end_time = set_time_attendance()
        except:
            return False
        if start_time <= now.time() <= end_time:
            break
        else:
            messagebox.showerror("Error", "Attendance outside the specified time range!")
    file_name = f"attendance_{start_time}_to_{end_time}_date-{date_attendance}.csv".replace(':', '-')
    return file_name, start_time, end_time

def mark_attendance(name, file_name, start_time, end_time):
    '''
    Fill the name of the person who participates in attendance and the attendance time to the CSV file.

    Args:
        name (str): The name of the person.
        file_name (str): The name of the attendance file.
        start_time (datetime.time): The start time of the attendance.
        end_time (datetime.time): The end time of the attendance.
    '''
    if name == '':
        messagebox.showerror('Error', "You don't have encoded data in the Encode Database!")
        return
    now = datetime.now()
    if not start_time <= now.time() <= end_time:
        messagebox.showerror("Error", "Attendance outside the specified time range!")
        return
    time_attendance = now.strftime('%H:%M:%S')
    file_path = os.path.join('attendance_infor', file_name)
    if os.path.isfile(file_path):          
        while True:
            try:
                with open(f'{file_path}', 'r+') as f:
                    data_table = f.readlines()
                    name_list = [row.split(',')[0] for row in data_table]
                    if name in name_list:
                        messagebox.showwarning('Warning', 'You marked attendance!')
                    else:
                        answer = messagebox.askyesno('Confirm', f'Do you accept mark attendance with name "{name}"?')
                        if answer:
                            f.write(f'{name}, {time_attendance}\n')
                            messagebox.showinfo('Done', f'{name}, you marked attendance successfully!')
                    break
            except:
                messagebox.showerror("Error", f"Please close the file {file_name}!")
    else:
        with open(f'{file_path}', 'w') as f:
            answer = messagebox.askyesno('Confirm', f'Do you accept mark attendance with name "{name}"?')
            if answer:
                f.write('Name, Attendance Time\n')
                f.write(f'{name}, {time_attendance}\n')
                messagebox.showinfo('Done', f'{name}, you marked attendance successfully!')

def convert_to_encode_db():
    '''
    Convert images to face encodings and add them to the Encode Database.

    The function reads the Encode Database to obtain existing person names. It then processes the images in the 'img_db' folder,
    extracts face encodings using the HOG algorithm, and adds the new person names and encodes to the Encode Database.

    Note: The existing Encode Database file should have the format: "name, encoding1, encoding2, ..."

    Returns:
        None
    '''
    # Read Encode Database to take existing person names
    csv_file = "encode_db.csv"
    existing_person_names = []
    with open(csv_file, mode='r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)
        existing_person_names = [row[0] for row in csv_reader]
        
    # Identify new persons and process images to face encoding respectively
    image_path = 'img_db'
    new_person_names = []
    new_encodes = []
    for img in os.listdir(image_path):
        name, ext = os.path.splitext(img)
        if name in existing_person_names:
            continue
        new_person_names.append(name) 
        img_path = os.path.join(image_path, img)
        image = cv2.imread(img_path)  
        image = crop_center_image(image)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # convert BGR to RGB
        image = cv2.GaussianBlur(image, (15, 15), 1)   # apply GaussianBlur filter to denoise the image
        augmented_images = augment_data(image) 
        encode = []
        for aug_img in augmented_images:
            # Extract face encodings by HOG algorithm
            encode_per_img = face_recognition.face_encodings(aug_img, model="hog")[0]  
            encode.append(encode_per_img)
        new_encodes.append(encode)

    # Add new person names and image encodes to Encode Database
    while True:
        try:
            with open(csv_file, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(zip(new_person_names, new_encodes))
            break
        except:
            messagebox.showerror("Error", "Please close the file encode_db.csv!")
    
    messagebox.showinfo('Done', 'Successfully added to Encode Database!')

def add_img_db():
    '''
    Add an image to the Image Database.

    The function prompts the user to select an image file and enter a new name for the image.
    It then copies the selected image to the 'img_db' folder with the new name.

    Returns:
        None
    '''
    # Take image path 
    while True:
        old_path = askopenfilename()
        if old_path == '':
            messagebox.showerror('Error', 'Please choose an image!')
        else:
            break

    # Label image to add to the Database
    while True:
        new_name = askstring("Rename", "Enter a new name for the image:")
        if not new_name: 
            messagebox.showerror('Error', 'Please provide a label for the image!')
        else:
            break
    new_name += ".jpg"

    # Add image to Image Database
    new_path = "img_db/" + new_name
    shutil.copyfile(old_path, new_path)

    messagebox.showinfo('Done', 'Successfully added to Image Database!')

def delete_from_encode_db():
    '''
    Delete a person's data from the Encode Database.

    The function prompts the user to choose a person's name to delete from the Encode Database.
    It opens the 'encode_db.csv' file and a temporary file for writing.
    It reads each row from the original file and writes all rows except the one with the target name to the temporary file.
    If the target name is found and deleted, the 'check' flag is set to True.

    After deleting the target name, it removes the original CSV file and renames the temporary file to the original filename.

    If the target name was found and deleted, it shows a success message.
    Otherwise, it shows an error message indicating that the target name was not found in the Encode Database.

    Returns:
        None
    '''
    target_name = askstring('Delete', 'Choose the person name to delete from the Encode Database:')
    csv_file = "encode_db.csv"
    temp_file = "temp.csv"
    check = False

    # Open the CSV file for reading and a temporary file for writing
    with open(csv_file, 'r') as file, open(temp_file, 'w', newline='') as temp:
        reader = csv.reader(file)
        writer = csv.writer(temp)
        for row in reader:
            if row[0] != target_name:
                writer.writerow(row)
            else:
                check = True
        file.close()

    # Remove the original CSV file and rename the temporary file to the original filename
    while True:
        try:
            os.remove(csv_file)
            break
        except:
            messagebox.showerror("Error", "Please close the file encode_db.csv!")
    os.rename(temp_file, csv_file)

    # Show success message if the target name was found and deleted, otherwise show an error message
    if check == True:
        messagebox.showinfo('Done', f'Successfully deleted "{target_name}" in Encode Database!')
        return
    messagebox.showerror('Error', f'"{target_name}" was not found in the Encode Database')

def delete_from_img_db():
    '''
    Delete a person's image from the Image Database.

    The function prompts the user to choose a person's name to delete from the Image Database.
    It iterates through all files in the 'img_db' folder and checks if the filename matches the target name.
    If a match is found, it removes the file from the folder.

    If the target name was found and deleted, it shows a success message.
    Otherwise, it shows an error message indicating that the target name was not found in the Image Database.

    Returns:
        None
    '''
    target_name = askstring('Delete', 'Choose the person name to delete from the Image Database:')
    img_folder = "img_db"
    for filename in os.listdir(img_folder):
        name, ext = os.path.splitext(filename)
        if name == target_name:
            file_path = os.path.join(img_folder, filename)
            os.remove(file_path)
            messagebox.showinfo('Done', f'Successfully deleted "{target_name}" in Image Database!')
            return
    messagebox.showerror('Error', f'"{target_name}" was not found in the Image Database')

def read_encode_db():
    '''
    Read the Encode Database and retrieve person names, full encodings, and main encodings.

    The function reads the 'encode_db.csv' file and extracts the person names, full encodings,
    and main encodings for each person in the database. It uses the helper function 'str_to_list_arr()'
    to convert the string representation of encodings into lists of encoding arrays.

    Returns:
        person_names_known (list): List of person names in the database.
        encodes_known (list): List of full encodings for each person in the database.
        main_encodes_known (list): List of main encodings for each person in the database.
    '''
    csv_file = "encode_db.csv"
    person_names_known = []  # names in the database
    encodes_known = []       # full encodings in the database
    main_encodes_known = []  # main encodings in the database
    with open(csv_file, mode='r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # skip header row
        for row in csv_reader:
            person_names_known.append(row[0])
            encode = str_to_list_arr(row[1])
            encodes_known.append(encode)
            main_encodes_known.append(encode[3])  # assuming the main encoding is at index 3
    return person_names_known, encodes_known, main_encodes_known

def cur_img_process(img):
    '''
    Detect and recognize the current face of the person in attendance.
    
    The function takes an input image and performs face detection and recognition on the image.
    It uses the 'read_encode_db()' function to retrieve the person names, full encodings, and
    main encodings from the Encode Database. The function then processes the input image to
    detect the face, extract face encodings, calculate face distances, and identify the name
    of the person in attendance and the recognition accuracy.
    
    Arguments:
        img (numpy.ndarray): The input image in BGR format.
        
    Returns:
        name (str): The name of the person in attendance. If the face is not recognized, the name is empty.
        img (numpy.ndarray): The input image with rectangles and text displaying the person's name and accuracy.
    '''
    name = '' # name not in encode database
    text = 'Unknown' # face not found in the database
    person_names_known, encodes_known, main_encodes_known = read_encode_db()
    imgS = crop_center_image(img) 
    imgS = cv2.resize(img, (0,0), None, 0.25, 0.25)  # resize the image for faster processing
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)     # convert BGR to RGB
    imgS = cv2.GaussianBlur(imgS, (15, 15), 1)       # apply GaussianBlur filter to denoise the image

    # Face detection and recognition
    face_locations = face_recognition.face_locations(imgS)
    if len(face_locations) != 0:
        # Identify the position of the current face
        face_loc = face_locations[0]  
        
        if len(person_names_known) != 0:
            # Extract face encodings for the current face using the HOG algorithm
            encode_face = face_recognition.face_encodings(imgS, model="hog")[0] 
            
            # Calculate face distance between current face and faces in the database
            face_dis = face_recognition.face_distance(main_encodes_known, encode_face)  
            
            # Identify the index of the face in the database that is most similar to the current face
            true_index = np.argmin(face_dis)  
            
            # Calculate face distance between current face and faces in 8 brightness levels
            face_dis = face_recognition.face_distance(encodes_known[true_index], encode_face)

            # Identify the name of person in attendance and the accuracy
            err = np.min(face_dis)
            acc = round(100 * (1 - err))    
            if acc > 50:  # face found in the database
                name = person_names_known[true_index]
                text = f"{name} {acc}%"  
            
        # Display the participant's name and accuracy above the rectangle that covers the face
        y1, x2, y2, x1 = face_loc
        y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4         
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 3, cv2.LINE_AA)
    img = cv2.resize(img, (0,0), None, 1/2, 2/3) # take fit dimension for displaying image in UI
    return name, img
