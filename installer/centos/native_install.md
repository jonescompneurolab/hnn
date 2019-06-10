# HNN native install (CentOS)

The scripts below can be used to install HNN and its prerequisites. However, there is a greater possibility that your base environment will not be compatible with the script and installation might require additional troubleshooting. Thus, we do not recommend this method. For the recommmeded Docker-based installation, please see the instructions below.
  - Alternative: [Docker install instructions](README.md)

See the scripts in this directory:
* CentOS 6: [centos6-installer.sh](centos6-installer.sh)
* CentOS 7: [centos7-installer.sh](centos7-installer.sh)
  ```
  chmod +x ./centos7-installer.sh
  ./centos7-installer.sh
  ```
* [uninstall.sh](uninstall.sh)
  ```
  chmod +x ./uninstall.sh
  ./uninstall.sh
  ```

# Troubleshooting

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will be able to suggest possible fixes.

For other HNN software issues, please visit the [HNN bulletin board](https://www.neuron.yale.edu/phpBB/viewforum.php?f=46)