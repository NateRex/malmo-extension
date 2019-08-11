import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

with open("malmoext/requirements.txt", "r") as f:
    requirements = f.read().splitlines()

setuptools.setup(
     name='malmoext',  
     version='37.0.2',
     author="Nathaniel Rex",
     author_email="nathanieljrex@gmail.com",
     description="An extension to Microsoft's Malmo Project",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/naterex/malmo-extension",
     packages=setuptools.find_packages(),
     package_data={
         "malmoext": ["MalmoPython.so", "MalmoPython.pyd", "MalmoPython.lib"]
     },
     install_requires=requirements,
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ]
 )