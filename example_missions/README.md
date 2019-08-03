# **malmo-extension Mission Guide** #

This README will provide you details on how to start building and running Malmo Minecraft missions using the malmo-extension. If you haven't done so already, make sure to install the necessary software by following [these instructions](https://github.com/NateRex/malmo-extension#malmo-extension).

____

## **Creating Missions** ##

This repository contains several example scripts to get you started creating missions in Malmo using the wrapper. These are located in the same directory as this README. All of the mission scripts follow a simple pattern:

1. Create the mission environment
2. Start the Malmo mission (specifying additional logging if necessary)
3. Define each agent's actions (occurs in a loop)
4. Cleanup

For more information, be sure to read the class method documentations.

____

## **Running Missions** ##

1. To run a mission, first make sure you have as many Malmo Minecraft client instances running as you do agents in your mission. A client can be started by navigating to the root of Microsoft's Malmo project you installed, and running the following command:

    Windows:
    ```
    ./Minecraft/launchClient.bat
    ```

    Mac & Linux:
    ```
    ./Minecraft/launchClient.sh
    ```

2. With those up and running, you can now run your mission just as you would any other Python script (Python version 3.6 or higher is required):

    ```
    python3 <myMission>.py
    ```

3. Once a mission finishes, several files will become available:
    - A single log describing everything that occurred during the mission will be output to a "logs" directory.
    - A CSV file for **each agent** will be output to a "performance" directory. Each CSV file contains agent statistics over time.