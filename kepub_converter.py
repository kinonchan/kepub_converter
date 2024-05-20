import sys
import os
import ebooklib.epub
import subprocess
import configparser
from kepub_converter_logger import Kepub_converter_logger
from opencc import OpenCC

class kepub_converter:

    def __init__(self, input_file_path, config_file):
        # Store the input file path and configuration file path
        self.input_file_path = input_file_path
        self.working_file = None
        self.config_file = config_file
        self.config = configparser.ConfigParser()

        # Try to get the config parameter from external ini file
        try:
            self.config.read(config_file)
            self.logger = Kepub_converter_logger(self.config)

            # kepub_command - the path of the kepubify
            self.kepub_command = self.config['PATH']['kepubCmd']
            self.output_path = self.config['PATH']['outputFolder']

        except KeyError as e:
            # Handle the case when a key is not found in the config file
            self.logger.error(f"The key {e} was not found in the ini config file.")
            sys.exit(1)
        except configparser.Error as e:
            # Handle errors while parsing the config file
            self.logger.error(f"An error occurred while parsing ini config file: {e}")
            sys.exit(2)
        except Exception as e:
            # Handle any other exceptions
            self.logger.error(f"An error occurred: {e}")
            sys.exit(3)


        # Define a temp file for TC conversion
        self.tc_output_file_path = self.input_file_path.replace('.epub', '_tc.epub')

        self.is_epub = False
        self.is_simplified_chinese = False
        self.book = None
        self.metadata = None
        try:
            # Attempt to read the EPUB file
            self.book = ebooklib.epub.read_epub(self.input_file_path)
            # If no exceptions are raised, it's likely a valid EPUB file
            self.logger.debug("It is likely a valid ePUB file.")
            self.is_epub = True
        except (ebooklib.epub.EpubException, ValueError) as e:
            # If an exception is raised, it's likely not a valid EPUB file
            self.logger.error(f"Error reading EPUB file: {e}")
        except Exception as e:
            # Catch any other exceptions that may occur
            self.logger.error(f"An unexpected error occurred: {e}")
        
        if self.is_epub:
            metadata = self.book.get_metadata('DC', 'language')
            self.working_file = self.input_file_path
            if metadata:
                languages = [lang[0] for lang in metadata]
                self.is_simplified_chinese = 'zh-cn' in languages or 'chi' in languages or 'zh' in languages

    def get_output_path(self):
        # Return the output path for the converted Kepub file
        return self.output_path

    def is_valid_epub(self):
        self.logger.debug("Inside is_valid_epub function")
        return self.is_epub

    # Function to check if the epub is a simplified chinese book by checking the lang feild in metadata area
    # If match "zh-cn" or "chi" or "zh", return True.  Otherwise, return False
    def is_simplified_chinese_epub(self):
        self.logger.debug("Inside is_simplified_chinese_epub function")
        return self.is_simplified_chinese


    """
    This method converts a Simplified Chinese EPUB file to Traditional Chinese using the OpenCC library.

    Steps:
    1. Load the EPUB book using ebooklib.epub.read_epub().
    2. Check if the input file is a valid EPUB and is encoded in Simplified Chinese.
    3. Create a converter from Simplified Chinese to Traditional Chinese using OpenCC('s2t').
    4. Iterate through the book's HTML files and convert the content from Simplified Chinese to Traditional Chinese.
    5. Save the converted book to a new EPUB file with a '_tc' suffix.
    6. Update the working file path to the converted Traditional Chinese file.
    7. Return True if the conversion is successful, False otherwise.
    """
    def convert_to_traditional_chinese(self):

        self.logger.debug("Inside convert_to_traditional_chinese function")

        # Load the ePub book
        book = ebooklib.epub.read_epub(self.input_file_path)

        if self.is_epub and self.is_simplified_chinese:

            # Create a converter from Simplified Chinese to Traditional Chinese
            converter = OpenCC('s2t')

            # Iterate through the book's HTML files and convert the contents
            for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                content = item.content.decode('utf-8')
                converted_content = converter.convert(content)
                item.content = converted_content.encode('utf-8')

            # Save the converted book to a new ePub file
            ebooklib.epub.write_epub(self.tc_output_file_path, book)

            self.logger.info(f"SC->TC conversion completed. New ePub file saved as: {self.tc_output_file_path}")
            self.working_file = self.tc_output_file_path

            return True
        else:
            return False

    # Check if the kepubify command is available and execute if so
    def convert_to_kepub(self):

        self.logger.debug("Inside convert_to_kepub function")

        try:
            subprocess.run([self.kepub_command, '--version'], check=True)
            self.logger.debug(f"{self.kepub_command} command is available.")
            subprocess.run([self.kepub_command, '-o', self.output_path, '-v', self.working_file], check=True)
            self.logger.info(f"{self.kepub_command} executed successfully.")
            self.logger.info(f"Output: {self.output_path}/{self.working_file}")
            return True
        except FileNotFoundError:
            self.logger.error(f"ERROR: {self.kepub_command} command is not available.")
            return False

    # Clean up worked files
    def cleanup(self):
        if self.is_simplified_chinese:
            try:
                os.remove(self.working_file)
                self.logger.info(f"File '{self.working_file}' removed successfully.")
            except FileNotFoundError:
                self.logger.error(f"File '{self.working_file}' not found.")
            except OSError as e:
                self.logger.error(f"Error occurred while removing file: {e}")

# Program start below
# -------------------------------------------
# This program takes pub filepath as input and perform the following:
#  1. Check if it is an epub file.  Exit the program if not.
#  2. Check if it is a simplified chinese epub file.  If yes, convert to tranditional chinese using OpenCC lib
#  3. Check if kepubify is available.  Convert the epub file to kepub (Kobo ePub) file format.
#  4. Write the converted file to output_path.
#  5. Execute MacOS command to open the output_path in Finder.
#

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the INI file
ini_file_path = os.path.join(script_dir, 'kepub_converter.ini')

# Check if a file is provided as an argument
if len(sys.argv) > 1:
    file_path = sys.argv[1]

    # declare a Kobo EPub converter instance
    k_converter = kepub_converter(file_path, ini_file_path)

    # Check if the input file is an ePub file
    k_converter.convert_to_traditional_chinese()
    k_converter.convert_to_kepub()
    k_converter.cleanup()

    # open output folder
    subprocess.run(["open", k_converter.get_output_path()], check=True)

else:
    print("Please provide a file path as an argument.")