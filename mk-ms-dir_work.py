#!/usr/bin/python
#coding: utf-8

############## MEDIASERVER FILENAMER ##############
## Frank Zalkow, 2011-12
## not possible: Collections
## Updated by Lennat Rathgeb, 2022-23
## now: Python3
## new features:    error handling
##                  default values for yes/no-questions
##                  ebd for previous composer
##                  filedialog for user input of working directory
##                  append data to excel sheet
##                  creat box/find box and move folders to it
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
import re
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

def check_quotation_balance(user_input):
    quotes = {"'": "'", "\"": "\"", "“": "”", "‘": "’", "«": "»", "‹": "›", "„": "”"}
    reverse_quotes = {v: k for k, v in quotes.items()}
    
    def validate_quotes(string):
        stack = []
        previous_char = None
        
        for i, char in enumerate(string):
            if char == '(':  # Skip parentheses
                continue
            
            # Check for opening or closing quotation marks
            if char in quotes.keys() or char in quotes.values():
                if previous_char is None or previous_char.isspace():  # If space before, it's an opening quote
                    if char in quotes.keys():  # Opening quote
                        stack.append(char)  # Add opening quote to stack
                    elif char in quotes.values():  # Found a closing quote, but expected an opening
                        expected_opening = reverse_quotes[char]
                        print(f"Error: unexpected location for closing quotation mark '{char}'. Expected quotation mark: '{expected_opening}'") # Error: found closing quote but expected an opening
                        return False, string, stack
                else:  # It's a closing quote
                    if stack:
                        expected = quotes[stack[-1]]  # Get the matching closing quote for the last opening
                        if char == expected:
                            stack.pop()  # Correct match, remove opening from stack
                        else:  # Mismatch between opening and closing quotes
                            return False, string, stack
                    else:  # No opening for the closing quote
                        expected_opening = reverse_quotes[char]
                        print(f"Error: Missing opening quotation mark. Expected '{expected_opening}' for '{char}'.")
                        return False, string, stack
            
            previous_char = char
        
        # If there's something left in the stack, it means an opening quote was not closed
        if stack:
            expected_closing = quotes[stack[-1]]
            print(f"Error: Missing closing quotation mark. Expected '{expected_closing}'.")
            return False, "!stop", stack
        
        return True, string, stack

    is_balanced, corrected_input, stack = validate_quotes(user_input)

    # Handle mismatch and give user a chance to fix
    while not is_balanced:
        # If the mismatch occurs because of an incorrect closing quote, handle it here
        if stack:  # For opening quote without a match
            expected = quotes[stack[-1]]
            for i, char in enumerate(corrected_input):
                if char in quotes.values() and (not stack or quotes[stack[-1]] != char):
                    while True:
                        confirm = input(f"Error: Found '{char}' but expected '{expected}'. Would you like to change it? (y(Default)/n) ")
                        check_exit(confirm)
                        if confirm == "y" or confirm == "":
                            # Replace the wrong quote with the expected one
                            corrected_input = corrected_input[:i] + expected + corrected_input[i+1:]
                            print(f"The input has been corrected to: {corrected_input}")
                            if stack:
                                stack.pop()  # Remove the matched opening quote from stack
                            break
                        elif confirm == "n":
                            break
                        else:
                            print("Invalid input. Please enter 'y' or 'n'.")
            
            if not corrected_input == "!stop":
                is_balanced, corrected_input, stack = validate_quotes(corrected_input) # After correction, revalidate the whole string from the beginning
            else:
                break
        else:
            break

    return is_balanced, corrected_input

