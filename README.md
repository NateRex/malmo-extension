# **malmo-extension** #

malmo-extension is a project that builds upon [Microsoft's Malmo Platform](https://github.com/Microsoft/malmo/). It contains wrappers and utilities for more intuitive mission design. Additionally, logs are automatically generated for each mission, providing a medium for training AI. The project currently only supports Python (version 3.6 or above).

![malmoext](https://user-images.githubusercontent.com/34667018/62836148-3b3ece00-bc2e-11e9-95e8-ab7f954061d3.gif)
___
## **Installation** ##

1. Before you are able to use this package, you must have Microsoft's Malmo Platform downloaded on your machine. [Download the prebuilt Malmo Platform for Windows, Linux, or MacOSX](https://github.com/Microsoft/malmo/releases), and unzip the directory.

2. Create a new global environment variable called MALMO_XSD_PATH. Let it equal the full path to the Schemas/ directory inside of the project you unzipped for step 1.

3. Install the malmo-extension package using pip:
    ```
    pip3 install malmoext==<VERSION>.*
    ```

    **Note** - The major version you choose should match the minor version of your Malmo Platform download. For example, if you downloaded version 0.37.\* of the Malmo Platform, you should download version 37.\* of the malmo-extension package.

That's it! You are now ready to begin using this Malmo wrapper. Check out the [Mission Guide](https://github.com/NateRex/malmo-extension/tree/master/example_missions#malmo-extension-mission-guide) for details on how to get started building and running Minecraft missions.
