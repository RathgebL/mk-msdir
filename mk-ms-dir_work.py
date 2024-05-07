#!/usr/bin/python
#coding: utf-8

############## MEDIASERVER FILENAMER ##############
## Frank Zalkow, 2011-12
## not possible: Collections
## Updated by Lennat Rathgeb, 2022-23
## now: Python3
## new features:    error handling
##                  default values for yes/no-questions
##                  filedialog for user input of working directory
##                  append data to excel sheet
##                  booklet processing:
##                      - rotating
##                      - sharpening
##                      - renaming
##                      - deleting unprocessed files
##                      - opening all booklet files

# --- importing
import sys
import os
import shutil
from tkinter import filedialog
from PIL import Image, ImageFilter
import pandas as pd
from datetime import datetime
import time

# Import for booklet processing (just on Mac)
if sys.platform == "darwin":
    import subprocess

# --- sub routines
def check_exit(input_string): #Function to check if input is '!exit'
    if str(input_string).strip().lower() == '!exit':
        print("Exiting the program.")
        exit()  # Exit the program

def handle_input(prompt):
    while True:
        user_input = input(prompt).strip().replace(" ", "_")
        if user_input.strip() == "":    # Check if input is empty
                print("Empty input. Please provide a name.")
        elif len(user_input.strip()) == 1:
            confirm = input("You entered a single character. Would you like to change your input? (y(Default)/n) ").lower()
            if confirm == "n":
                break
            elif confirm == "y" or confirm == "":
                continue
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
        elif user_input.strip().islower():
            confirm = input("Lower case input. A capital letter to start the name would be preferred. Would you like to change your input? (y(Default)/n) ").lower()
            if confirm == "n":
                break
            elif confirm == "y" or confirm == "":
                continue
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
        else:
            break

def getmedianumber():
    while True:
        try:
            medianumber = int(input("Enter the number of the media (four digit number on the CD cover): "))
            check_exit(medianumber)  # Check for exit command
            num_str = str(medianumber)
            if len(num_str) == 4:
                return (medianumber)
            else:
                print("Please enter a valid number (four digits).") #change the number of digits if needed
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

def getcomposer():
    while True:
        lastname = handle_input("Family name of composer: ")
        firstname = handle_input("First name of composer: ")
        check_exit(handle_input)
        return (lastname, firstname)
      
def getinterpreters():
    while True:
        try:
            num_interpreters = int(input("Enter the number of interpreters: "))
            check_exit(num_interpreters)
            if num_interpreters > 0:
                break
            else:
                print("Please enter a valid number (greater than zero).")
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

    # Get the names of interpreters
    interpreters = []
    for i in range(num_interpreters):
        while True:
            interpreter_name = handle_input(f"Enter the name of the {i+1}. interpreter (Firstname Lastname): ")
            check_exit(interpreter_name)
            interpreters.append(interpreter_name)
            break
            
    
    return(interpreters)

def escape(string):
    string = string.replace(" ", "_")
    string = string.replace("-", "--")
    string = string.replace(":", "")
    string = string.replace("/", "")
    string = string.replace("\\", "")

    #replacements for windows
    if sys.platform == "win32":
        string = string.replace("?", ".")
        string = string.replace("\"", "\'")
        string = string.replace("<", "")
        string = string.replace(">", "")
        string = string.replace("|", "")
        string = string.replace("*", "")
    
    return string

