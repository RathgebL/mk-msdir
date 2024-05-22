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


# More testing for move final folder required!

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
def check_exit(input_string): # Function to check if input is '!exit'
    if str(input_string).strip().lower() == '!exit':
        print("Program exited.")
        sys.exit()  # Exit the program

def handle_input(prompt): # Function to check for empty, single character and lower case inputs
    while True:
        user_input = str(input(prompt).strip())
        check_exit(user_input)
        if user_input.strip() == "":
            print("Empty input. Please provide a name.")
        elif len(user_input.strip()) == 1:
            confirm = input("You entered a single character. Would you like to change your input? (y(Default)/n) ").lower()
            check_exit(confirm)
            if confirm == "n":
                return user_input
            elif confirm == "y" or confirm == "":
                continue
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
        elif user_input.strip().islower():
            confirm = input("Lower case input. A capital letter to start the name would be preferred. Would you like to change your input? (y(Default)/n) ").lower()
            check_exit(confirm)
            if confirm == "n":
                return user_input
            elif confirm == "y" or confirm == "":
                continue
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
        else:
            return user_input  # Return valid input

def getmedianumber(): # Function to get the four digit medianumber which is found on every CD cover
    while True:
        try:
            medianumber = int(input("Enter the number of the media (four digit number on the CD cover): "))
            check_exit(medianumber)
            num_str = str(medianumber)
            if len(num_str) == 4:
                return (medianumber)
            else:
                print("Please enter a valid number (four digits).") #change the number of digits if needed
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

def getcomposer(): # Function to get the family and first name. (Middle name optional with first name)
    while True:
        lastname = handle_input("Family name of composer: ")
        firstname = handle_input("First (and middle) name of composer: ")
        return (lastname, firstname)
      
def getinterpreters(): # Function to get number and names of interpreters
    # Get the number of interpreters
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
            interpreters.append(interpreter_name)
            break
            
    return(interpreters) # Return the array of interpreters

def escape(string): # Function to get the desired form for the output
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