def handle_input(prompt): # Function to check for empty, single character and lower case inputs
    while True:
        user_input = str(input(prompt).strip())
        check_exit(user_input)
       
        exceptions = {"!exit", "none", "ebd", "¡", "“", "¶"}
        if user_input.lower() in exceptions:
            return user_input
        
        if user_input.strip() == "":
            print("Empty input not possible!")
            continue

        if user_input.strip().endswith(","):
            user_input = user_input[:-1].strip()
            print("A comma at the end of your input has been removed!")

        is_balanced, corrected_input = check_quotation_balance(user_input) # Check for quotation mark balance and get corrected input

        if not is_balanced:  # If the quotation marks are unbalanced
            confirm = input("Your input has mismatched quotation marks. Would you like to change your input? (y(Default)/n) ")
            check_exit(confirm)
            if confirm == "y" or confirm == "":  # If user confirms, use the corrected input
                user_input = corrected_input
                continue  # Re-check the input
            elif confirm not in ("n", "y", ""):  # Handle invalid input
                print("Invalid input. Please enter 'y' or 'n'.")
                continue
        else:
            user_input = corrected_input  # If the input was already balanced, use the corrected version
        
        if len(user_input.strip()) == 1: # Check for single character inputs and lowercase
            confirm = input("You entered a single character. Would you like to change your input? (y(Default)/n) ").strip().lower()
            check_exit(confirm)
            if confirm == "n":
                if user_input[0].islower():
                    confirm = input("Lower case input. A capital letter to start the name would be preferred. Would you like to change your input? (y(Default)/n) ").strip().lower()
                    check_exit(confirm)
                    if confirm == "n":
                        return user_input
                    elif confirm == "y" or confirm == "":
                        continue
                    else:
                        print("Invalid input. Please enter 'y' or 'n'.")
                        continue
                return user_input
            elif confirm in {"y", ""}:
                continue
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
                continue

        while True: # Check for uppercase characters in the moddle of words
            words = user_input.split()
            char_exceptions = { "„","\"", "\'", "‚", "‘" "-", "(", "/", "‘", "«", "»", "‹", "›"}
            for i, word in enumerate(words):             
                if "-" in word and not word.isupper():
                    if word[0] not in char_exceptions:
                        parts = word.split('-')  # Split the word by hyphen
                        updated_parts = []
                        for part in parts:
                            if part and part[1:].isupper():  # Check if part has uppercase after the first character
                                confirm = input(f"Your input contains uppercase letters in the middle of the word '{word}'. Would you like to convert these to lowercase (except the first letter)? (y(Default)/n) ").strip().lower()
                                check_exit(confirm)
                                if (confirm == "y" or confirm == ""):
                                    updated_part = part[0] + part[1:].lower()  # Change everything after the first character to lowercase
                                    updated_parts.append(updated_part)
                                elif not confirm == "n":
                                    print("Invalid input. Please enter 'y' or 'n'.")
                                    continue
                            else:
                                updated_parts.append(part)  # No issue, keep it as is                                
                        
                        updated_word = '-'.join(updated_parts)
                        if updated_word != word:  # If any part was changed, notify the user
                            words[i] = updated_word
                            print(f"The word '{word}' has been changed to: '{updated_word}'")
                    elif word[0] in char_exceptions:
                        parts = re.split(r'(?<=\w)(?=-)', word)  # Split the word infront of the hyphen and include it in the second part via lookahead and re.split
                        updated_parts = []
                        for part in parts:
                            if part and part[2:].isupper():  # Check if part has uppercase after the first character
                                confirm = input(f"Your input contains uppercase letters in the middle of the word '{word}'. Would you like to convert these to lowercase (except the first letter)? (y(Default)/n) ").strip().lower()
                                check_exit(confirm)
                                if (confirm == "y" or confirm == ""):
                                    updated_part = part[0] + part[1] + part[2:].lower()  # Change everything after the first character to lowercase
                                    updated_parts.append(updated_part)
                                elif not confirm == "n":
                                    print("Invalid input. Please enter 'y' or 'n'.")
                                    continue
                            else:
                                updated_parts.append(part)  # No issue, keep it as is                                
                        
                        updated_word = '-'.join(updated_parts)
                        if updated_word != word:  # If any part was changed, notify the user
                            words[i] = updated_word
                            print(f"The word '{word}' has been changed to: '{updated_word}'")
                    elif not word.isupper() and any(c.isupper() for c in word[1:]) and word[0] not in char_exceptions:
                        confirm = input(f"Your input contains uppercase letters in the middle of the word '{word}'. Would you like to convert these to lowercase (except the first letter)? (y(Default)/n) ").strip().lower()
                        check_exit(confirm)
                        if (confirm == "y" or confirm == ""):
                            updated_word = word[0] + word[1:].lower()
                            words[i] = updated_word
                            print(f"The word '{word}' has been changed to: '{updated_word}'")
                        elif not confirm == "n":
                            print("Invalid input. Please enter 'y' or 'n'.")
                            continue
                    elif not word.isupper() and any(c.isupper() for c in word[2:]) and word[0] in char_exceptions:
                        confirm = input(f"Your input contains uppercase letters in the middle of the word '{word}'. Would you like to convert these to lowercase (except the first letter)? (y(Default)/n) ").strip().lower()
                        check_exit(confirm)
                        if word[0] in char_exceptions and (confirm == "y" or confirm == ""):
                            updated_word = word[0] + word[1] + word[2:].lower()
                            words[i] = updated_word
                            print(f"The word '{word}' has been changed to: '{updated_word}'")
                        elif not confirm == "n":
                            print("Invalid input. Please enter 'y' or 'n'.")
                            continue

            user_input = ' '.join(words)  # Reconstruct the user input from the modified words list
            break
        
        if user_input[0].islower(): # check for lowercase input
            confirm = input("Lower case input. A capital letter at the start would be preferred. Would you like to change your input? (y(Default)/n) ").strip().lower()
            check_exit(confirm)
            if confirm == "n":
                return user_input
            elif confirm == "y" or confirm == "":
                continue
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
                continue

        return user_input

