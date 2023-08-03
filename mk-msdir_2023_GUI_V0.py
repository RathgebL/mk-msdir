#!/usr/bin/python
#coding: utf-8

############## MEDIASERVER FILENAMER ##############
## Frank Zalkow, 2011-12
## not possible: Collections
## Updated by Lennat Rathgeb, 2022-23
## now: Python3, compatible with Windows
## new features:    renaming of scans if in booklet folder
##                  error handling
##                  opens finder window for user input


# --- importing
import sys
import os
import shutil
from tkinter import filedialog

# --- sub routines
def getcomposer():
    while True:
        fname = input("Family name of composer: ")
        lname = input("First name of composer: ")
        
        if fname.strip() == "" or lname.strip() == "":
            print("Invalid input. Please provide both a family name and a first name.")
        else:
            return (fname, lname)

def escape(string):
    string = string.replace(" ", "_")
    string = string.replace("-", "--")
    string = string.replace(":", "")
    string = string.replace("/", "")
    string = string.replace("\\", "")
    return string

def mkms_audiofiles(mydir):
    # audio files
    audio_extensions = (".wav", ".aif", ".aiff")
    allfiles = [file for file in os.listdir(mydir) if file.lower().endswith(audio_extensions)]
    allfiles.sort(key=str.lower)

    if not allfiles:
        print("No audio files in " + mydir + "!")
        sys.exit(1)

    # mediatitle
    while True:
        mediatitle = input("Mediatitle: ")
        
        if mediatitle.strip() == "":
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
                    break
                except ValueError:
                    print("Invalid input. Please enter a numeric value.")
             
        else:
            print("Wrong input...")

    # work stuff
    track = 0
    endtrack = 0
    works = []
    allcomposers = []    # only needed when composers between 2 and 4

    while endtrack < len(allfiles):
        # workname + composer
        print(str(len(works) + 1) + ". work of media")
        while True:
            workname = input("Name of work: ")
        
            if workname.strip() == "":
                print("Invalid input. Please provide a name of work.")
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
        mediadir += "Verschiedene" + "-" + escape(mediatitle)
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
        os.mkdir(workdir)

        if work[3] == work[4]:
            file = allfiles[filenr]
            filename = os.path.join(workdir, escape(work[0])) + "-" + escape(work[2]) + os.path.splitext(file)[1]
            summary.append(file + " -> " + filename)
            shutil.move(os.path.join(mydir, file), filename)
            filenr += 1
        else:
            for multimovnr in range(1, (int(work[4]) - int(work[3]) + 2)):
                file = allfiles[filenr]
                while True:
                    movtitle = input("Give name for " + str(multimovnr) + ". movement of " + work[2] + ": ")

                    if movtitle.strip() == "":
                        print("Invalid input. Please provide a name for the movement.")
                    else:
                        break

                filename = os.path.join(workdir, escape(work[0])) + "-" + escape(work[2]) + "-%02d" % (multimovnr) + "-" + escape(movtitle) + os.path.splitext(file)[1]
                summary.append(file + " -> " + filename)
                shutil.move(os.path.join(mydir, file), filename)
                filenr += 1

    # summary
    for line in summary:
        print(line)
        
    return mediadir

def extract_number(filename):
    # Extracts the numeric portion from the filename
    name = os.path.splitext(filename)[0]  # Remove the file extension
    numeric_part = ''.join(filter(str.isdigit, name))
    if numeric_part:
        return int(numeric_part)
    else:
        return 0

# Defining the source and destination directories
def mkms_bookletfiles(mydir, mediadir):
    bookletdir = os.path.join(mydir, "booklet")
    newbookletdir = os.path.join(mediadir, "booklet")

    if os.path.exists(bookletdir):
        counter = 1
        #Sort the files
        bookfiles = os.listdir(bookletdir)
        bookfiles = sorted(bookfiles, key=extract_number)

        # Exclude the files which are already named correctly or give an error if renamed
        excluded_files = ["booklet-b.jpg", "booklet.jpg", ".DS_Store"]

        for bookfile in bookfiles:
            if bookfile not in excluded_files and bookfile.lower().endswith(".jpg"):
            
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
        print(f"Moved booklet folder from {bookletdir} to {newbookletdir}")

    else:
        askbookdir = ""
        while askbookdir.lower() not in ["y", "n"]:
            askbookdir = input("No booklet directory found. Do you want to create one? (y/n) ") 
        if askbookdir.lower() == "y": 
            os.mkdir(newbookletdir)
            print("New booklet directory created ready to put files in.")

# --- run

# Directory
mydir = filedialog.askdirectory()

allfiles = []
for file in os.listdir(mydir):
    if file.lower().endswith((".wav", ".aif", ".aiff")):
        allfiles.append(file)
allfiles.sort(key=str.lower)

if len(allfiles) == 0:
    print("No audio files in " + mydir + " !")
    sys.exit(1)

mediadir = mkms_audiofiles(mydir)
mkms_bookletfiles(mydir, mediadir)

input("Everything done!\nPress ENTER to close: ")