# **malmo-extension** #

malmo-extension is a project that builds upon Microsoft's Malmo Platform. It contains wrappers and utility functions for more intuitive mission design. Additionally, logs are automatically generated for each mission, providing a medium for training AI. This project depends on a local copy of Microsoft's Malmo Platform, available at https://github.com/Microsoft/malmo/.

___
## **Developer Setup** ##

1. [Download the latest _prebuilt_ version of the Malmo Platform for Windows, Linux, or MacOSX.](https://github.com/Microsoft/malmo/releases) Unzip the directory to any location on your computer.

2. Create a new environment variable called MALMO_PATH equal to the full path into the directory you unzipped above.

3. Install the dependencies required to run Malmo for your operating system: [Windows](https://github.com/microsoft/malmo/blob/master/doc/install_windows.md), [Linux](https://github.com/microsoft/malmo/blob/master/doc/install_linux.md), [MacOSX](https://github.com/microsoft/malmo/blob/master/doc/install_macosx.md).

4. Clone this repository to any location on your computer:
    ```
    git clone https://github.com/NateRex/malmo-extension.git
    ```

5. Run the setup script (.sh if you are on Linux or MacOSX, and .bat if you are on Windows):
    ```
    cd malmo-extension
    ./setup.sh
    ```