def process_booklet(mydir): # Function to rotate, sharpen, rename and automaticly open booklet files (for Mac user)
    bookletfolder = os.path.join(mydir, 'booklet')
    if not os.path.exists(bookletfolder):
        print("\nNo booklet folder found!")
        return
    susbooklet = any(file.lower().startswith("booklet0") for file in os.listdir(bookletfolder)) # Check if any file in the booklet folder starts with "booklet0"
    if susbooklet: # Exclude folders that probably are already finished
        print("Finished booklet spotted. Please check the folder.\nContinuing without booklet processing...")
        return
    else:
        # Creat a list of valid booklet files
        valid_booklet_files = [file for file in os.listdir(bookletfolder) if not file.lower().startswith("processed_booklet") and file.lower().endswith((".jpeg", ".jpg"))]
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
                ask_to_delete = input("Would you like to delete the booklet folder? (y/n(Default)) ").strip().lower()
                check_exit(ask_to_delete)
                if ask_to_delete == "y":
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
            
            ask_to_continue = input("Do you want to continue with renaming the audio files? (y(Default)/n) ").strip().lower()
            check_exit(ask_to_continue)
            processed_booklet_files = [file for file in os.listdir(bookletfolder) if file.lower().startswith("processed_booklet") and file.lower().endswith((".jpeg", ".jpg"))]
            while True:
                if ask_to_continue == "y" or ask_to_continue == "":
                    print("Booklet will be opend automatically.\nContinue with renaming audio files in a second...")
                    file_paths = [os.path.join(bookletfolder, file) for file in processed_booklet_files]
                    file_paths.sort(key=lambda x: int(''.join(filter(str.isdigit, os.path.basename(x)))) if any(char.isdigit() for char in os.path.basename(x)) else 0)
                    time.sleep(0.5) # Pause the execution for half a second
                    subprocess.Popen(["open"] + file_paths) # Open all files in one window (Preview application)
                    break
                elif ask_to_continue == "n":
                    print("Program exited.")
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
            
                # Iterate through all files in the folder. Exclude already processed ones from an unfinished run and from finished booklet folders for up to 999 booklet files.
                for filename in valid_booklet_files:
                    if not filename.lower().startswith("processed_booklet") and not filename.lower().startswith("booklet0"): # Change here if booklet names after scanning changed to a differt format
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
            
def extract_number(filename): # Fuction to extracts the numeric portion from the filename
    name = os.path.splitext(filename)[0]  # Remove the file extension
    numeric_part = ''.join(filter(str.isdigit, name))
    if numeric_part:
        return int(numeric_part)
    else:
        return 0

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
        firstname = handle_input("First (and middle) name of composer: ")
        
        if firstname.strip().lower() == "none":
            firstname = ""
            while True:
                anonyme = input("Should 'Anonymous' be taken as lastname? (y(Default)/n) ")
                if anonyme.strip().lower() == "" or anonyme.strip().lower() == "y":
                    lastname = "Anonymous"
                    print("Last name has been successfully changed to 'Anonymous'.")
                    break
                elif anonyme.strip().lower() == "n":
                    lastname = handle_input("Family name of composer: ")
                    break
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")
                    continue
        elif firstname.strip().lower() == "ebd":
            print("Input set to previous composer:")
            lastname = "l-ebd"
        else:
            lastname = handle_input("Family name of composer: ")

        return [lastname, firstname]
    
def getnumberofcomposers(): # Function to get number of composers
    numberofcomposers = 0
    while numberofcomposers == 0:
        yorn = input("Is the whole media from one composer? (y(Default)/n) ")
        check_exit(yorn)
        if yorn.strip().lower() == "y" or yorn == "":
            numberofcomposers = 1
            composer = getcomposer()        
        elif yorn.strip().lower() == "n":
            composer = [str, str] # define composer empty to avoid referencing before assignement
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

    return numberofcomposers, composer
         
def getinterpreters(): # Function to get number and names of interpreters
    # Get the number of interpreters
    while True:
        try:
            interpreters = int(input("Enter the number of interpreters: "))
            check_exit(interpreters)
            if interpreters > 0:
                break
            else:
                print("Please enter a valid number (greater than zero).")
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

    # Get the names of interpreters
    interpreterlist = []
    for i in range(interpreters):
        while True:
            interpretername = handle_input(f"Enter the name of the {i+1}. interpreter (Firstname Lastname): ")
            interpreterlist.append(interpretername)
            break
            
    return(interpreterlist) # Return the array of interpreters

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

def files(mydir): # Audio file check
    allfiles = [file for file in os.listdir(mydir) if file.lower().endswith(".wav")]
    allfiles.sort(key=str.lower)
    if len(allfiles) == 0:
        print(f"\nNo audio files in {mydir}!")
        sys.exit(1)
    else:
        return allfiles
    
