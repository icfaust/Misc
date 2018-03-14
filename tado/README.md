This test is dependent on the non-standard python packages of Flask. Everything else should be
standard in a typical python2.7 installation. To run the code, download the files, grant operational
permissions and run the associated shell script 'tadostart.sh'. A file named 'key.txt' should be
placed in the folder with only the text key for the TimeZoneDB web-API. 
The TimeZoneDB does not seem to work for all latitudes and longitudes, as I think it is only known
in relation to nearby cities. Please be careful of your inputs.  This package has been developed
for unix/linux use, and has not been tested on a windows machine.

Steps as a list:

1) Download contents of this folder
2) Create key.txt containing web-API key in the same folder
3) Check operational permissions
4) Check python2.7 and related Flask installation
5) run ./tadostart.sh
6) ctrl+C to stop the script
