
from pdf2image import convert_from_path
import os
import glob

def pdf_converter(images_folder):
    # get current directory
    current_directory = os.getcwd()
    # get project directory
    project_directory = os.path.dirname(current_directory)
    # loop through all directories in project directory
    list_directories = [directory for directory in os.listdir(project_directory) if
                        os.path.isdir(os.path.join(project_directory, directory))]
    # Get directory with images to convert
    images_dir = os.path.join(project_directory,images_folder)

    if not os.path.exists(images_dir):
        print(f"Images directory '{images_folder}' not found.")
        return

        # Loop through the PDF files in the images directory
    for filename in os.listdir(images_dir):
        # Create the full path to the current file
        file_path = os.path.join(images_dir, filename)

        # Check if the current item is a file and its name ends with "pdf" or "PDF"
        if os.path.isfile(file_path) and filename.lower().endswith(("pdf", "PDF")):
            try:
                # Convert the PDF to jpg
                images = convert_from_path(file_path)

                # Save each page as an image in the images directory
                for i, image in enumerate(images):
                    output_filename = f"{os.path.splitext(filename)[0]}_page_{i + 1}.jpg"
                    output_path = os.path.join(images_dir, output_filename)
                    image.save(output_path, "JPEG")

                    print(f"Converted page {i + 1} of '{filename}' to '{output_filename}'")
                    # Delete the PDF file with the same name
                os.remove(file_path)

            except Exception as e:
                print(f"Error converting '{filename}': {str(e)}")


# define folder name
images_folder = "images"
# convert all images in folder to .jpg
pdf_converter(images_folder)

