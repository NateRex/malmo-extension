import setuptools

with open("../README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
     name='malmoext',  
     version='0.1',
     author="Nathaniel Rex",
     author_email="nathanieljrex@gmail.com",
     description="An extension to Microsoft's Malmo Project",
     long_description=long_description,
   long_description_content_type="text/markdown",
     url="https://github.com/naterex/malmo-extension",
     packages=setuptools.find_packages(),
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
 )