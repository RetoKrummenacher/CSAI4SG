# Analysis of traffic intensity and car park usage in Basel since 2019

Project in course of the seminar CSAI4SG, Fall 2021, University of Basel

michellej.boesiger@stud.unibas.ch   
erind.shima@stud.unibas.ch   
reto.krummenacher@unibas.ch   

## Set up Conda environment

We use Python in [Miniconda](https://docs.conda.io/en/latest/miniconda.html#) during this project. Too, we need the OpenStreetMap Python interface [OSMnx](https://osmnx.readthedocs.io/en/stable/). 

1. Start *Anaconda Prompt(miniconda3)* terminal
2. Create a new environment based on the *osmnx* module. Some details are described [here](https://osmnx.readthedocs.io/en/stable/):
    - ```conda config --prepend channels conda-forge``` 
    - ```conda create -n osmnx --strict-channel-priority osmnx jupyterlab```     
    Note that jupyterlab needs to be included in that command.
3. Activate *osmnx* environment: ```conda activate osmnx```.
4. Install all the necessary packages into your *osmnx* environment by entering below commands in your *miniconda3* terminal.
    - ```conda install pandas```
    - ```conda install folium```
    - ```conda install matplotlib```
    - ```conda install selenium```
    - ```conda install pillow```
    - ...  
5. Start Jupyter Notebook from the minicoda terminal: ```jupyter notebook```
6. For rendering the HTML map in Firefox Browser to create an PNG image download [Gecko driver](https://github.com/mozilla/geckodriver/releases)

