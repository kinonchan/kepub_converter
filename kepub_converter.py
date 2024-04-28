import sys
import os
import ebooklib.epub
import subprocess
import configparser
from opencc import OpenCC
import logging

def is_simplified_chinese_epub(file_path):

    logging.debug("Inside is_simplified_chinese_epub function")

    book = ebooklib.epub.read_epub(file_path)
    metadata = book.get_metadata('DC', 'language')
    if metadata:
        languages = [lang[0] for lang in metadata]
        return 'zh-cn' in languages or 'chi' in languages or 'zh' in languages
    return False

def is_valid_epub(file_path):

    logging.debug("Inside is_valid_epub function")
    try:
        # Attempt to read the EPUB file
        book = ebooklib.epub.read_epub(file_path)
        # If no exceptions are raised, it's likely a valid EPUB file
        logging.debug("It is likely a valid ePUB file.")

        return True
    except (ebooklib.epub.EpubException, ValueError) as e:
        # If an exception is raised, it's likely not a valid EPUB file
        logging.error(f"Error reading EPUB file: {e}")
        return False
    except Exception as e:
        # Catch any other exceptions that may occur
        logging.error(f"An unexpected error occurred: {e}")
        return False


def convert_to_traditional_chinese(epub_file_path, output_file_path):

    logging.debug("Inside convert_to_traditional_chinese function")

    # Load the ePub book
    book = ebooklib.epub.read_epub(epub_file_path)

    # Create a converter from Simplified Chinese to Traditional Chinese
    # converter = OpenCC('s2t.json')
    converter = OpenCC('s2t')

    # Iterate through the book's HTML files and convert the contents
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        content = item.content.decode('utf-8')
        converted_content = converter.convert(content)
        item.content = converted_content.encode('utf-8')

    # Save the converted book to a new ePub file
    ebooklib.epub.write_epub(output_file_path, book)

    logging.info(f"SC->TC conversion completed. New ePub file saved as: {output_file_path}")

    return output_file_path

# Check if the kepubify command is available and execute if so
def convert_to_kepub(kepub_command, filename):

    logging.debug("Inside convert_to_kepub function")

    try:
        subprocess.run([kepub_command, '--version'], check=True)
        logging.debug(f"{kepub_command} command is available.")
        subprocess.run([kepub_command, '-o', output_path, '-v', filename], check=True)
        logging.info(f"{kepub_command} executed successfully.")
        logging.info(f"Output file: {output_path}/{filename}")
        return True
    except FileNotFoundError:
        logging.error(f"ERROR: {kepub_command} command is not available.")
        return False

# Clean up worked files
def remove_file(file_path):
    try:
        os.remove(file_path)
        logging.info(f"File '{file_path}' removed successfully.")
    except FileNotFoundError:
        logging.error(f"File '{file_path}' not found.")
    except OSError as e:
        logging.error(f"Error occurred while removing file: {e}")

# Program start below
# -------------------------------------------
# This program takes pub filepath as input and perform the following:
#  1. Check if it is an epub file.  Exit the program if not.
#  2. Check if it is a simplified chinese epub file.  If yes, convert to tranditional chinese using OpenCC lib
#  3. Check if kepubify is available.  Convert the epub file to kepub (Kobo ePub) file format.
#  4. Write the converted file to output_path.
#  5. Execute MacOS command to open the output_path in Finder.
#


# config.ini
# [section]
# parameter1 = value1
# parameter2 = value2

config = configparser.ConfigParser()

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the INI file
ini_file_path = os.path.join(script_dir, 'kepub_converter.ini')

# Try to get the config parameter from external ini file
try:
    config.read(ini_file_path)

    # kepub_command - the path of the kepubify
    kepub_command = config['PATH']['kepubCmd']
    output_path = config['PATH']['outputFolder']

    # Get the logging level from the INI file
    log_level_str = config.get('LOGGING', 'Level', fallback='INFO').upper()

    # Define a dictionary to map the logging level from string to the actual logging level
    log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    # Get the corresponding logging level object
    log_level = log_levels.get(log_level_str, logging.INFO)

    # Configure logging with the level from the INI file
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

except KeyError as e:
    logging.error(f"The key {e} was not found in the ini config file.")
    sys.exit(1)
except configparser.Error as e:
    logging.error(f"An error occurred while parsing ini config file: {e}")
    sys.exit(2)
except Exception as e:
    logging.error(f"An error occurred: {e}")
    sys.exit(3)

# Log variable values
logging.debug("script_dir=" + script_dir)
logging.debug("ini_file_path=" + ini_file_path)
logging.debug("kepub_command=" + kepub_command)
logging.debug("output_path=" + output_path)

# Check if a file is provided as an argument
if len(sys.argv) > 1:
    file_path = sys.argv[1]

    # Define a temp file for conversion
    temp_file_path = file_path.replace('.epub', '_tc.epub')

    logging.debug("Input filepath=" + file_path)
    logging.debug("Temp filepath for TC work file=" + temp_file_path)

    # Check if the input file is an ePub file
    if not is_valid_epub(file_path):
        logging.info(f"{file_path} is not an ePub file.  Exiting..")
        sys.exit(4)

    isTempFile=False
    # Check if the input file is encoded in simplified chinese
    if is_simplified_chinese_epub(file_path):
        logging.debug("the input file is encoded in simplified chinese")
        file_path=convert_to_traditional_chinese(file_path, temp_file_path)
        isTempFile=True

    # Convert to kepub format
    convert_to_kepub(kepub_command, file_path)

    # Clean-up worked file
    if isTempFile:
        remove_file(temp_file_path)

    # open output folder
    subprocess.run(["open", output_path], check=True)

else:
    logging.error("Please provide a file path as an argument.")