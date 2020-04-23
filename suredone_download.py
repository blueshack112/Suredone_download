#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Suredone Download

@contributor: Hassan Ahmed
@contact: ahmed.hassan.112.ha@gmail.com
@owner: Patrick Mahoney
@version: 1.0.3

This module is created to use the Suredone API to create a custom CSV of store's 
product and sales records, and get it downloaded
The CSV currently intended to download has the following columns:
    - guid
    - stock
    - price
    - msrp
    - cost
    - title
    - longdescription
    - condition
    - brand
    - upc
    - media1
    - weight
    - datesold
    - totalsold
    - manufacturerpartnumber
    - warranty
    - mpn
    - ebayid
    - ebaysku
    - ebaycatid
    - ebaystoreid
    - ebayprice
    - ebaytitle
    - ebaystarttime
    - ebayendtime
    - ebaysiteid
    - ebaysubtitle
    - ebaypaymentprofileid
    - ebayreturnprofileid
    - ebayshippingprofileid
    - ebaybestofferenabled
    - ebaybestofferminimumprice
    - ebaybestofferautoacceptprice
    - ebaybuyitnow
    - ebayupcnot
    - ebayskip
    - amznsku
    - amznasin
    - amznprice
    - amznskip
    - walmartskip
    - walmartprice
    - walmartcategory
    - walmartdescription
    - walmartislisted
    - walmartinprogress
    - walmartstatus
    - walmarturl
    - total_stock
    
Usage:
    TODO: This part and all below
    $ python rearrange.py [-f <filepath>] [options]

Parameters/Options:
    -h                      : usage help and examples
    -f  | --file            : define input CSV path 
    -o  | --output_file     : define output CSV path
    -i  | --max_iterations  : define max iterations allowed on a single GUID
    -v  | --verbose         : show program execution details (may increase execution time)
    -l  | --log             : level of information in log file 
                              (0 - nothing | 1 - over max iterations | 2 - all information)
                              
Example:
    $ python rearrange.py -f [source.csv]
    $ python rearrange.py -file [source.csv]

    $ python rearrange.py -f [source.csv] -o [output.csv]
    $ python rearrange.py -file [source.csv] --output_file [output.csv]

    $ python rearrange.py -f [source.csv] -o [output.csv] -i 1000
    $ python rearrange.py -file [source.csv] --output_file [output.csv] --max_iterations 1000

Todo:
    - Every exit must change to a safe exit where the log file is told why the script exited
"""

# Help message
HELP_MESSAGE = """
Usage:
    TODO: this part and all below
    From all the arguments available, the input file path is necessary and the
    script will not work if it is not provided.
    
    $ python rearrange.py [-f <filepath>] [options]

Parameters/Options:
    -h                      : usage help and examples
    -f  | --file            : define input CSV path 
    -o  | --output_file     : define output CSV path
    -i  | --max_iterations  : define max iterations allowed on a single GUID
    -v  | --verbose         : show program execution details (may increase execution time)
    -l  | --log             : level of information in log file 
                              (0 - nothing | 1 - over max iterations | 2 - information of all)

Example:
    $ python rearrange.py -f [source.csv]
    $ python rearrange.py -file [source.csv]

    $ python rearrange.py -f [source.csv] -o [output.csv]
    $ python rearrange.py -file [source.csv] --output_file [output.csv]

    $ python rearrange.py -f [source.csv] -o [output.csv] -i 1000
    $ python rearrange.py -file [source.csv] --output_file [output.csv] --max_iterations 1000
