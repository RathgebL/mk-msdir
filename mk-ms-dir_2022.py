#!/usr/bin/python
#coding: utf-8

############## MEDIASERVER FILENAMER ##############
## Frank Zalkow, 2011-12
## not possible at the moment: Collections

## Updated by Lennat Rathgeb, 2022-23

# --- importing
import glob
import sys
import os
import string
import shutil

# --- sub routines
def getcomposer():
	fname =  input("Family name of composer: ")
	lname =  input("First name of composer: ")
	return (fname, lname)
	
def escape(string):
	string = string.replace(" ","_")
	### string = string.replace(".","") ####
	string = string.replace("-","--")
	string = string.replace(":","")
	string = string.replace("/","")
	string = string.replace("\\","")
	return string
	
def mkms_audiofiles(mydir):
	# audio files
	mydir = mydir[1:-1]	#cuts away first and last char of string
						#nessecary because draging in the folder adds ''
	allfiles = glob.glob(mydir+"/*.wav")
	allfiles = allfiles + glob.glob(mydir+"/*.aif")
	allfiles = allfiles + glob.glob(mydir+"/*.aiff")
	allfiles.sort(key=str.lower)
	
	if len(allfiles) == 0:
		print ("No audio files in " + mydir + " !")
		return -1
	
	# mediatitle
	mediatitle =  input("Mediatitle: ")
	
	# number of composers
	numberofcomposers = 0
	while (numberofcomposers == 0):
		yorn =  input("Is the whole media from one composer? (y/n) ")
		if (yorn == "y") or (yorn == "Y"):
			numberofcomposers = 1
			composer = getcomposer()
		elif (yorn == "n") or (yorn == "N"):
			numberofcomposers = int( input("How many composers are mentioned?  "))
		else:
			print ("Wrong input...")
		
	# work stuff
	track = 0
	endtrack = 0
	works = []
	allcomposers = [] # only needed when composers between 2 and 4
	
	while (endtrack < len(allfiles)):
		# workname + composer
		print (str(len(works)+1) + ". work of media")
		workname =  input("Name of work: ")
		if numberofcomposers > 1:
			composer = getcomposer()
			allcomposers.append(composer)
		
		multimov = 0
		while (multimov != "y") and (multimov != "Y") and (multimov != "n") and (multimov != "N"):
			multimov =  input("Does the work range over more than one audio track? (y/n) ")
		
			if (multimov == "y") or (multimov == "Y"):
				track +=1
				endtrack = int( input("It ranges from track " + str(track) + " to track... "))
			elif (multimov == "n") or (multimov == "N"):
				track += 1
				endtrack = track
			else:
				print ("Wrong input....")
				
		works.append((composer[0], composer[1], workname, track, endtrack))
		track = endtrack
		
	# media directory
	mediadir = mydir + "/"
	if numberofcomposers == 1:
		mediadir += composer[0] + "," + composer[1]
	elif numberofcomposers > 4:
		mediadir += "Verschiedene" + "-" + escape(mediatitle)
	else:
		allcomposers = list(set(allcomposers)) # remve duplicates
		composersfordir = map(lambda s: escape(s[0]) + "," + escape(s[1]), allcomposers)
		composersfordir = string.join(composersfordir, "+")
		mediadir += composersfordir
		
	mediadir += "-" + escape(mediatitle)
	os.mkdir(mediadir)
	
	# work directories
	filenr = 0
	summery = []
	for work in works:
		workdir = mediadir + "/" + escape(work[0]) + "," + escape(work[1]) + "-" + escape(work[2])
		os.mkdir(workdir)
	
		if work[3] == work[4]:
			file = allfiles[filenr]
			filename = workdir + "/" + escape(work[0]) + "-" + escape(work[2]) + os.path.splitext(file)[1]
			summery.append(file + " -> " + filename)
			shutil.move(file, filename)
			filenr += 1
			
		else:
			for multimovnr in range(1, (int(work[4]) - int(work[3]) + 2)):
				file = allfiles[filenr]
				movtitle =  input("Give name for " + str(multimovnr) + ". movement of " + work[2] + ": ")
				filename = workdir + "/" + escape(work[0]) + "-" + escape(work[2]) + "-%02d"%(multimovnr) + "-" + escape(movtitle) + os.path.splitext(file)[1]
				summery.append(file + " -> " + filename)
				shutil.move(file, filename)
				filenr += 1
	
	# summary
	for line in summery:
		print (line)
		
	return mediadir
		
def mkms_bookletfiles(mydir, mediadir):
	bookletdir = mydir + "/booklet"
	newbookletdir = mediadir + "/booklet"
	
	if os.path.exists(bookletdir):
		if not os.path.exists(newbookletdir):
			os.mkdir(newbookletdir)
		booki = 1
		bookfiles = glob.glob(bookletdir + "/*")
		bookfiles.sort(key=str.lower)
		for bookfile in bookfiles:
			base = os.path.basename(bookfile)
			base = os.path.splitext(base)[0]
			if (base != "booklet") and (base != "booklet-b"):
				newbookfile = "booklet%04d"%(booki)
				newbookfile +=  os.path.splitext(bookfile)[1].replace("jpeg", "jpg")
				if bookfile != newbookletdir + "/" + newbookfile:
					print (bookfile + " -> " +  newbookletdir + "/" + newbookfile)
					shutil.move(bookfile, newbookletdir + "/" + newbookfile)
				booki += 1
			else:
				newbookfile = newbookletdir + "/" + os.path.basename(bookfile).replace("jpeg", "jpg")
				if bookfile != newbookfile:
					print (bookfile + " -> " + newbookfile)
					shutil.move(bookfile, newbookfile)
					
		if bookletdir != newbookletdir:
			os.removedirs(bookletdir)
						
	else:
		print ("No booklet directory...")

# --- run

# Directory
mydir =  input("Directory with audio files: ")
if mydir[-1] == " ": mydir = mydir[:len(mydir)-1]

mediadir = mkms_audiofiles(mydir)
if mediadir == -1:
	mkms_bookletfiles(mydir, mydir)
else:
	mkms_bookletfiles(mydir, mediadir)

print ("Everything done!")
