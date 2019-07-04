# **malmo-extension** #

malmo-extension is a project that builds upon [Microsoft's Malmo Platform](https://github.com/Microsoft/malmo/). It contains wrappers and utility functions for more intuitive mission design. Additionally, logs are automatically generated for each mission, providing a medium for training AI. The project currently only supports Python.

___
## **Installation** ##

These instructions are for people who would like to install and use the malmo-extension as is.

1. [Download the latest _prebuilt_ version of the Malmo Platform for Windows, Linux, or MacOSX](https://github.com/Microsoft/malmo/releases). Unzip the directory.

2. [Download the latest _prebuilt_ version of malmo-extension for Windows, Linux, or MacOSX]() Unzip the directory to access the library file.

    You can now begin using the library. Navigate to the root of the Malmo directory (1), and launch a Malmo Minecraft client (.sh on MacOSX and Linux, .bat on Windows):

    ```
    ./Minecraft/launchClient.sh
    ```

    Note that you will need multiple clients running for missions involving multiple agents. Now copy the malmo-extension library file (2) to the directory you will create missions in. See the [example_missions]() directory for examples. When you're ready, run your mission:

    ```
    python3 myMission.py
    ```

___
## **Developer Setup** ##

These instructions are for people who would like to clone this repository to make changes and add functionality for future releases of malmo-extension.

1. [Download the latest _prebuilt_ version of the Malmo Platform for Windows, Linux, or MacOSX](https://github.com/Microsoft/malmo/releases). Unzip the directory.

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