def boxcheck(mydir): # Function to check for box set
    bookletpath = os.path.join(mydir, 'booklet')
    bookletstatus = 0
    if os.path.exists(bookletpath):
        bookletstatus = 1
    cdnumber = ""

    while True:
        askbox = input("\nIs this media part of a box set? (y(Default)/n) ").strip().lower()
        check_exit(askbox)
        if askbox not in ("y", "n", ""):
            print("Invalid input. Please enter 'y' or 'n'.")
        else:
            break

    return (bookletstatus, cdnumber, askbox)

def getcdnumber(askbox,bookletstatus, cdnumber): # First CD of a box
    if (askbox == "y" or askbox == "") and bookletstatus == 1:
        cdnumber = 1

    if bookletstatus == 0:    
        while True:
            if askbox == "y" or askbox == "":
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
            elif askbox == "n":
                break
            else:
                print("Invalid input. Please enter 'y' or 'n'.")

    return cdnumber

def getmediatitle(askbox, cdnumber): # Function to get the mediatitle
    mediatitle = handle_input("\nMediatitle: ")
    if (askbox == "y" or askbox == ""):
        mediatitle += f"._CD{str(cdnumber)}"
        print(f"Box number successfully appended. New mediatitle: {mediatitle}")
        
    return mediatitle

def dirname(mydir): # Function to extract the directory name of mydir (last part of the path)
    dirname = os.path.basename(mydir) 
    return dirname

def dateform(today): # Function to get the date in YYYY-MM-DD
    dateform = today.strftime('%Y-%m-%d') 
    return dateform

def excelinfo(numberofcomposers, composer):
    # Prepare the data for the Excel sheet
    interpreterlist = getinterpreters()
    medianumber = getmedianumber()

    if numberofcomposers == 1:
        composerlist = [composer[0], composer[1]]
    else:
        composerlist = 'Verschiedene'
    
    return interpreterlist, medianumber, composerlist

def excel(interpreterlist, composerlist, medianumber, dateform, dirname, mediatitle):
    try:
        new_data = {
                    'CD Number': [medianumber],
                    'Composer': [f"{composerlist[0]}, {composerlist[1]}"],
                    'Mediatitle': [mediatitle],
                    'Interpreters': [', '.join(interpreterlist)],
                    'Place': [dirname],
                    'Status': [""],
                    'Date': [dateform],
                    'Comment' : [""]
                    }
                        
        # Create a DataFrame from the data and define the path for the Excel file on the desktop
        new_df = pd.DataFrame(new_data)
        desktop = os.path.expanduser('~/Desktop')  # Get the path to the desktop
        excelpath = os.path.join(desktop, 'Neues_Logbuch.xlsx')

        # Check if the Excel file exists
        if os.path.exists(excelpath):
            existing_df = pd.read_excel(excelpath) # Read the existing data
            combined_df = pd.concat([existing_df, new_df], ignore_index=True) # Append the new data to the existing DataFrame
            return combined_df, excelpath, medianumber
        else:
            combined_df = new_df # If the file does not exist, use the new data as the combined data
            return combined_df, excelpath, medianumber
    except Exception as e:
        print(f"\nError: {e}")

def writeexcel(combined_df, excelpath): # Function to write to the combined DataFrame to the Excel file
    try:    
        combined_df.to_excel(excelpath, index=False)
        print(f"Excel sheet updated: {excelpath}")
    except Exception as e:
        print(f"\nError: {e}\nExcel sheet must be updated manually.")

def getwork(allfiles, numberofcomposers, composer):
    # work stuff
    track = 0
    tracknumber = 0
    endtrack = 0
    works = []  # List to store information about works
    composers = [] # List to store composer names
    allcomposers = []   # only needed when composers between 2 and 4
    total_tracks = len(allfiles) # Get the number of available tracks
    
    
    while endtrack < len(allfiles):
        
        # workname + composer
        tracknumber = track + 1
        print(str(len(works) + 1) + ". Work of media (Track: " + str(tracknumber) + ")")
        while True:
            workname = handle_input("Name of work: ")
            if any(work[2] == workname for work in works) and numberofcomposers == 1: # Check if the workname already exist in the works list for CDs with just one composer
                print("Work with the same name already exists. Please provide a unique name.")                      
            else:
                break

        if numberofcomposers > 1:
            composer = getcomposer()
            composers.append(composer) # List of composer names (lastname, firstname) as put in (doubles possible)
            if len(composers) > 1 and composers[-1][1] == "ebd":
                composer = composers[-2]
                composers[-1] = composers [-2]
                print(f"\tFirst name: {composers[-1][1]}\n\tLast name: {composers[-1][0]}")
            
            if any(work[2] == workname and [work[0], work[1]] == composer for work in works): # Check if both the workname and the composer already exist in the works list for CDs with multiple composers
                print("Work with the same name and composer already exists. Please provide a unique pair of work name and composer.")
                continue                      

            allcomposers.append(composer) # List of composers. No doubles
            allcomposers = list(set(tuple(comp) for comp in allcomposers))


        # multiple movements
        while True:
            multimov = input("Does the work range over more than one audio track? (y/n(default)) ").strip().lower()
            check_exit(multimov)
            if multimov == "y":
                track += 1
                while True:
                    endtrack_input = input("It ranges from track " + str(track) + " to track... ")
                    check_exit(endtrack_input)
                    try:
                        endtrack = int(endtrack_input)
                        if track <= endtrack <= total_tracks: # Check if the input is within the valid range
                            break
                        else:
                            print("Invalid input. End track is out of range.")
                            continue
                    except ValueError:
                        print("Invalid input. Please enter a numeric value.")
                
                if endtrack_input:
                    break
            elif multimov == "n" or multimov == "":
                track += 1
                endtrack = track
                break
            else:
                print("Wrong input....")

        works.append([composer[0], composer[1], workname, track, endtrack])
        track = endtrack

    return works, allcomposers