def mkms_audiofiles(mydir): # Function to process audiofiles
    # audio file check
    allfiles = []
    for file in os.listdir(mydir):
        if file.lower().endswith((".wav")):
            allfiles.append(file)
    
    allfiles.sort(key=str.lower)
    if len(allfiles) == 0:
        print(f"\nNo audio files in {mydir}!")
        sys.exit(1)
    else:
        audio_extensions = (".wav")
        allfiles = [file for file in os.listdir(mydir) if file.lower().endswith(audio_extensions)]
        allfiles.sort(key=str.lower)

    # box set check
    booklet_folder_status = os.path.join(mydir, 'booklet')
    cdnumber = ""

    while True:
        ask_for_box = input("\nIs this media part of a box set? (y(Default)/n): ").strip().lower()
        check_exit(ask_for_box)
        if ask_for_box not in ("y", "n", ""):
            print("Invalid input. Please enter 'y' or 'n'.")
        else:
            break

    # First CD of a box
    if (ask_for_box == "y" or ask_for_box == "") and os.path.exists(booklet_folder_status):
        cdnumber = 1
    
    if not os.path.exists(booklet_folder_status):    
        while True:
            if ask_for_box == "y" or ask_for_box == "":
                try:
                    cdnumber = int(input("Number of current CD: "))
                    if cdnumber < 0:
                        print("Invalid input. Please provide a natural number.")
                    elif cdnumber == "":
                        print("Empty input. Please provide a natural number.")
                    else:
                        break
                except ValueError:
                    print("Invalid input. Please enter a numeric value.")
            elif ask_for_box == "n":
                break
            else:
                print("Invalid input. Please enter 'y' or 'n'.")

    # mediatitle
    while True:
        mediatitle = handle_input("\nMediatitle: ")
        if (ask_for_box == "y" or ask_for_box == ""):
            mediatitle += f"._CD{str(cdnumber)}"
            print(f"Box number successfully appended. New mediatitle: {mediatitle}")
            break
        else:
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
            print("Invalid input. Please enter 'y' or 'n'.")

    # Excel Sheet
    if (ask_for_box == "y" or ask_for_box == "") and str(cdnumber) != "1":
        print("Skipping Excel sheet creation for subsequent discs.")
    elif ask_for_box == "n" or (ask_for_box == "y" or ask_for_box == "") and str(cdnumber) == "1":
        list_of_interpreters = getinterpreters() # Get an array of interpreters
        medianumber = getmedianumber() # Get the four digit number writen on the CD cover later used as the counter in the excel sheet
        today = datetime.today() 
        formatted_date = today.strftime('%Y-%m-%d') # Get the date in YYYY-MM-DD
        dir_name = os.path.basename(mydir) # Extract the directory name (last part of the path)

        # Prepare the data for the Excel sheet
        if numberofcomposers == 1:
            composer_name = f"{composer[0]}, {composer[1]}"
        else:
            composer_name = 'Verschiedene'

        new_data = {
                    'CD Number': [medianumber],
                    'Composer': [composer_name],
                    'Mediatitle': [mediatitle],
                    'Interpreters': [', '.join(list_of_interpreters)],
                    'Place': [dir_name],
                    'Status': [""],
                    'Date': [formatted_date],
                    'Comment' : [""]
                    }
                    
        # Create a DataFrame from the data and define the path for the Excel file on the desktop
        new_df = pd.DataFrame(new_data)
        desktop_dir = os.path.expanduser('~/Desktop')  # Get the path to the desktop
        excel_file_path = os.path.join(desktop_dir, 'media_data.xlsx')

        # Check if the Excel file exists
        if os.path.exists(excel_file_path):
            existing_df = pd.read_excel(excel_file_path) # Read the existing data
            combined_df = pd.concat([existing_df, new_df], ignore_index=True) # Append the new data to the existing DataFrame
        else:
            combined_df = new_df # If the file does not exist, use the new data as the combined data

        # Write the combined DataFrame to the Excel file
        combined_df.to_excel(excel_file_path, index=False)
        print(f"Excel sheet updated: {excel_file_path}")

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
            workname = handle_input("Name of work: ")
            if any(work[2] == workname for work in works):    #check if input is unique
                print("Work with the same name already exists. Please provide a unique name.")                      
            else:
                break

        if numberofcomposers > 1:
            composer = getcomposer()
            allcomposers.append(composer)

        # multiple movements
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
    prev_movtitle = None

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
                    movtitle = handle_input("Give name for " + str(multimovnr) + ". movement of " + work[2] + ": ")         
                    if movtitle == prev_movtitle:  # Check if input is the same as previous one
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

    return (mediadir, ask_for_box)

# booklet
def extract_number(filename): # Fuction to extracts the numeric portion from the filename
    name = os.path.splitext(filename)[0]  # Remove the file extension
    numeric_part = ''.join(filter(str.isdigit, name))
    if numeric_part:
        return int(numeric_part)
    else:
        return 0

def process_booklet(mydir): # Function to rotate, sharpen, rename and automaticly open booklet files (for Mac user)
    bookletfolder = os.path.join(mydir, 'booklet')
    if not os.path.exists(bookletfolder):
        print("\nNo booklet folder found!")
        return
    else:
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
            while True:
                if ask_to_continue.lower() == "y" or ask_to_continue.lower() == "":
                    break
                elif ask_to_continue == "n":
                    sys.exit()
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")

        else:
            try:
                valid_booklet_files.sort(key=lambda x:
                    (
                        x.startswith('booklet-b'),
                        x.startswith('booklet'),
                        int(''.join(filter(str.isdigit, x))) if any(char.isdigit() for char in x) else float('inf')
                    )
                    if x.lower().endswith(('.jpeg', '.jpg'))
                    else (False, False, 0))

                # Iterate through all files in the folder. Exclude already processed ones.
                for filename in valid_booklet_files:
                    if not filename.lower().startswith("processed_booklet"):
                        original_file_path = os.path.join(bookletfolder, filename) # Full file path

                        # Open the image
                        try:
                            image = Image.open(original_file_path)
                        except Exception as e:
                            print(f"Error opening {filename}: {e}")
                            continue

                        rotated_image = image.transpose(Image.Transpose.ROTATE_270) # Rotate the image to the right 
                        sharpened_image = rotated_image.filter(ImageFilter.SHARPEN) # Adjust sharpness to the highest level
                        processed_filename = f"processed_{filename}".replace(" ", "_") # Rename processed files
                        processed_file_path = os.path.join(bookletfolder, processed_filename)
                        sharpened_image.save(processed_file_path)
                        print(f"Processed: {filename} -> {processed_filename}\tOriginal deleted")
                        os.remove(original_file_path) # Delete the original unprocessed JPEG file immediately after processing

                # Create a list of full file paths and sort them
                new_valid_booklet_files = [file for file in os.listdir(bookletfolder)]
                file_paths = [os.path.join(bookletfolder, file) for file in new_valid_booklet_files]
                file_paths = [path for path in file_paths if not os.path.basename(path).lower().endswith(".ds_store")] # Skip processing for .DS_Store files
                file_paths.sort(key=lambda x: int(''.join(filter(str.isdigit, os.path.basename(x)))) if any(char.isdigit() for char in os.path.basename(x)) else 0)
                print("Booklet processing done.\nBooklet will be opend automatically.\nContinue with renaming audio files in a second...")
                time.sleep(0.5) # Pause the execution for half a second
                subprocess.Popen(["open"] + file_paths) # Open all files in one window (Preview application)         

            except FileNotFoundError:
                return
    

