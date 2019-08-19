# clean up the bashrc (sed looks like it uses regex, but I don't
# think that it does. You do have to escape the '/' character, though)
sed -i '/# these lines define global session variables for HNN/d' ~/.bashrc
sed -i '/export CPU=$(uname -m)/d' ~/.bashrc
sed -i "/export PATH=\$PATH:$startdir\/nrn\/build\/\$CPU\/bin/d" ~/.bashrc