def getmediadir(mydir, numberofcomposers, composer, allcomposers, mediatitle): # Function to get media directory
    mediadir = os.path.join(mydir, "")
    if numberofcomposers == 1:
        if composer[0] == "Anonymous" or composer[1] == "":
            mediadir += escape(composer[0])
        else:
            mediadir += escape(composer[0]) + "," + escape(composer[1])
    elif numberofcomposers > 4:
        mediadir += "Verschiedene"
    else:
        allcomposers = list(set(allcomposers))
        composersfordir = "+".join([escape(s[0]) + "," + escape(s[1]) for s in allcomposers])
        mediadir += composersfordir

    mediadir += "-" + escape(mediatitle)
    os.mkdir(mediadir) # Create folder (Familyname,Firstname-Mediatitle)
    
    return mediadir

def getworkdir(works, allfiles, mediadir): # Function for work directories
    filenr = 0
    movlist = []
    summary = []
    prev_movtitle = None
    

    for work in works:
        if work[0] == "Anonymous" or work[1] == "":
            workdir = os.path.join(mediadir, escape(work[0]) + "-" + escape(work[2])) # leaves out the "," and first name if the composer is not known        
        else:
            workdir = os.path.join(mediadir, escape(work[0]) + "," + escape(work[1]) + "-" + escape(work[2]))

        try:
            os.makedirs(workdir, exist_ok=True) # Create folder (Familyname,Firstname-Workname)
        except OSError as e:
            print(f"Failed to create directory '{workdir}': {e}")

        if work[3] == work[4]:
            file = allfiles[filenr]
            file_path = os.path.join(mydir, file)
            if os.path.exists(file_path):
                filename = os.path.join(workdir, escape(work[0])) + "-" + escape(work[2]) + os.path.splitext(file)[1] # Create filepath (/Users/Username/Desktop/mydir/Mediadir/Familyname,Firstname-Workname/Familyname-Workname.Fileextansion(wav))
                summary.append(file + " -> " + filename)
                shutil.move(file_path, filename)
            else:
                print(f"Source file '{file_path}' not found. Skipping.")
            filenr += 1
        else:
            tracknumber = work[3]
            for multimovnr in range(1, (int(work[4]) - int(work[3]) + 2)):
                file = allfiles[filenr]             
                while True:
                    movtitle = handle_input("Give name for " + str(multimovnr) + ". movement of " + work[2] + " (Track: " + str(tracknumber) + "): ")
                    tracknumber += 1
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
                        prev_movtitle = movtitle  # Update prev_movtitle with current input before shortcuts
                        if movtitle == "¡":
                            movtitle = "Allegro"
                            print("Shortcut applied. Name of movement changed to 'Allegro'.")
                        elif movtitle == "“":
                            movtitle = "Andante"
                            print("Shortcut applied. Name of movement changed to 'Andante'.")
                        elif movtitle == "¶":
                            movtitle = "Adagio"
                            print("Shortcut applied. Name of movement changed to 'Adagio'.")
                        break

                movlist.append([int(filenr), movtitle, work[2]])
                file_path = os.path.join(mydir, file)  # Update file_path for each iteration
                if os.path.exists(file_path):
                    filename = os.path.join(workdir, escape(work[0])) + "-" + escape(work[2]) + "-%02d" % (multimovnr) + "-" + escape(movtitle) + os.path.splitext(file)[1]
                    summary.append(file + " -> " + filename)
                    shutil.move(file_path, filename)
                else:
                    print(f"Source file '{file_path}' not found. Skipping.")
                
                filenr += 1
    
    return workdir, movlist, summary

