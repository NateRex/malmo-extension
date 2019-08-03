# **malmo-extension** #

malmo-extension is a project that builds upon [Microsoft's Malmo Platform](https://github.com/Microsoft/malmo/). It contains wrappers and utilities for more intuitive mission design. Additionally, logs are automatically generated for each mission, providing a medium for training AI. The project currently only supports Python.

___
## **Installation** ##

1. Before you are able to use this package, you must have Microsoft's Malmo Platform installed on your machine. [Download the prebuilt Malmo Platform for Windows, Linux, or MacOSX](https://github.com/Microsoft/malmo/releases), and unzip the directory.

2. Create a new global environment variable called MALMO_XSD_PATH. Let it equal the full path to the Schemas/ directory inside of the project you unzipped for step 1.

3. Install the malmo-extension package using pip:
    ```
    pip3 install malmoext
    ```

    **Note** - The minor version number of this package should match the minor version number of the Malmo Platform. For example, if you downloaded version 0.37.0 of the Malmo Platform, you should download the latest 0.37.x version of the malmo-extension package.

That's it! You are now ready to begin using this Malmo wrapper. Check out the [Mission Guide](https://github.com/NateRex/malmo-extension/tree/master/example_missions#malmo-extension-mission-guide) for details on how to get started building and running Minecraft missions.