def mkms_bookletfiles(mydir, mediadir): # Function to handle the booklet
    bookletdir = os.path.join(mydir, "booklet")
    newbookletdir = os.path.join(mediadir, "booklet")
    if os.path.exists(bookletdir):
        counter = 1
        bookfiles = os.listdir(bookletdir)
        bookfiles = sorted(bookfiles, key=extract_number)
        special_files = ["processed_booklet-b.jpeg", "processed_booklet.jpeg", "processed_booklet-b.jpg", "processed_booklet.jpg"]

        # Renaming booklet files
        print("\nBooklet renaming:")
        for bookfile in bookfiles:
            if bookfile in special_files:
                newbookfile = bookfile.replace("processed_", "").replace(".jpg", ".jpeg") # Remove "processed_" from the filename and replace "jpg" with "jpeg"
                print(f"Renaming: {bookfile} -> {newbookfile}")
                os.rename(os.path.join(bookletdir, bookfile), os.path.join(bookletdir, newbookfile))
            elif bookfile not in special_files and bookfile.lower().endswith(".jpeg" or ".jpg"):
                file_extension = os.path.splitext(bookfile)[1] # Get the file extension
                newbookfile = "booklet{:04d}{}".format(counter, file_extension.replace("jpeg", "jpg")) # Create the new filename with the number padded with zeros
                print(f"Renaming: {bookfile} -> {newbookfile}") # User feedback
                counter += 1
                os.rename(os.path.join(bookletdir, bookfile), os.path.join(bookletdir, newbookfile))

        # Move the booklet folder and give feedback
        shutil.move(bookletdir, newbookletdir)
        print(f"Moved booklet folder from {bookletdir} -> {newbookletdir}")
    
    elif sys.platform == "win32": # New booklet funtion for Windows user
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

# booklet renaming
mediadir, ask_for_box = mkms_audiofiles(mydir)
mkms_bookletfiles(mydir, mediadir)

# Check if booklet folder is not present and ask_for_box indicates part of a box set
bookletstatus = os.path.join(mydir, 'booklet')

# # DEBUG
# debug = os.path.exists(bookletstatus)
# print(f"Booklet status: {debug}\nBox: {ask_for_box}") 

if not os.path.exists(bookletstatus) and (ask_for_box == "y" or ask_for_box == ""):
    time.sleep(2)
    move_folder = input("\nDo you want to move the finished folder to another location? (y(Default)/n): ").strip().lower()
    check_exit(move_folder)
    while True:
        if move_folder == "y" or move_folder == "":
            time.sleep(2)
            destination_folder = filedialog.askdirectory() 
            time.sleep(1) 
            if destination_folder:
                # Move the finished media directory to the selected destination
                try:
                    shutil.move(mediadir, destination_folder)
                    print(f"Media directory moved to: {destination_folder}")
                    break
                except Exception as e:
                    print(f"Error moving media directory: {e}")
            else:
                print("No destination folder selected. Media directory not moved.")
        elif move_folder == "n":
            print("Media directory not moved.")
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

if sys.platform == "win32":
    print("\nEverything done!")
    input("Press ENTER to close: ")


# 21-05-24