def mkms_audiofiles(mydir):
    
    # audio files
    audio_extensions = (".wav")
    allfiles = [file for file in os.listdir(mydir) if file.lower().endswith(audio_extensions)]
    allfiles.sort(key=str.lower)

    if not allfiles:
        print("No audio files in " + mydir + "!")
        sys.exit(1)

    # mediatitle
    while True:
        mediatitle = handle_input("\nMediatitle: ")
        check_exit(mediatitle)
        break

    # number of composers
    numberofcomposers = 0
    while numberofcomposers == 0:
        yorn = input("Is the whole media from one composer? (y(Default)/n) ")
        check_exit(yorn)
        if yorn.lower() == "y" or yorn == "":
            numberofcomposers = 1
            composer = getcomposer()        
        elif yorn.lower() == "n":
            while True:
                try:
                    numberofcomposers = int(input("How many composers are mentioned? "))
                    check_exit(numberofcomposers)
                    if numberofcomposers < 2:
                        print("Invalid input. Please enter a number greater than 1.")
                    else:
                        break
                except ValueError:
                    print("Invalid input. Please enter a numeric value.")
        else:
            print("Wrong input...")

    # Excel Sheet
    booklet_folder = os.path.join(mydir, 'booklet')
    if not os.path.exists(booklet_folder):
        while True:
            ask_for_box = input("Is this media part of a box set? (y(Default)/n): ").strip().lower()
            check_exit(ask_for_box)
            if ask_for_box == "y" or ask_for_box == "":
                print("Skipping Excel sheet creation for subsequent discs.")
                break
            elif ask_for_box == "n":
                list_of_interpreters = getinterpreters() # Get an array of interpreters
                medianumber = getmedianumber() # Get the four digit number writen on the CD cover later used as the counter in the excel sheet
                today = datetime.today() # Get the date in YYYY-MM-DD
                dir_name = os.path.basename(mydir) # Extract the directory name (last part of the path)

                # Prepare the data for the Excel sheet
                if numberofcomposers == 1:
                    composer_name = f"{composer[0]}, {composer[1]}"
                else:
                   composer_name = 'Verschiedene'

                data = {
                        'Counter': [medianumber],
                        'Composer': [composer_name],
                        'Mediatitle': [mediatitle],
                        'Interpreters': [', '.join(list_of_interpreters)],
                        'Place': [dir_name],
                        'Status': [""],
                        'Date': [today],
                        'Comment' : [""]
                    }
                    
                # Create a DataFrame from the data
                df = pd.DataFrame(data)

                # Define the path for the Excel file on the desktop
                desktop_dir = os.path.expanduser('~/Desktop')  # Get the path to the desktop
                excel_file_path = os.path.join(desktop_dir, 'media_data.xlsx')

                # Write the DataFrame to an Excel file
                df.to_excel(excel_file_path, index=False)

                print(f"Excel sheet created: {excel_file_path}")
                break
            else:
                print("Invalid input. Please enter 'y' or 'n'.")

    # work stuff
    track = 0
    endtrack = 0
    works = []  # List to store information about works
    allcomposers = []   # only needed when composers between 2 and 4
    total_tracks = len(allfiles) # Get the number of available tracks

    while endtrack < len(allfiles):
        
        # workname + composer
        print(str(len(works) + 1) + ". work of media")
        while True:
            workname = input("Name of work: ")
            check_exit(workname)
            if len(workname.strip()) == 1:  # Check if input length is 1 character
                confirm = input("You entered a single character. Would you like to change your input? (y(Default)/n) ").lower()
                check_exit(confirm)
                if confirm == "y" or confirm == "":
                    continue
                elif confirm == "n":
                    break
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")
            elif workname.strip() == "":    # Check if input is empty
                print("Empty input. Please provide a name of work.")
            elif any(work[2] == workname for work in works):    #check if input is unique
                print("Work with the same name already exists. Please provide a unique name.")           
            elif workname.strip()[0].islower():    # Check if input starts with a capital letter 
                confirm = input("Lower case input. A capital letter to start the name would be preferred. Would you like to change your input? (y(Default)/n) ").lower()
                check_exit(confirm)
                if confirm == "y" or confirm == "":
                    continue
                elif confirm == "n":
                    break
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")           
            else:
                break

        if numberofcomposers > 1:
            composer = getcomposer()
            allcomposers.append(composer)

        while True:
            multimov = input("Does the work range over more than one audio track? (y/n(default)) ")
            check_exit(multimov)
            if multimov.lower() == "y":
                track += 1
            
                while True:
                    endtrack_input = input("It ranges from track " + str(track) + " to track... ")
                    check_exit(endtrack_input)
                    try:
                        endtrack = int(endtrack_input)

                        # Check if the input is within the valid range
                        if track <= endtrack <= total_tracks:
                            break
                        else:
                            print("Invalid input. End track is out of range.")
                            continue
                    except ValueError:
                        print("Invalid input. Please enter a numeric value.")

                if endtrack_input:
                    break
            elif multimov.lower() == "n" or multimov.lower() == "":
                track += 1
                endtrack = track
                break
            else:
                print("Wrong input....")

        works.append((composer[0], composer[1], workname, track, endtrack))
        track = endtrack

    # media directory
    mediadir = os.path.join(mydir, "")
    if numberofcomposers == 1:
        mediadir += composer[0] + "," + composer[1]
    elif numberofcomposers > 4:
        mediadir += "Verschiedene"
    else:
        allcomposers = list(set(allcomposers))
        composersfordir = "+".join([escape(s[0]) + "," + escape(s[1]) for s in allcomposers])
        mediadir += composersfordir

    mediadir += "-" + escape(mediatitle)
    os.mkdir(mediadir)

    # work directories
    filenr = 0
    summary = []
    prev_movtitle = None  # Variable to store the previous movement title

    for work in works:
        workdir = os.path.join(mediadir, escape(work[0]) + "," + escape(work[1]) + "-" + escape(work[2]))        
        
        try:
            os.makedirs(workdir, exist_ok=True)
        except OSError as e:
            print(f"Failed to create directory '{workdir}': {e}")

        if work[3] == work[4]:
            file = allfiles[filenr]
            file_path = os.path.join(mydir, file)
            if os.path.exists(file_path):
                filename = os.path.join(workdir, escape(work[0])) + "-" + escape(work[2]) + os.path.splitext(file)[1]
                summary.append(file + " -> " + filename)
                shutil.move(file_path, filename)
            else:
                print(f"Source file '{file_path}' not found. Skipping.")
            filenr += 1
        else:
            for multimovnr in range(1, (int(work[4]) - int(work[3]) + 2)):
                file = allfiles[filenr]
                while True:
                    movtitle = input("Give name for " + str(multimovnr) + ". movement of " + work[2] + ": ")
                    check_exit(movtitle)         
                    if len(movtitle.strip()) == 1:  # Check if input length is 1 character
                        confirm = input("You entered a single character. Would you like to change your input? (y(Default)/n) ").lower()
                        check_exit(confirm)
                        if confirm == "y" or confirm == "":
                            continue
                        elif confirm == "n":
                            break
                        else:
                            print("Invalid input. Please enter 'y' or 'n'.")
                    elif movtitle.strip() == "":
                        print("Empty input. Please provide a name for the movement.")            
                    elif movtitle.strip()[0].islower():  
                        confirm = input("Lower case input. A capital letter to start the name would be preferred. Would you like to change your input? (y(Default)/n) ").lower()
                        check_exit(confirm)
                        if confirm == "y" or confirm == "":
                            continue
                        elif confirm == "n":
                            break
                        else:
                            print("Invalid input. Please enter 'y' or 'n'.")
                    elif movtitle == prev_movtitle:  # Check if input is the same as previous one
                        confirm = input("You gave the same input as before. Would you like to change your input? (y(Default)/n) ").lower()
                        check_exit(confirm)
                        if confirm == "y" or confirm == "":
                            continue
                        elif confirm == "n":
                            break
                        else:
                            print("Invalid input. Please enter 'y' or 'n'.")
                    else:
                        prev_movtitle = movtitle  # Update prev_movtitle with current input
                        break

                file_path = os.path.join(mydir, file)  # Update file_path for each iteration
                if os.path.exists(file_path):
                    filename = os.path.join(workdir, escape(work[0])) + "-" + escape(work[2]) + "-%02d" % (multimovnr) + "-" + escape(movtitle) + os.path.splitext(file)[1]
                    summary.append(file + " -> " + filename)
                    shutil.move(file_path, filename)
                else:
                    print(f"Source file '{file_path}' not found. Skipping.")
                filenr += 1

    # summary
    print("\n")
    for line in summary:
        print(line)
    #print(f"Interpreters: {list_of_interpreters}")

    return mediadir 

