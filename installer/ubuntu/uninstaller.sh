# cleanup the icon and unregister the program with the system
sudo rm -f /usr/share/pixmaps/hnn.png
sudo rm -f /usr/share/applications/hnn.desktop

# clean up the program's shortcut
sudo rm -f /usr/local/bin/hnn
sudo updatedb

# delete the installed hnn folder
sudo rm -rf /usr/local/hnn

# delete hnn's dependencies
sudo rm -rf /usr/local/nrn

# clean up the bashrc (sed looks like it uses regex, but I don't
# think that it does. You do have to escape the '/' character, though)
sed -i '/# these lines define global session variables for HNN/d' ~/.bashrc
sed -i '/export CPU=$(uname -m)/d' ~/.bashrc
sed -i '/export PATH=$PATH:\/usr\/local\/nrn\/$CPU\/bin/d' ~/.bashrc