def booklet(mydir, mediadir, askbox, cdnumber): # Function that handles the booklet
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
                newbookfile = bookfile.replace("processed_", "").replace(".jpeg", ".jpg") # Remove "processed_" from the filename and replace "jpg" with "jpeg"
                print(f"Renaming: {bookfile} -> {newbookfile}")
                os.rename(os.path.join(bookletdir, bookfile), os.path.join(bookletdir, newbookfile))
            elif bookfile not in special_files and bookfile.lower().endswith(".jpeg" or ".jpg"):
                file_extension = os.path.splitext(bookfile)[1] # Get the file extension
                newbookfile = "booklet{:04d}{}".format(counter, file_extension.replace("jpeg", "jpg")) # Create the new filename with the number padded with zeros
                print(f"Renaming: {bookfile} -> {newbookfile}") # User feedback
                counter += 1
                os.rename(os.path.join(bookletdir, bookfile), os.path.join(bookletdir, newbookfile))

        # Move the booklet folder and give feedback
        if ((askbox == "y" or askbox == "") and cdnumber != 1) or askbox == "n":
            shutil.move(bookletdir, newbookletdir)
            print(f"Moved booklet folder from {bookletdir} -> {newbookletdir}")
    
    elif sys.platform == "win32": # New booklet funtion for Windows user
        askbookdir = ""
        while True:
            askbookdir = input("No booklet directory found. Do you want to create one? (y(Default)/n) ").strip().lower()
            if askbookdir == "y" or askbookdir == "": 
                os.mkdir(newbookletdir)
                print("New booklet directory created ready to put files in.")
                break
            elif askbookdir == "n":
                break
            else:
                print("Invalid input. Please enter 'y' or 'n'.")

    return bookletdir

def createbox(mydir, mediadir, workdir, askbox, bookletstatus, bookletdir): # Function to create folder for box
    boxname = os.path.basename(os.path.dirname(workdir))
    boxname = re.sub(r'\._CD\d+$', '', boxname)
    if (askbox == "y" or askbox == "") and bookletstatus == 1:
        create_box = input("\nDo you want to create a box? (y(Default)/n) ").strip().lower()
        if create_box == "y" or create_box == "":
            boxname = boxname
            boxpath = os.path.join(mydir, boxname)
            try:
                os.makedirs(boxpath, exist_ok=True)
                shutil.move(mediadir, boxpath)
                shutil.move(bookletdir, boxpath)
                print(f"Folder created and media and booklet directory successfully moved to: {boxpath}")
                time.sleep(1)
            except Exception as e:
                print(f"An error occurred while creating or moving the folder: {e}")
        elif create_box == "n":
            print("Proceeding without creating a folder for the box.")
        else: 
            print("Invalid input. Please enter 'y' or 'n'.")

    return boxname

def movebox(mediadir, boxname): # Funtion to move folder to box
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        for folder in os.listdir(desktop):
            if folder.startswith("audio") and os.path.isdir(os.path.join(desktop, folder)):
                potential_folder = os.path.join(desktop, folder)
                for subfolder in os.listdir(potential_folder):
                    if subfolder == boxname and os.path.isdir(os.path.join(potential_folder, subfolder)):
                        box = os.path.join(potential_folder, subfolder)
                        while True:
                            ask_to_move = input(f"Box found at: {box}\nDo you want to move the folder? (y(Default)/n) ")
                            check_exit(ask_to_move)
                            if ask_to_move == "y" or ask_to_move == "":
                                try:
                                    shutil.move(mediadir, box)
                                    print("Folder successfully moved.")
                                    break
                                except Exception as e:
                                    print(f"Error moving media directory: {e}")
                            elif ask_to_move == "n":
                                print("Folder not moved.")
                                break
                            else:
                                print("Invalid input. Please enter 'y' or 'n'.")
    
        if not folder.startswith("audio"):
            print("\nNo box folder found. ")
        elif not subfolder == boxname:
            print("\nNo box folder found. ")