# booklet
def extract_number(filename):
    
    # Extracts the numeric portion from the filename
    name = os.path.splitext(filename)[0]  # Remove the file extension
    numeric_part = ''.join(filter(str.isdigit, name))
    if numeric_part:
        return int(numeric_part)
    else:
        return 0

def process_booklet(mydir):
    
    # Construct the path for the 'booklet' directory within the chosen directory
    bookletfolder = os.path.join(mydir, 'booklet')

    # Check if the 'booklet' directory exists
    if not os.path.exists(bookletfolder):
        return

    try:
        
        # List all files in the booklet folder
        bookletfiles = os.listdir(bookletfolder)

        # Sort the booklet files in the desired order
        bookletfiles.sort(key=lambda x:
            (
                x.startswith('booklet-b'),
                x.startswith('booklet'),
                int(''.join(filter(str.isdigit, x))) if any(char.isdigit() for char in x) else float('inf')
            )
            if x.lower().endswith(('.jpeg', '.jpg'))
            else (False, False, 0))

        # Iterate through all files in the folder. Exclude already processed ones.
        for filename in bookletfiles:
            if filename.lower().endswith((".jpeg", ".jpg")) and not filename.lower().startswith("processed_booklet"):
                
                # Full file path
                original_file_path = os.path.join(bookletfolder, filename)

                # Open the image
                try:
                    image = Image.open(original_file_path)
                except Exception as e:
                    print(f"Error opening {filename}: {e}")
                    continue

                # Rotate the image to the right
                rotated_image = image.transpose(Image.Transpose.ROTATE_270)

                # Adjust sharpness to the highest level
                sharpened_image = rotated_image.filter(ImageFilter.SHARPEN)

                # Rename processed files
                processed_filename = f"processed_{filename}".replace(" ", "_")

                processed_file_path = os.path.join(bookletfolder, processed_filename)
                sharpened_image.save(processed_file_path)
                print(f"Processed: {filename} -> {processed_filename}")

                # Delete the original unprocessed JPEG file immediately after processing
                os.remove(original_file_path)
                print(f"Deleted original: {filename}")

    except FileNotFoundError:
        return
    