"""

# Imports
import pdb
import sys
import getopt
import platform
import requests
import yaml
import json
import re
import time
import os
from os.path import expanduser
from datetime import datetime

# TODO: EVERY PRINT STATEMENT NEEDS TO GO

PYTHON_VERSION = float(sys.version[:sys.version.index(' ')-2])

def getCurrentTimestamp():
    """
    Simple function that calculates the current time stamp and simply formats it as a string and returns.
    Mainly aimed for logging.

    Returns
    -------
        - timestamp : str
            A formatted string of current time
    """
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def writeLog(message, logFilePath, verbose=False, severity='normal', data=None):
    """
    Function that writes out to the log file and console based on verbose.
    The function will change behavior slightly based on severity of the message.

    Parameters
    ----------
        - message : str
            Message to write
        - logFilePath : str
            Path that points to the log file
        - verbose : bool
            Modifier to print results out to the console or not.
        - severity : str
            Defines what the message is related to. Is the message:
                - [N] : A 'normal' notification
                - [W] : A 'warning'
                - [E] : An 'error'
                - [!] : A 'code-breaker error' (errors that are followed by the script exitting)
        - data : dict
            A dictionary that will contain additional information when a code-breaker error occurs
            Attributes:
                - code : error code
                    1 : Generic error, only print the message.
                    2 : An API call was not successful. Response object attached.
                    3 : YAML loading error. Error object attached
                - response : str
                    JSON-like str - the response recieved from the request in conern at the point of error.
                - error : str
                    String produced by exception if an exception occured
    """
    if not os.path.exists(logFilePath):
        logFile = open(logFilePath, 'w')
    else:
        logFile = open(logFilePath, 'a')
    
    # Get a timestamp
    timestamp = getCurrentTimestamp()

    # Format the message based on severity
    if severity == 'normal':
        indicator = '[N]'
        toWrite = indicator + '|' + timestamp + ':   ' + message
    elif severity == 'warning':
        indicator = '[W]'
        toWrite = indicator + '|' + timestamp + ':   ' + message
    elif severity == 'code-breaker':
        indicator = '[!]'
        toWrite = indicator + '|' + timestamp + ':   ' + message
        
        if data['code'] == 2: # Response recieved but unsuccessful
            details = '\n[ErrorDetailsStart]\n' + data['response'] + '\n[ErrorDetailsEnd]'
            toWrite = toWrite + details
        elif data['code'] == 2: # YAML loading error
            details = '\n[ErrorDetailsStart]\n' + data['error'] + '\n[ErrorDetailsEnd]'
            toWrite = toWrite + details
    
    # Write out the message
    logFile.write(toWrite + '\n')
    if verbose: print(toWrite)

def main(argv):
    # Check if python version is 3.5 or higher
    if not PYTHON_VERSION >= 3.5:
        writeLog("Must use Python version 3.5 or higher!", logFilePath, severity='code-breaker', data={'code':1})
        exit()

    # Parse arguments
    waitTime, configPath = parseArgs(argv)

    # TODO: add more arguments data here
    writeLog("SureDone bulk downloader initalized.", logFilePath, severity='normal')
    writeLog("Wait time: {} seconds.".format(waitTime), logFilePath, severity='normal')
    writeLog("Configurations path: {}.".format(configPath), logFilePath, severity='normal')

    # Parse configuration
    user, apiToken = loadConfig(configPath)

    writeLog("Configuration read.", logFilePath, severity='normal')
    
    # Initialize API handler object
    sureDone = SureDone(user, apiToken, waitTime)

    # Get data to send to the bulk/exports sub module
    data = getDataForExports()

    # Invoke the GET API call to bulk/exports sub module
    exportRequestResponse = sureDone.apicall('get', 'bulk/exports', data)
    
    writeLog("API response recieved.", logFilePath, severity='normal')
    
    # If the returning json has a 'result' key with 'success' value...
    if exportRequestResponse['result'] == 'success':
        # Get the file name of the newly exported file
        fileName = exportRequestResponse['export_file']

        # Get download Path
        downloadPath = getDefaultDownloadPath()

        # TODO: This will be removed when preserve is implemented
        writeLog("Purged existing files.", logFilePath, severity='normal')

        # Download and save the file
        downloadExportedFile(fileName, downloadPath, sureDone)

        # TODO: safeExit(marker='execution complete')

    # If the returning JSON wasn't successful in the first place, end the code with a generic error.
    else:
        writeLog("Can not export for some reason.", logFilePath, severity='code-breaker', data={'code':2, 'response':exportRequestResponse})

def loadConfig (configPath):
    """
    Function that parses the configuration file and reads user and apiToken variables

    Parameters
    ----------
        - configPath : str
            Path to the configuration file
    
    Returns
    -------
        - user : str
            Username from the configuration file
        - apiToken : str
            Api authentication token from the configuration file
    """
    # Loading configurations
    with open(configPath, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            writeLog("Error while loading YAML.", logFilePath, severity='code-breaker', data={'code':3, 'error':exc})
    
    # Try to read the user and api_token from suredone_api set in the settings
    # Print error that the settings weren't found and exit
    try:
        user = config['user']
        apiToken = config['token']
    except KeyError as exc:
        writeLog("Not found user or token in config file.", logFilePath, severity='code-breaker', data={'code':3, 'error':exc})
        exit()
    return user, apiToken

def getDefaultDownloadPath():
    """
    Function to check the operating system and determine the appropriate 
    download path for the export file based on operating system.

    This funciton also purges the whole directory with any previous export files.
    
    Returns
    -------
        - downloadPath : str
            A valid path that points to the diretory where the file should be downloaded
    TODO:
    -----
        - Implement preserve argument. If preserve is activated, don't purge the files
    """
    # If the platform is windows, set the download path to the current user's Downloads folder
    if sys.platform == 'win32' or sys.platform == 'win64': # Windows
        downloadPath = os.path.expandvars(r'%USERPROFILE%')
        downloadPath = os.path.join(downloadPath, 'Downloads')
        purge(downloadPath, 'SureDone_')
        return downloadPath

    # If Linux, set the download path to the $HOME/downloads folder
    elif sys.platform == 'linux' or sys.platform == 'linux2': # Linux
        downloadPath = expanduser('~')
        downloadPath = os.path.join(downloadPath, 'downloads')
        if os.path.exists(downloadPath):
            purge(downloadPath, 'SureDone_')
        else:   # Create the downloads directory
            os.mkdir(downloadPath)
        return downloadPath

def getDataForExports():
    """
    Function that prepares the data that will be sent to the bulk/exports sub module.
    
    Returns
    -------
        - data : dict
            Dictionary that contains all the necessary key-value pairs that need to be sent to the Suredone API's bulk/exports sub module.
    """
    # Prepare to send api call. Create the SureDone object and create the data dict
    data = {}
    data['type'] = 'items'
    data['mode'] = 'include'
    # data['fields'] = 'guid,stock,price, msrp,cost,title,condition,brand,media1,weight,fitmentfootnotes, manufacturerpartnumber, otherpartnumber,chaincablepattern, compatibletiresizes,caution, howmanywheelsdoesthisdo,howmanytiresdoesthiscover,ebayid,ebaypaymentprofileid,ebayreturnprofileid,ebayshippingprofileid'
    data['fields'] ='guid,stock,price,msrp,cost,title,longdescription,condition,brand,upc,media1,weight,datesold,totalsold,manufacturerpartnumber,warranty,mpn,ebayid,ebaysku,ebaycatid,ebaystoreid,ebayprice,ebaytitle,ebaystarttime,ebayendtime,ebaysiteid,ebaysubtitle,ebaypaymentprofileid,ebayreturnprofileid,ebayshippingprofileid,ebaybestofferenabled,ebaybestofferminimumprice,ebaybestofferautoacceptprice,ebaybuyitnow,ebayupcnot,ebayskip,amznsku,amznasin,amznprice,amznskip,walmartskip,walmartprice,walmartcategory,walmartdescription,walmartislisted,walmartinprogress,walmartstatus,walmarturl,total_stock'

    # Split the data fields based on ',' and they strip each field of any spaces
    t=list(map(lambda x: x.strip(' '),data['fields'].split(',')))
    seen = set()
    seen_add = seen.add
    field_list = list()

    # Iterate through each field and make sure a duplicate isn't present
    for element in t:
        k = element
        if k not in seen:
            seen_add(k)
            field_list.append(k)

    # Rejoin the fields into a single string, separated by a ','
    data['fields'] = ','.join(field_list)

def downloadExportedFile(fileName, downloadPath, sureDone):
    """
    Fucntion that is invoked once the file is exported and is ready to download.
    Invokes the download stream, reads it and write to the file in the decided download directory.

    Parameters
    ----------
        - fileName : str
            Name of the file that is being saved.
        - downloadPath : str
            Path to the download directory.
        - sureDone : SureDone object
            Object of the SureDone API handler class
    """
    errorCount=0
    while True:
        # Invoke api call to the same module but with a filename and no data 
        fileDownloadURLResponse = sureDone.apicall('get', 'bulk/exports/' + fileName, {})

        # If the result was successfull...
        if fileDownloadURLResponse['result'] == 'success':
            # Set the path, get the download URL of the file requested, and start a stream to download it
            writeLog("Starting file download.", logFilePath, severity='normal')
            downloadedFilePath = downloadPath + 'SureDone_' + fileName
            downloadStream = requests.get(fileDownloadURLResponse['url'], stream=True)
            
            # Get all the file bytes in the stream and write to the file
            index = 0
            with open(downloadedFilePath, 'wb') as downloadedFile:
                for index, chunk in enumerate(downloadStream.iter_content(chunk_size=1024)):
                    if chunk:  # filter out keep-alive new chunks
                        downloadedFile.write(chunk)
            writeLog("Saved to " + downloadedFilePath, logFilePath, severity='normal')
            break
        else:
            # If the api call with the file name in the url wasn't successfull
            # Increase the error count and check if error count has crossed 10 or not.
            # More than 10 attempts with errors will end the code
            errorCount += 1
            if errorCount > 10:
                writeLog("Can not download.", logFilePath, severity='code-breaker', data={'code':2, 'response':fileDownloadURLResponse})
                # TODO: exit()
                break
            else:
                writeLog('Attempt ' + str(errorCount) + ' ' + str(fileDownloadURLResponse), logFilePath, severity='warning')
                time.sleep(30)
                continue

def parseArgs(argv):
    """
    Function that parses the arguments sent from the command line 
    and returns the behavioral variables to the caller.

    Parameters
    ----------
        - argv : str
            Arguments sent through the command line
    
    Returns
    -------
        - waitTime : int
            - The time defined in seconds by the user before which the requests must not timeout if a response is not received from the API
            - Can be float in order to access millisecond scale
    """
    # Defining options in for command line arguments
    options = "hw:f:"
    long_options = ["help", "wait=", "file="]
    
    # Arguments
    waitTime = 15
    configPath = 'suredone.yaml'
    customPathFoundAndValidated = False

    # Extracting arguments
    try:
        opts, args = getopt.getopt(argv, options, long_options)
    except getopt.GetoptError:
        # Not logging here since this is a command-line feature and must be printed on console
        print ("Error in arguments!")
        print (HELP_MESSAGE)
        exit()
    for option, value in opts:
        if option == '-h':
            # Not logging here since this is a command-line feature and must be printed on console
            print (HELP_MESSAGE)
            sys.exit()
        elif option in ("-w", "--wait"):
            waitTime = float(value)
        elif option in ("-f", "--file"):
            configPath = value
            customPathFoundAndValidated = validateConfigPath(configPath)

    # If custom path to config file wasn't found, search in default locations
    if not customPathFoundAndValidated:
        configPath = getDefaultConfigPath()
    
    return waitTime, configPath

def validateConfigPath(configPath):
    """
    Function to validate the provided config file path.

    Parameters
    ----------
        - configPath : str
            Path to the configuration file
    Returns
    -------
        - validated : bool
            A True or False as a result of the validation of the path
    """
    # Check extension, must be YAML
    if not configPath.endswith('yaml'):
        writeLog("Configuration file must be .yaml extension.\nLooking for configuration file in default locations.", logFilePath, severity='error')
        return False

    # Check if file exists
    if not os.path.exists(configPath):
        writeLog("Specified path to the configuration file is invalid.\nLooking for configuration file in default locations.", logFilePath, severity='error')
        return False
    else:
        return True

def getDefaultConfigPath():
    """
    Function to validate the provided config file path.

    Returns
    -------
        - configPath : str
            Path to the configuration file if found in the default locations
    """
    fileName = 'suredone.yaml'
    # Check in current directory
    directory = os.getcwd()
    configPath = os.path.join(directory, fileName)
    if os.path.exists(configPath):
        return configPath
    
    # Check in alternative locations
    if sys.platform == 'win32' or sys.platform == 'win64': # Windows
        directory = os.path.expandvars(r'%LOCALAPPDATA%')
        configPath = os.path.join(directory, fileName)
        if os.path.exists(configPath):
            return configPath
    elif sys.platform == 'linux' or sys.platform == 'linux2': # Linux
        directory = expanduser('~')
        configPath = os.path.join(directory, fileName)
        if os.path.exists(configPath):
            return configPath
    else:
        writeLog("Platform couldn't be recognized. Are you sure you are running this script on Windows or Ubuntu Linux?", logFilePath, severity='code-breaker', data={'code':1})
        exit()

    writeLog("suredone.yaml config file wasn't found in default locations!\nSpecify a path to configuration file using (-f --file) argument.", logFilePath, severity='code-breaker', data={'code':1})
    exit()

def getLogPath():
    """
    Function that will determine the default log file path based on the operating system being used.
    Will also create appropriate directories they aren't present.

    Returns
    -------
        - logFilePath : str
            Path to the log file.
    """
    # Define the file name for logging
    temp = datetime.now().strftime('%Y_%m_%d-%H-%M-%S')
    logFileName = "suredone_download_" + temp + ".log"

    # If the platform is windows, set the log file path to the current user's Downloads/log folder
    if sys.platform == 'win32' or sys.platform == 'win64': # Windows
        logFilePath = os.path.expandvars(r'%USERPROFILE%')
        logFilePath = os.path.join(logFilePath, 'Downloads')
        logFilePath = os.path.join(logFilePath, 'log')
        if os.path.exists(logFilePath):
            return os.path.join(logFilePath, logFileName)
        else:   # Create the log directory
            os.mkdir(logFilePath)
            return logFilePath + logFileName

    # If Linux, set the download path to the $HOME/downloads folder
    elif sys.platform == 'linux' or sys.platform == 'linux2': # Linux
        logFilePath = expanduser('~')
        logFilePath = os.path.join(logFilePath, 'log')
        if os.path.exists(logFilePath):
            return os.path.join(logFilePath, logFileName)
        else:   # Create the log directory
            os.mkdir(logFilePath)
            return os.path.join(logFilePath, logFileName)

""" Custom Exceptions that will be caught by the script """
class LoadingError(Exception):
    pass

class UnauthorizedError(Exception):
    pass

class SureDone:
    """ A driver class to manage connection and make requests to the Suredone API """
    def __init__(self, user, api_token, timeout):
        """
        Constructor function. Basically creates a header template for api calls.

        Parameters
        ----------
            - user : str
                User name for API
            - 'api_token' : str
                Auth token provided by the API
        """
        self.timeout = timeout
        self.api_endpoint = 'https://api.suredone.com/v1/'
        self.headers = {}
        self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        self.headers['x-auth-integration'] = 'partnername'
        self.headers['x-auth-user'] = user
        self.headers['x-auth-token'] = api_token
    
    def apicall(self, typ, endpoint, data=None):
        """
        Function that will concatenate the intended endpoint with the main URL that
        goes to the Suredone API and initiate the request with the provided data.

        Parameters
        ----------
            - typ : str
                Defines the type of request. (REST functionality)
                Available types:
                    - get
                    - put
                    - post
                    - delete
            - endpoint : str
                Specific module of the API that needs to be called.
            - data : dict
                The data that is meant to be sent in the API request in key-value dict format.
        
        Returns
        -------
            - r : str
                The JSON formatted response data after the request was made
        """
        # Build url string by concatenating the main url with the sub module
        url = self.api_endpoint + endpoint
        errorCount = 0

        # Main loop
        while True:
            # 3 or more errors break the loop
            if errorCount >= 3:
                break
            try:
                # Invoke the corresponding api call based on the type
                if typ == 'get':
                    resp = requests.get(url, params=data, headers=self.headers, timeout=self.timeout)
                elif typ == 'put':
                    resp = requests.put(url, data=json.dumps(data), headers=self.headers, timeout=self.timeout)
                elif typ == 'post':
                    resp = requests.post(url, data=json.dumps(data), headers=self.headers, timeout=self.timeout)
                elif typ == 'delete':
                    resp = requests.delete(url, data=json.dumps(data), headers=self.headers, timeout=self.timeout)
            except requests.exceptions.RequestException as e:
                # Error handling. Increment error counter and sleep for
                # 15 seconds and try again if error was ocurred
                temp = 'HTTP Error {} {} {} {}.'.format(typ, url, data, e) + '\nAttempt ' + str(errorCount)
                writeLog(temp, logFilePath, severity='error')
                errorCount += 1
                time.sleep(15)
                continue

            # If the response code is 200 (Which means OK)
            if resp.status_code == requests.codes.ok:
                # Try loading the response in json format
                try:
                    r = json.loads(resp.text)
                except json.decoder.JSONDecodeError:
                    # Error handling. Increment error counter and raise LoadingError
                    # if the response was OK but data couldn't be read in JSON
                    temp = 'JSONDecodeError Error ' + typ + ' ' + url + ' ' + data + "\n" + resp.text
                    writeLog(temp, logFilePath, severity='error')
                    errorCount += 1
                    # TODO: remove custom exceptions probably
                    raise LoadingError
                
                # Return the JSON formatted data
                return r
            elif resp.status_code == 401:  # Unauthorized
                # Error handling. Handle for unauthorized error.
                writeLog(json.dumps(self.headers, indent=4), logFilePath, severity='error')
                raise UnauthorizedError
            elif resp.status_code == 403:
                try:
                    # Try to load the data in JSON to get more information on error
                    r = json.loads(resp.text)
                except json.decoder.JSONDecodeError:
                    # Error handling. Increment error counter and sleep for 15 seconds 
                    # and try again if the 403 error couldn't also be decoded to JSON either.
                    writeLog('API json.decoder 403 ' + resp.text, logFilePath, severity='error')
                    errorCount += 1
                    time.sleep(15)
                    continue
                try:
                    # If the message tells us that the account has been expired
                    if r['message'] == 'The requested Account has expired.':
                        print('The requested Account has expired.')
                        raise LoadingError
                except KeyError:
                    # Error handling. Increment error counter and sleep for 15 seconds
                    # and try again if r['message'] wasn't present in the response.
                    writeLog('Api not message: 403 ' + resp.text + ' ' + data, logFilePath, severity='error')
                    errorCount += 1
                    time.sleep(15)
                    continue
            # ?? TODO: Find out more
            elif resp.status_code == 429:  # X-Rate-Limit-Time-Reset-Ms
                time.sleep(40)
                continue
            # elif resp.status_code == 422:
            #     error_count += 1
            #     print(' Error 422', error_count,resp.status_code, typ, url, data)
            #     print(resp.headers)
            #
            #     print(resp.text)
            #     time.sleep(60)
            #     continue
            else:
                errorCount += 1
                temp = 'Error' + ' ' + errorCount + ' ' + resp.status_code + ' ' + typ + ' ' + url + ' ' + data + '\n' + resp.text
                writeLog(temp, logFilePath, severity='error')
                time.sleep(10)
                continue
            break
        # TODO: logxx
        temp = 'Error ' + str(errorCount) + ' ' + typ + ' ' + url + ' ' + data
        writeLog(temp, logFilePath, severity='error')
        raise LoadingError

def purge(dir, pattern, inclusive=True):
    """
    A simple function to remove everything within a directory and it's subdirectories if the file name mathces a specific pattern.

    Parameters
    ----------
        - dir : str
            The top level path of the directory from where the searching will begin
        - pattern : regex-like str
            A regex-like string that defines the pattern that needs to be deleted
        - inclusive : boolean
            Currently only has a True implementation
    
    Returns
    -------
        - count : int
            The number files that were removed by the function
    """
    count = 0
    regexObj = re.compile(pattern)
    for root, dirs, files in os.walk(dir, topdown=False):
        for name in files:
            path = os.path.join(root, name)
            if bool(regexObj.search(path)) == bool(inclusive):
                os.remove(path)
                count += 1
                # for name in dirs:
                #     path = os.path.join(root, name)
                #     if len(os.listdir(path)) == 0:
                #         os.rmdir(path)
    return count

# Determine log file path
logFilePath = getLogPath()

if __name__ == "__main__":
    main(sys.argv[1:])