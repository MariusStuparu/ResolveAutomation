#!/usr/bin/env sh

which -s brew
if [[ $? != 0 ]] ; then
  echo "Hombrew not present. Installing..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
else
  echo "Hombrew present. Updating references..."
  brew update
fi

echo "Installing tkinter..."
brew install python-tk@3.9
echo "tkinter installed"

echo "Installing ffmpeg..."
brew install ffmpeg
echo "ffmpeg installed"

echo "Initial setup done. You can run the app now."
