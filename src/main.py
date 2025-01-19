#!/usr/local/bin/python3
"""
Use os package to iterate through files in a directory
"""
import os
import sys
import json
import base64
import datetime as dt

# Load icon mappings from JSON
with open('/src/icons.json', encoding="utf-8") as json_file:
    data = json.load(json_file)


def main():
    """
    Main function
    """
    total_files = 0  # Initialize file count

    if len(sys.argv) > 1:
        print("Changing directory to " + sys.argv[1])
        try:
            os.chdir(sys.argv[1])
        except OSError:
            print("Cannot change the current working directory")
            sys.exit()
    else:
        print("No directory specified")
        sys.exit()

    # Iterate through all subdirectories and files
    for dirname, dirnames, filenames in os.walk('.'):
        # Exclude index.html from the file count
        filenames = [filename for filename in filenames if filename != 'index.html']

        # Update total file count (excluding index.html)
        total_files += len(filenames)

        if 'index.html' in filenames:
            print(f"{dirname}/index.html already exists, skipping...")
        else:
            print(f"{dirname}/index.html does not exist, generating")
            with open(os.path.join(dirname, 'index.html'), 'w', encoding="utf-8") as f:
                f.write("\n".join([get_template_head(dirname)]))

                if dirname != ".":
                    f.write("<tr class=\"w-2/4 bg-gray-800 dark:bg-gray-900 border-b border-gray-600 hover:bg-gray-700 dark:hover:bg-gray-800\"><th scope=\"row\" class=\"py-2 px-2 lg:px-6 font-medium text-gray-300 dark:text-gray-400 whitespace-nowrap flex align-middle\"><img style=\"max-width:23px; margin-right:5px\" src=\"" + get_icon_base64("o.folder-home") + "\"/>" +
                            "<a class=\"my-auto text-blue-400 dark:text-blue-500\" href=\"../\">../</a></th><td>-</td><td>-</td></tr>")

                # Sort dirnames alphabetically
                dirnames.sort()
                for subdirname in dirnames:
                    f.write("<tr class=\"w-1/4 bg-gray-800 dark:bg-gray-900 border-b border-gray-600 hover:bg-gray-700 dark:hover:bg-gray-800\"><th scope=\"row\" class=\"py-2 px-2 lg:px-6 font-medium text-gray-300 dark:text-gray-400 whitespace-nowrap flex align-middle\"><img style=\"max-width:23px; margin-right:5px\" src=\"" + get_icon_base64("o.folder") + "\"/>" +
                            "<a class=\"my-auto text-blue-400 dark:text-blue-500\" href=\"" + subdirname + "/\">" +
                            subdirname + "/</a></th><td>-</td><td>-</td></tr>\n")

                # Sort filenames alphabetically
                filenames.sort()
                for filename in filenames:
                    path = (dirname == '.' and filename or dirname + '/' + filename)
                    f.write("<tr class=\"w-1/4 bg-gray-800 dark:bg-gray-900 border-b border-gray-600 hover:bg-gray-700 dark:hover:bg-gray-800\"><th scope=\"row\" class=\"py-2 px-2 lg:px-6 font-medium text-gray-300 dark:text-gray-400 whitespace-nowrap flex align-middle\"><img style=\"max-width:23px; margin-right:5px\" src=\"" + get_icon_base64(filename) + "\"/>" + "<a class=\"my-auto text-blue-400 dark:text-blue-500\" href=\"" + filename + "\">" + filename + "</a></th><td>" +
                            get_file_size(path) + "</td><td>" + get_file_modified_time(path) + "</td></tr>\n")

                f.write("\n".join([get_template_foot(total_files)]))

    # Log the total number of files (excluding index.html)
    print(f"Total files (excluding index.html): {total_files}")


def get_file_size(filepath):
    """
    Get file size
    """
    size = os.path.getsize(filepath)
    if size < 1024:
        return str(size) + " B"
    elif size < 1024 * 1024:
        return str(round((size / 1024), 2)) + " KB"
    elif size < 1024 * 1024 * 1024:
        return str(round((size / 1024 / 1024), 2)) + " MB"
    else:
        return str(round((size / 1024 / 1024 / 1024), 2)) + " GB"
    return str(size)


def get_file_modified_time(filepath):
    """
    Get file modified time
    """
    return dt.datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S UTC')


def get_template_head(foldername):
    """
    Get template head
    """
    if foldername.startswith('.'):
        if not foldername.startswith('/', 1):
            return get_template_head('/' + foldername[1:])
        else:
            return get_template_head(foldername[1:])

    with open("/src/template/head.html", "r", encoding="utf-8") as file:
        head = file.read()
    head = head.replace("{{foldername}}", foldername)
    return head


def get_template_foot(total_files):
    """
    Get template foot
    """
    with open("/src/template/foot.html", "r", encoding="utf-8") as file:
        foot = file.read()

    # Ensure that the total_files placeholder is replaced with the actual value
    foot = foot.replace("{{buildtime}}", "at " + dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'))
    foot = foot.replace("{{totalfiles}}", str(total_files))  # Replaces {{totalfiles}} with the total file count
    
    # Debug print
    print(f"Foot content after replacement:\n{foot}\n")

    return foot



def get_icon_base64(filename):
    """
    Get icon base64
    """
    with open("/src/png/" + get_icon_from_filename(filename), "rb") as file:
        return "data:image/png;base64, " + base64.b64encode(file.read()).decode('ascii')


def get_icon_from_filename(filename):
    """
    Get icon from filename
    """
    extension = "." + filename.split(".")[-1]
    for i in data:
        if extension in i["extension"]:
            return i["icon"] + ".png"
    return "unknown.png"


if __name__ == "__main__":
    main()
