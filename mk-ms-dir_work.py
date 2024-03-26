#!/usr/bin/python
#coding: utf-8

############## MEDIASERVER FILENAMER ##############
## Frank Zalkow, 2011-12
## not possible: Collections
## Updated by Lennat Rathgeb, 2022-23
## now: Python3
## new features:    renaming of scans if in booklet folder
##                  error handling
##                  opens finder window for user input
##                  booklet processing


# --- importing
import sys
import os
import shutil
from tkinter import filedialog
from PIL import Image, ImageFilter
import subprocess

# Import for booklet processing (just on Mac)
if sys.platform == "darwin":
    import subprocess

# --- sub routines
def getcomposer():
    while True:
        lastname = input("Family name of composer: ").strip().replace(" ", "_")
        firstname = input("First name of composer: ").strip().replace(" ", "_")

        if firstname == "" or lastname == "":
            print("Invalid input. Please provide both a family name and a first name.")
        else:
            return (lastname, firstname)

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
        mediatitle = input("\nMediatitle: ").strip()

        if mediatitle == "":
            print("Invalid input. Please provide a titel.")
        else:
            break

    # number of composers
    numberofcomposers = 0
    while numberofcomposers == 0:
        yorn = input("Is the whole media from one composer? (y/n) ")
        
        if yorn.lower() == "y":
            numberofcomposers = 1
            composer = getcomposer()        
        elif yorn.lower() == "n":
            while True:
                try:
                    numberofcomposers = int(input("How many composers are mentioned? "))
                    if numberofcomposers < 2:
                        print("Invalid input. Please enter a number greater than 1.")
                    else:
                        break
                except ValueError:
                    print("Invalid input. Please enter a numeric value.")
        else:
            print("Wrong input...")

    # work stuff
    track = 0
    endtrack = 0
    works = []  # List to store information about works
    allcomposers = []   # only needed when composers between 2 and 4

    while endtrack < len(allfiles):
        
        # workname + composer
        print(str(len(works) + 1) + ". work of media")
        while True:
            workname = input("Name of work: ")

            if len(workname.strip()) == 1:  # Check if input length is 1 character
                confirm = input("You entered a single character. Are you sure about your input? (y/n) ").lower()
                
                if confirm == "n":
                    continue
                elif confirm == "y":
                    break
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")
            elif workname.strip() == "":    # Check if input is empty
                print("Invalid input. Please provide a name of work.")
            elif any(work[2] == workname for work in works):    #check if input is unique
                print("Work with the same name already exists. Please provide a unique name.")           
            elif workname.strip()[0].islower():    # Check if input starts with a capital letter 
                confirm = input("Lower case input. A capital letter to start the name would be preferred. Would you like to change your input? (y/n) ").lower()
                
                if confirm == "y":
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

        multimov = ""
        while multimov.lower() not in ["y", "n"]:
            multimov = input("Does the work range over more than one audio track? (y/n) ")

            if multimov.lower() == "y":
                track += 1
                endtrack_input = input("It ranges from track " + str(track) + " to track... ")

                while not endtrack_input.isdigit():
                    print("Invalid input. Please enter a numeric value.")
                    endtrack_input = input("It ranges from track " + str(track) + " to track... ")
                endtrack = int(endtrack_input)
            elif multimov.lower() == "n":
                track += 1
                endtrack = track            
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

                    if len(movtitle.strip()) == 1:  # Check if input length is 1 character
                        confirm = input("You entered a single character. Are you sure about your input? (y/n) ").lower()
                        if confirm == "n":
                            continue
                        elif confirm == "y":
                            break
                        else:
                            print("Invalid input. Please enter 'y' or 'n'.")
                    elif movtitle.strip() == "":
                        print("Invalid input. Please provide a name for the movement.")            
                    elif movtitle.strip()[0].islower():  
                        confirm = input("Lower case input. A capital letter to start the name would be preferred. Would you like to change your input? (y/n) ").lower()
                        if confirm == "y":
                            continue
                        elif confirm == "n":
                            break
                        else:
                            print("Invalid input. Please enter 'y' or 'n'.")
                    else:
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

                # Rename all processed files except: "booklet" and "booklet-b" files
                excluded_files = ["booklet-b.jpeg", "booklet.jpeg", "booklet-b.jpg", "booklet.jpg"]
                if filename in excluded_files:
                    processed_filename = f"{filename}"
                else:
                    processed_filename = f"processed_{filename}"

                processed_file_path = os.path.join(bookletfolder, processed_filename)
                sharpened_image.save(processed_file_path)
                print(f"Processed: {filename} -> {processed_filename}")

                # Delete the original unprocessed JPEG file immediately after processing
                if filename not in excluded_files:
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

        # Exclude the files which are already named correctly
        excluded_files = ["booklet-b.jpeg", "booklet.jpeg", "booklet-b.jpg", "booklet.jpg", ".DS_Store"]

        print("\nBooklet renaming:")
        for bookfile in bookfiles:
            if bookfile not in excluded_files and bookfile.lower().endswith(".jpeg" or ".jpg"):

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
        while askbookdir.lower() not in ["y", "n"]:
            askbookdir = input("No booklet directory found. Do you want to create one? (y/n) ") 
        if askbookdir.lower() == "y": 
            os.mkdir(newbookletdir)
            print("New booklet directory created ready to put files in.")

# --- run

# Get the directory from the user
mydir = filedialog.askdirectory()

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
            ask_to_delete = input("Do you like to delete the booklet folder? (y/n): ")
            if ask_to_delete.lower() == "y":
                try:
                    shutil.rmtree(bookletfolder)
                    print("Booklet folder deleted.\n")
                except Exception as e:
                    print(f"Error deleting the booklet folder: {e}")
            
            ask_to_continue = input("Do you want to continue with renaming the audio files (y/n): ")
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

                print("Booklet processing done.")
                input("\nPress ENTER to continue with renaming the audio files! (booklet will automatically be opened)")

                # Open all files in one window (Preview application)
                subprocess.Popen(["open"] + file_paths)

    else:
        print("\nNo booklet folder found!")
        user_input = input("Press ENTER if you want to continue with renaming the audio files without booklet processing or type \"EXIT\" to stop: ")

        if user_input.lower() == "exit":
            sys.exit()

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

# 26-03-24