#!/bin/bash
#
# This script generates an image based on a text prompt using the 'frameit' command
# and then displays the generated image using 'fbi' (FrameBuffer Imageviewer).
#
# Usage: ./regen_image.sh "Your text prompt here"
# Or, to use a previous image as inspiration:  ./regen_image.sh "Your text prompt here" --image-to-image="full path to image here"
#
# The script uses 'frameit' with the --autoprompt=sonnet option to generate an image,
# and then pipes the output (image file path) to 'fbi' for display.
#
# Note that images and prompts are stored in ~/drawings/main/ as follows:
# Images: [timestamp].png
# Prompt (useful for repeating command): [timestamp].txt
# Reprompt (mainly just used for debugging): [timestamp]_reprompt.txt
#

if [ $# -eq 0 ]; then
    echo "Please provide a text prompt as an argument."
    exit 1
fi

input_text="$1"
user=$(whoami)

# Handle optional image to image path
itoipath=""
if [[ "$2" == "--image-to-image="* ]]; then
    itoipath="${2#*=}"
    if [ ! -f "$itoipath" ]; then
        echo "The specified image file does not exist: $itoipath"
        exit 1
    fi
fi

# Construct the frameit command
frameit_cmd="/home/$user/.local/bin/frameit --autoprompt=sonnet \"$input_text\""
if [ -n "$itoipath" ]; then
    frameit_cmd+=" --image-to-image \"$itoipath\""
fi

# Execute the command and display the image
eval $frameit_cmd | xargs -I{} sudo fbi -T 1 -noverbose -a {}