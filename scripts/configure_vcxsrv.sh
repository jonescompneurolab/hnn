#!/bin/bash

# Determine IPv4 address
echo "Finding IPv4 Address..."
HostIPv4Address=$(ip route show default | awk '/default/ {print $3}')

# Replace the following line with the obtained IPv4 address
export DISPLAY=$IPv4Address:0


# Check if credentials are set up
xauth list 

# Set up magiccookie
echo "Creating magiccookie with IPv4 Address ..."
passPhrase="hnn-app"
magiccookie=$(echo "hnn-cookie" | tr -d '\n\r' | md5sum | awk '{print $1}')

# Add credentials
echo "Adding magiccookie credentials to X Server..."
xauth add "$DISPLAY" . "$magiccookie"

# Display new credentials
echo "Display new credentials below..."
xauth list

# Copy .Xauthority to Windows user profile
echo "Copying credentials to Windows user profile..."
userprofile=$(wslpath $(/mnt/c/Windows/System32/cmd.exe /C "echo %USERPROFILE%" | tr -d '\r\n'))
cp "~/.Xauthority" "${userprofile}/."

echo "Done setting up X server credentials!"