def main(mydir): # Function to process audiofiles, the booklet folder and boxes and update to excel file
    allfiles = files(mydir)
    bookletstatus, cdnumber, askbox = boxcheck(mydir)
    cdnumber = getcdnumber(askbox, bookletstatus, cdnumber)
    mediatitle = getmediatitle(askbox, cdnumber)
    numberofcomposers, composer = getnumberofcomposers()
    current_date = datetime.now()
    day = dateform(current_date)
    audiodirname = dirname(mydir)

    # Excel Sheet
    if (askbox == "y" or askbox == "") and str(cdnumber) != "1":
        print("Skipping Excel sheet update for subsequent discs.")
        ask_to_skip = "skip"
    else:
        ask_to_skip = input("Press ENTER to continue or type 'skip' to proceed without updating the Excel sheet: ").strip().lower()
        if ask_to_skip == "skip":
            print("Skipping Excel sheet uptade.")
        else:
            interpreterlist, medianumber, composerlist = excelinfo(numberofcomposers, composer)
            combined_df, excelpath, medianumber = excel(interpreterlist, composerlist, medianumber, day, audiodirname, mediatitle)

    if ask_to_skip == "skip": # Define composer for case where Excel was skipped
        composerlist = [composer[0], composer[1]]

    # 1. Confirm input
    while True:
        # review
        print("\n--------------------------------------------\nReview your inputs:")
        print(f"1. Mediatitle: {mediatitle}")
        i = 0
        if numberofcomposers == 1:
            highesti = 3
            print(f"2. Family name of composer: {composerlist[0]}")
            print(f"3. First (middle) name of composer: {composerlist[1]}")
            if (ask_to_skip != "skip" and (cdnumber == 1 or (cdnumber != 1 and askbox == "n"))):
                for i, interpreter in enumerate(interpreterlist, start=4):
                    print(f"{i}. Edit name of interpreter: {interpreter}")
                print(f"{i+1}. Edit number of media (four digits): {medianumber}")
                highesti = i + 1
        else:
            highesti = 2
            print(f"2. Number of composer: {numberofcomposers}")
            if (ask_to_skip != "skip" and (cdnumber == 1 or (cdnumber != 1 and askbox == "n"))):
                for i, interpreter in enumerate(interpreterlist, start=3):
                    print(f"{i}. Name of interpreter: {interpreter}")
                print(f"{i+1}. Number of media (four digits): {medianumber}")
                highesti = i + 1
        print("--------------------------------------------\n")
        confirm1 = input("To change an input, type its number or press ENTER to confirm: ").strip()
        check_exit(confirm1)

        if confirm1 == "":
            if not ask_to_skip == "skip":
                if numberofcomposers < 1:
                    composerlist = "Verschiedene"
                updatedmediatitle = mediatitle
                updatedmedianumber = medianumber
                updatedcomposerlist = composerlist
                updatedinterpreterlist = interpreterlist
                combined_df, excelpath, medianumber = excel(updatedinterpreterlist, updatedcomposerlist, updatedmedianumber, day, audiodirname, updatedmediatitle)
                writeexcel(combined_df, excelpath)                
            print("")
            break
        elif confirm1 == "1":
            mediatitle = handle_input("Edit mediatitle: ")
            if (askbox == "y" or askbox == ""):
                ask_cdnumber = input(f"Do you want to change the CD number? (currently at: {cdnumber}) (y/n(Default)) ")
                check_exit(ask_cdnumber)
                while True:
                    if ask_cdnumber.strip().lower() not in ("y", "n", ""):
                        print("Invalid input. Please enter 'y' or 'n'.")
                        continue
                    elif ask_cdnumber.strip().lower() == "n" or ask_cdnumber.strip().lower() == "":
                        mediatitle += f"._CD{str(cdnumber)}"
                        print(f"Box number successfully appended. New mediatitle: {mediatitle}")
                        break
                    else:
                        try:
                            newcdnumber = int(input("Number of current CD: "))
                            if cdnumber < 0:
                                print("Invalid input. Please provide a natural number.")
                            elif cdnumber == "":
                                print("Empty input. Please provide a natural number.")
                            else:
                                mediatitle += f"._CD{str(newcdnumber)}"
                                print(f"Box number successfully appended. New mediatitle: {mediatitle}")
                                break
                        except ValueError:
                            print("Invalid input. Please enter a numeric value.")
                        
        elif confirm1 == '2' and numberofcomposers == 1:
            composer[0] = handle_input("Edit family name of composer: ")
            composerlist = [composer[0], composer[1]]
        elif confirm1 == '2' and numberofcomposers > 1:
            try:
                numberofcomposers = int(input("Edit number of composers: "))
                check_exit(numberofcomposers)
                if numberofcomposers < 2:
                    print("Invalid input. Please enter a number greater than 1.")
                else:
                    break
            except ValueError:
                print("Invalid input. Please enter a numeric value.")
        elif confirm1 == '3' and numberofcomposers == 1:
            composer[1] = handle_input("Edit first (middle) name of composer: ")
            composerlist = [composer[0], composer[1]]
        elif confirm1.isdigit() and (4 <= int(confirm1) <= highesti) and ask_to_skip != "skip":
            if int(confirm1) == highesti:
                medianumber = getmedianumber()
            else:
                interpreterlist[int(confirm1) - 4] = handle_input(f" Edit name of interpreter {int(confirm1) - 3}: ")
        else:
            print("Invalid input. Please provide a number in range or press ENTER to confirm. ")

    # --- PART 2 ---

    # Process works
    works, allcomposers = getwork(allfiles, numberofcomposers, composer)
    mediadir = getmediadir(mydir, numberofcomposers, composer, allcomposers, mediatitle)
    workdir, movlist, summary = getworkdir(works, allfiles, mediadir)

    # 2. Confirm input
    # while True:
    #     print("\n----------------------------------\nReview your inputs:")
    #     w = 0
    #     m = 0
    #     confirmnum = 0
    #     if numberofcomposers == 1:
    #         print("Works:")
    #         for w, work in enumerate(works, start=1):
    #             if work[3] < work[4]:
    #                 print(f"W{w}. Work: {work[2]} (Track {work[3]} - {work[4]})")
    #             else:
    #                 print(f"W{w}. Work: {work[2]} (Track {work[3]})")
    #             highestw = w

    #         if movlist:
    #             print("Movements:")
    #             for m, mov in enumerate(movlist, start=1):
    #                 print(f"M{m}. Movement of {mov[2]}: {mov[1]} (Track {mov[0] + 1})")
    #                 highestm = m
    #     else:
    #         print("Works:")
    #         for w, work in enumerate(works, start=1):
    #             if work[3] < work[4]:
    #                 print(f"W{w}. Work: {work[2]} by {work[1]} {work[0]} (Track {work[3]} - {work[4]})")
    #             else:
    #                 print(f"W{w}. Work: {work[2]} by {work[1]} {work[0]} (Track {work[3]})")
    #             highestw = w

    #         if movlist:
    #             print("Movements:")
    #             for m, mov in enumerate(movlist, start=1):
    #                 print(f"M{m}. Movement of {mov[2]}: {mov[1]} (Track {mov[0] + 1})")
    #                 highestm = m
        
    #     if numberofcomposers > 1:
    #         confirm2 = str(input(
    #             "\nType 'w' for work, 'm' for movement and the number of the item you want to change or press ENTER to confirm:"
    #             "\nIf you want to change a composers name put a 'n' for name im front: "
    #             )).strip().lower()
    #     else:
    #         confirm2 = str(input("\nType 'w' for work, 'm' for movement and the number of the item you want to change or press ENTER to confirm: ")).strip().lower()
    #     check_exit(confirm2)
    #     confirmnum = ''.join([char for char in confirm2 if char.isdigit()])

    #     if confirm2 == "":
    #         print("Hier müssten jetzt aktuellen daten auf tie ordner und tracks geschrieben werden")
    #         break
    #     elif confirm2.startswith("w") and 0 < int(confirmnum) <= highestw: # Change works
    #         index = int(confirmnum) - 1
    #         works[index][2] = handle_input(f"Edit {works[index][2]} to: ")
    #     elif numberofcomposers > 1 and confirm2.startswith("nw") and 0 < int(confirmnum) <= highestw:
    #         index = int(confirmnum) - 1
    #         works[index][0] = handle_input(f"Edit family name of composer of {works[index][2]}: ")
    #         works[index][1] = handle_input(f"Edit fist name of composer of {works[index][2]}: ")
    #     elif confirm2.startswith("m") and 0 < int(confirmnum) <= highestm: # Change movements
    #         index = int(confirmnum) - 1
    #         movlist[index][1] = handle_input(f"Edit name of movement: ")
    #     else:
    #         print("Invalid input. Please provide a character and number (example: w1) in range or press ENTER to confirm. ")


    # Call booklet function
    bookletdir = booklet(mydir, mediadir, askbox, cdnumber)
 
    # Call create box funtion
    boxname = createbox(mydir, mediadir, workdir, askbox, bookletstatus, bookletdir)

    # Call move to box function
    if bookletstatus == 0 and (askbox == "y" or askbox == ""):
        movebox(mediadir, boxname)

    # summary
    print("\nSummary:")
    for line in summary:
        print(line)
    #print(f"Interpreters: {interpreterlist}")

    return mediadir   


