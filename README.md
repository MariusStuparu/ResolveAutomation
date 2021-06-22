#Running the Resolve Scripting tool

##1. Setup requirements

Open Terminal.app and navigate to the tool folder (wherever you unpacked it): `cd ~/ResolveScripting/`

Run the setup script: `./setup.sh`

If you didn't install them previously (probably not). It will check for Homebrew, if not present it will install it.

Then it will proceed to install some libraries required to draw the GUI and to process the output.

This will take some time, so grab a coffee. You only need to do this once on your Mac.

##2. Prepare DaVinci Resolve Studio

Make sure you have Resolve Studio (the free version does not support scripting automation), and that
you have started it (selected some project before running the script.

For simplicity, the automation does not look inside database folders, it only reads the projects listed in the currently
open database folder.

Inside the project that will be automated, organize the source clips into folders (bins) as follows:
- each bin must contain at least one video file (only the first will be used) to be multiplied and any number of audio files
- make sure the video file is not longer than any of the music files (this case will be covered in future versions, if needed) 
- any timeline or compound object in that folder will be erased by the automation
- due to some Resolve bug, make sure there are no render jobs in the Delivery page (completed, errored or pending)

##3. Start the automation

After the setup has finished, you can run the main start script: `./run.sh`

In the automation GUI, select the project that contains your sources. All bins present in the root will be listed
and are available for processing if they satisfy the requirements above.

Select the output folder where your videos will be rendered. Press Start.

While processing, multiple files will appear in the output folder - do not touch them, as the app may fail.
All temporary files will be automatically erased.

After each audio file is processed successfuly, it will be moved in the root of the Media Pool, so in case of a
catastrophic failure, you can restart processing where you were left.

Due to the nature of the automation app and how it interacts with Resolve, the Cancel button will take effect only
after the current file has been processed.

Sit back and let it run.
