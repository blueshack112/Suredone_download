import pdb
import platform
import requests
import configparser
import json
import re
import time
import os
from os.path import expanduser


class LoadingError(Exception):
    pass

class UnauthorizedError(Exception):
    pass

class SureDone:
    def __init__(self, user, api_token):
        """
        Constructor function. Basically creates a header template for api calls.

        Parameters
        ----------
            - user : str
                User name for API
            - 'api_token' : str
                Auth token provided by the API
        """
        self.timeout = 15
        self.api_endpoint = 'https://api.suredone.com/v1/'
        self.headers = {}
        self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        self.headers['x-auth-integration'] = 'partnername'
        self.headers['x-auth-user'] = user
        self.headers['x-auth-token'] = api_token

    def apicall(self, typ, endpoint, data=None):
        """
        TODO: Document how the code is running.

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
            - data : ?
                The data that is meant to be sent in the API request.
        """
        # print(typ, endpoint, data)
        # Build url string by concatenating the main url with the sub module
        url = self.api_endpoint + endpoint
        error_count = 0

        # Main loop
        while True:
            # 3 or more errors break the loop
            if error_count >= 3:
                break
            try:
                # print(url,json.dumps(data),self.headers)
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
                print(' HTTP Error {} {} {} {}'.format(typ, url, data, e))
                print(' attempt', error_count)
                error_count += 1
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
                    print(' JSONDecodeError Error', typ, url, data)
                    print(resp.text)
                    error_count += 1
                    raise LoadingError
                
                # Return the JSON formatted data
                return r
            elif resp.status_code == 401:  # Unauthorized
                # Error handling. Handle for unauthorized error.
                print(json.dumps(self.headers, indent=4))
                raise UnauthorizedError
            elif resp.status_code == 403:
                try:
                    # Try to load the data in JSON to get more information on error
                    r = json.loads(resp.text)
                except json.decoder.JSONDecodeError:
                    # Error handling. Increment error counter and sleep for 15 seconds 
                    # and try again if the 403 error couldn't also be decoded to JSON either. 
                    print('api json.decoder 403', resp.text)
                    error_count += 1
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
                    print('api not message. 403', resp.text, data)
                    error_count += 1
                    time.sleep(15)
                    continue
            # ?? TODO: Find out more
            elif resp.status_code == 429:  # X-Rate-Limit-Time-Reset-Ms
                # print(' Rate limit in {}. Wait 40 sec'.format(url))
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
                error_count += 1
                print(' Error', error_count, resp.status_code, typ, url, data)
                print(resp.text)
                time.sleep(10)
                continue
            break
        print(' Error', error_count, typ, url, data)
        raise LoadingError


def purge(dir, pattern, inclusive=True):
    """
    A simple function to remove everything within a directory and it's subdirectories if the file name mathces a specific pattern.add()

    Parameters
    ----------
        - dir : str
            The top level path of the directory from where the searching will begin
        - pattern : regex-like str
            A regex-like string that defines the pattern that needs to be deleted
        - inclusive : boolean
            Currently only has a True implementation
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

if __name__ == '__main__':
    print('SureDone bulk downloader')

    # Loading configurations
    config = configparser.ConfigParser()
    sett_name = 'settings.ini'
    # Read the settings.ini file in the same folder as well as in ~\Appdata\Local folder
    # Exit the script if couldn't find the settings.ini file
    if not config.read(sett_name):
        if platform.system() == 'Windows':
            path = expanduser("~") + "\\AppData\\Local\\"
            if not config.read(path + 'settings.ini'):
                print('settings.ini not found')
                exit()
        else:
            print(sett_name + ' not found')
            exit()

    # Try to read the user and api_token from suredone_api set in the settings
    # Print error that the settings weren't found and exit    
    try:
        user = config['suredone_api']['user']
        api_token = config['suredone_api']['api_token']
    except KeyError:
        print('Not found user or api_token in suredone_api section')
        exit()

    # If the platform is windows, set the download path to the current user's Downloads folder
    if re.search('Windows', str(platform.platform())):
        path = expanduser("~") + "\\Downloads\\"
        purge(path, 'SureDone_')
    
    # Else, set the download path to the current folder
    else:
        path = ''
        purge('.', 'SureDone_')

    # If the directory has anything at all, remove all files that
    # start with 'SureDone_' in the directory and subdirectories.
    # TODO: This funciton has been called above. Why repeat?
    purge('.', 'SureDone_')

    # Prepare to send api call. Create the SureDone object and create the data dict
    sd = SureDone(user, api_token)
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

    # Iterate through each field and make sure there isn't a duplicate present
    for element in t:
        k = element
        if k not in seen:
            seen_add(k)
            field_list.append(k)

    # Rejoin the fields into a single string, separated by a ','
    data['fields'] = ','.join(field_list)

    # Invoke the GET API call in v1/bulk/exports sub module
    r = sd.apicall('get', 'bulk/exports', data)
    # print(json.dumps(r, indent=4))

    # If the returning json has a 'result' key with 'success' value...
    if r['result'] == 'success':
        # Get the file name(s?) of the newly downloaded file
        file_name = r['export_file']

        # Now that we have the file name, time to download the file
        # print(json.dumps(r, indent=4))
        e_count=0
        while True:
            # Invoke api call to the same module but with a filename and no data 
            r = sd.apicall('get', 'bulk/exports/' + file_name, {})

            # If the result was successfull...
            if r['result'] == 'success':
                # Define the path to where the file should be kept
                # ?? TODO: this path definition has ocurred twice now
                if re.search('Windows', str(platform.platform())):
                    path = expanduser("~") + "\\Downloads\\"
                else:
                    path = ''
                
                # Set the path, get the download URL of the file requested, and start a stream to download it
                save_to_file = path + 'SureDone_' + file_name
                resp = requests.get(r['url'], stream=True)
                idx=0
                with open(save_to_file, 'wb') as f:
                    for idx, chunk in enumerate(resp.iter_content(chunk_size=1024)):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)

                print('Saved to', save_to_file)
                break
            else:
                # If the api call with just the file name in the url wasn't successfull
                # Increase the error count and check if error count has crossed 10 or not.
                # More than 10 attempts with errors will end the code
                e_count +=1
                if e_count >10:
                    print(r)
                    print('Can not download {}'.format(''))
                    break
                else:
                    print('attempt',e_count,r)
                    time.sleep(30)
                    continue
    # If the returning JSON wasn't successful in the first place, end the code with a generic error.
    else:
        print('Can not export {}'.format())
