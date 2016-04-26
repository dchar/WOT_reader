# Author: Dylan Ruggeroli
# Date	: 4/23/2016
# 
# Python prototype for finding a reader's position in a book using their 
# audiobook progress. Scans audiobook .mp3 files in the directory, using
# metadata to find total duration. Then requests an XML string containing
# information about the file currently playing in VLC Media Player. The user's
# completion percentage for the audiobook is then used to approximate their
# location within a viewable version.
#	
# Input (argv1): Total number of pages in the viewable copy 
# Output: Approximate page number within the viewable copy

import sys, eyed3, os, requests
import xml.etree.ElementTree as ET

# GLOBAL CONSTANTS
PAGES_IN_BOOK    = sys.argv[1]
AUDIO_INTRO_BIAS = (3 * 60) + 31
AUDIO_OUTRO_BIAS = 0 				# undetermined
MP3_SECONDS_BIAS = 13

# Set global variables
duration_lst   = [0]
total_duration =  0
file_number    =  0

# For each file in the directory, add to total duration
def scan_directory():
	global total_duration

	for file in os.listdir("."):
		if file.endswith(".mp3"):
			audiofile      = eyed3.load(file)
			file_duration  = audiofile.info.time_secs - MP3_SECONDS_BIAS
			total_duration += file_duration

			duration_lst.append(file_duration)

# Request XML data for the file currently playing in VLC media player
# Note: Requires Lua http interface within VLC
# FIXME: currenntly ahead
def request_position():
	global file_number, secs_into_audiobook
	s = requests.Session()
	s.auth = ('', 'testing')
	r = s.get('http://localhost:8080/requests/status.xml', verify = False)
	tree = ET.fromstring(r.content) 

	temp_file_ratio    = -1.0
	temp_file_number   = -1
	
	for elem in tree:
		# Find the ratio representing position in the XML string
		if (elem.tag == "position"):
			temp_file_ratio = float(elem.text)

		# Find the track number for the currently playing file
		elif (elem.tag == "information"):
			if (elem[0].get('name') == "meta"):
				for child in elem[0]:
					if (child.get('name') == 'track_number'):
						temp_file_number = int(child.text)

	# Find the duration of the currently playing file in duration_lst
	temp_file_duration = duration_lst[temp_file_number]
	secs_into_current  = temp_file_duration * temp_file_ratio

	# Update global audiobook position
	if (temp_file_ratio == -1.0 or temp_file_number == -1):
		# VLC is not streaming so exit the program
		print("\nERROR: No file currently playing within VLC")
		print("Exiting program..")
		exit()
	else:
		# Set the current file number and update seconds into audiobook
		file_number = temp_file_number
		length_of_prior_files = 0

		for i in range(file_number):			
			length_of_prior_files += duration_lst[i]

		secs_into_audiobook = length_of_prior_files + secs_into_current

# Using audiobook completion percentage, find and return an approximate page 
# number
def find_approximate_page(seconds_in):
	audio_ratio = seconds_in / (total_duration - AUDIO_INTRO_BIAS)
	approx_page = audio_ratio * float(PAGES_IN_BOOK)
	return approx_page


# Informal report method for testing purposes
def test_report(approx_page):

	# Print command-line arugments
	print("\nTotal pages:	 ", PAGES_IN_BOOK)
	print("File number:	 ",     file_number)
	print("Location in secs:",  secs_into_audiobook)

	# Print gathered variables
	print("\nApproximate page #: ", page_num)
	print("Audibook Duration : " +
		str(total_duration) + " seconds, " +
		str(total_duration / 60) + " minutes")


# --- INITIALIZATION
print("\nLoading audiobook files..")
scan_directory()

# --- FIXME: WHILE !DONE wait for keystroke to invoke request ---
# Request information, calculate approximate page number, then report
print("\nRequesting information..")
request_position()
page_num = find_approximate_page(secs_into_audiobook)
test_report(page_num)