# Defining the source and destination directories
def mkms_bookletfiles(mydir, mediadir):
    bookletdir = os.path.join(mydir, "booklet")
    newbookletdir = os.path.join(mediadir, "booklet")

    if os.path.exists(bookletdir):
        counter = 1
        
        #Sort the files
        bookfiles = os.listdir(bookletdir)
        bookfiles = sorted(bookfiles, key=extract_number)
        special_files = ["processed_booklet-b.jpeg", "processed_booklet.jpeg", "processed_booklet-b.jpg", "processed_booklet.jpg"]

        print("\nBooklet renaming:")
        for bookfile in bookfiles:
            if bookfile in special_files:
                # Remove "processed_" from the filename and replace "jpg" with "jpeg"
                newbookfile = bookfile.replace("processed_", "").replace(".jpg", ".jpeg")
                print(f"Renaming: {bookfile} -> {newbookfile}")
                os.rename(os.path.join(bookletdir, bookfile), os.path.join(bookletdir, newbookfile))
            elif bookfile not in special_files and bookfile.lower().endswith(".jpeg" or ".jpg"):
                # Get the file extension
                file_extension = os.path.splitext(bookfile)[1]

                # Create the new filename with the number padded with zeros
                newbookfile = "booklet{:04d}{}".format(counter, file_extension.replace("jpeg", "jpg"))

                # User feedback
                print(f"Renaming: {bookfile} -> {newbookfile}")

                # Increment the counter for the next file
                counter += 1

                os.rename(os.path.join(bookletdir, bookfile), os.path.join(bookletdir, newbookfile))

        # Move the booklet folder and give feedback
        shutil.move(bookletdir, newbookletdir)
        print(f"\nMoved booklet folder from {bookletdir} -> {newbookletdir}")

    elif sys.platform == "win32":
        askbookdir = ""
        while True:
            askbookdir = input("No booklet directory found. Do you want to create one? (y(Default)/n) ") 
            if askbookdir.lower() == "y" or askbookdir == "": 
                os.mkdir(newbookletdir)
                print("New booklet directory created ready to put files in.")
                break
            elif askbookdir == "n":
                break
            else:
                print("Invalid input. Please enter 'y' or 'n'.")

