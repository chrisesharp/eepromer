import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
     name='eepromer',  
     version='0.1',
     scripts=['eepromer'] ,
     author="Chris Sharp",
     author_email="chrisesharp@gmail.com",
     description="An EEPROM programmer utility package",
     long_description=long_description,
   long_description_content_type="text/markdown",
     url="https://github.com/chrisesharp/eepromer",
     packages=setuptools.find_packages(),
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
 )