# --- run

# Preperation
print("\nTo quit at any time just type '!exit'.")
print("To get the default value just press ENTER.")
print("If a composer is unknown write 'none' as first name and the family name will be changed to 'Anonymous'.")
print("To type in just one name for the composer (i.e. a band name) write 'none' as first name and 'n' to enter as family name.")
print("Write 'ebd' as first name and the name of the previous composer will automaticlly be filled in.")
print("Commas (,) and colons (:) will automatically be removed at end of an input.")
print("Shortcuts:\n\ttype '¡' (opt + 1) for Allegro\n\ttype '“' (opt + 2) for Andante\n\ttype '¶' (opt + 3) for Adagio\n")

# Directory
while True:
    # Ask for directory
    mydir = filedialog.askdirectory()
    basenamemydir = os.path.basename(mydir)
    tracks = len([file for file in os.listdir(mydir) if file.lower().endswith(".wav")])

    # Check if directory is not empty
    if mydir != '/':
        print("\nChosen directory:", mydir)
        print(f"Number of files in {basenamemydir}: {tracks}\n")
        break
    else:
        continue

# Process booklet for Mac
if sys.platform == "darwin":
    process_booklet(mydir)


# call main
mediadir = main(mydir)


# Last feedback
if sys.platform == "win32":
    print("\nEverything done!")
    input("Press ENTER to close: ")
else:
    print("\nEverything done!")


# 29-05-24