# --- run
print("To quit at any time just type '!exit'.")
print("To get the default value just press ENTER.")

while True:
    # Ask for directory
    mydir = filedialog.askdirectory()

    # Check if directory is not empty
    if mydir and mydir != '/':
        print("\nChosen directory:", mydir)
        break
    else:
        print("\nNo directory chosen. Please choose a directory.")

# Process booklet for Mac
if sys.platform == "darwin":
    process_booklet(mydir)

    # Check if the booklet folder was found and if there are files inside
    bookletfolder = os.path.join(mydir, "booklet")

    if os.path.exists(bookletfolder):
        
        # Creat a list of valid booklet files
        valid_booklet_files = [file for file in os.listdir(bookletfolder) if file.lower().endswith((".jpeg", ".jpg"))]

        if not valid_booklet_files:
            print(f"\nNo valid files found in {bookletfolder}!")

            # see if there are any files in the booklet folder
            any_files_in_bookletfolder = [file for file in os.listdir(bookletfolder)]
            num_files = len(any_files_in_bookletfolder)
            if num_files >= 1:
                print("List of files in " + bookletfolder + ":")
                for file in any_files_in_bookletfolder:
                    print(f"\tFilename: {file}")

            # Ask the user to continue or delete the folder
            while True:
                ask_to_delete = input("Would you like to delete the booklet folder? (y/n(Default)): ")
                check_exit(ask_to_delete)
                if ask_to_delete.lower() == "y":
                    try:
                        shutil.rmtree(bookletfolder)
                        print("Booklet folder deleted.\n")
                        break
                    except Exception as e:
                        print(f"Error deleting the booklet folder: {e}")
                        continue
                elif ask_to_delete == "n" or ask_to_delete == "":
                    break
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")
            
            ask_to_continue = input("Do you want to continue with renaming the audio files (y(Default)/n): ")
            check_exit(ask_to_continue)
            if ask_to_continue.lower() != "y":
                sys.exit()

        else:  
            if sys.platform == "darwin":
                
                # Create a list of full file paths
                file_paths = [os.path.join(bookletfolder, file) for file in valid_booklet_files]

                # Sort the file paths based on their numeric values
                file_paths.sort(key=lambda x: int(''.join(filter(str.isdigit, os.path.basename(x)))) if any(char.isdigit() for char in os.path.basename(x)) else 0)

                # Add debug prints
                # print("Sorted file paths:")
                # for path in file_paths:
                #     print(path)

                # Skip processing for .DS_Store files
                file_paths = [path for path in file_paths if not os.path.basename(path).lower().endswith(".ds_store")]

                print("Booklet processing done.\nBooklet will be opend automatically.\nContinue with renaming audio files in a second...")
                
                # Pause the execution for 1 second
                time.sleep(0.5)

                # Open all files in one window (Preview application)
                subprocess.Popen(["open"] + file_paths)

    else:
        print("\nNo booklet folder found!")

# Check for audio files in the final directory (mediadir)
allfiles = []
for file in os.listdir(mydir):
    if file.lower().endswith((".wav")):
        allfiles.append(file)
allfiles.sort(key=str.lower)

if len(allfiles) == 0:
    print(f"\nNo audio files in {mydir}!")
    sys.exit(1)

# booklet renaming
mediadir = mkms_audiofiles(mydir)
mkms_bookletfiles(mydir, mediadir)

if sys.platform == "win32":
    print("\nEverything done!")
    input("Press ENTER to close: ")

# 07-05-24