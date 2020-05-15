# HNN native install (CentOS)

The script below assumes that it can update OS packages for python and prerequisites for NEURON and HNN. To install HNN in an isolated environment, we recommend using the [Docker-based installation method](README.md).

- CentOS 7: [centos7-installer.sh](centos7-installer.sh)

  ```bash
  chmod +x ./hnn-centos7.sh
  ./hnn-centos7.sh
  ```

- CentOS 6 (no longer maintained): [centos6-installer.sh](centos6-installer.sh)

  ```bash
  chmod +x ./hnn-centos6.sh
  ./hnn-centos6.sh
  ```

## Troubleshooting

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will be able to suggest possible fixes.

For other HNN software issues, please visit the [HNN bulletin board](https://www.neuron.yale.edu/phpBB/viewforum.php?f=46)
