import requests # interaction with the web
import os  #  file system operations
import yaml # human-friendly data format
import re  # regular expressions
import pandas as pd # pandas... the best time series library out there
import datetime as dt # date and time functions
import io
import bs4 as bs  # web scraping



# search with regular expressions

# "CrumbStore":\{"crumb":"(?<crumb>[^"]+)"\}

url = 'https://uk.finance.yahoo.com/quote/AAPL/history' # url for a ticker symbol, with a download link
r = requests.get(url)  # download page
print(r)  # <Response [200]>
# https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
# new cookie & crumb appears with each download

txt = r.text # extract html

# print(txt)
# Now we need to extract the token from html.
# the string we need looks like this: "CrumbStore":{"crumb":"lQHxbbYOBCq"}
# regular expressions will do the trick!

pattern = re.compile('.*"CrumbStore":\{"crumb":"(?P<crumb>[^"]+)"\}')

#  print(pattern)

for line in txt.splitlines():  #  split txt into lines
    m = pattern.match(line)  # apply pattern to each line
    if m is not None:  #  matchobject has a match
        crumb = m.groupdict()['crumb']  #  call groupdict method on m
        #  value of key crumb assigned to str crumb

print('Crumb=',crumb)

cookie = r.cookies['B'] # the cookie we're looking for is named 'B'
''' http://docs.python-requests.org/en/master/user/quickstart/#cookies
the requests library has methods that will find cookies '''
print('Cookie: ', cookie)

# create data directory named twpData in the user folder

''' os functions work on strings representing file names & paths rather
than the actual file system. The expanduser method Returns a path-like
object which is an object representing a particular file system path
- the users home directory in this case '''
dataDir = os.path.expanduser('~')+'/twpData'  #  /home/pmy/twpData

if not os.path.exists(dataDir):
    os.mkdir(dataDir)

# save data to YAML file
data = {'cookie':cookie,'crumb':crumb}  # dictionary

dataFile = os.path.join(dataDir,'yahoo_cookie.yml')
#  /home/pmy/twpData/yahoo_cookie.yml

''' The YML file type is primarily associated with 'Javascript' by YAML.
YAML stand for "YAML Ain't Markup Language;". It is a human readable
data serialization language for converting a text files into a stream of
bytes in order to store the object or transmit it to memory, a database,
or a file. Its main purpose is to save the state of an object in order
to be able to recreate it when needed. The reverse process is called
deserialization.
organizes it into a format which is Human-readable. YAML may be used
 with multiple platforms of programming languages such as PHP, Python,
 Ruby, Perl, Javascript amongst others. '''

with open(dataFile,'w') as fid:
    yaml.dump(data,fid)
'''
start and end times of the requested data are in seconds since epoch
(1 Jan 1970) these are easey to get with timestamp()

https://query1.finance.yahoo.com/v7/finance/download/SPY?period1=1463754
366&period2=1495290366&interval=1d&events=history&crumb=DB/mJy8XKWr
 '''

# start with tuples ...
start = (2009,1,1)
end = (2017,5,20) #  print(type(end))   <class 'tuple'>

''' you can use * and ** when calling functions , like *args & **kwargs.
This is a shortcut that allows you to pass multiple arguments to a
function directly by using * to reference a list/tuple, or ** to
reference a dictionary. See lines below'''


# convert to seconds since epoch
start = int(dt.datetime(*start).timestamp())
''' argument after * must be an iterable, not not an int. We have to present
the value of the tuple "start" to datetime, call timsestamp() on it & then cast
the result to an int '''

end = int(dt.datetime(*end).timestamp())
print(start, "seconds since epoch")  # 1230768000 seconds since epoch
print(end, "seconds since epoch")  # 1495234800 seconds since epoch


# prepare input data as a tuple
data = (start, end, crumb)
print(data)

''' here we are presenting the tuple data to format using * and {0} is start
{1} is end and {1} is crumb '''
url = "https://query1.finance.yahoo.com/v7/finance/download/VXX?period1={0}&period2={1}&interval=1d&events=history&crumb={2}".format(*data)
print(url)
data = requests.get(url, cookies={'B':cookie})
''' gives the cookie back to the server on subsequent requets '''

print('requesting ticker data -- http status code ', data)

buf = io.StringIO(data.text)
''' An in-memory stream for text I/O is assigned to buf which acts as a
buffer for the text. The buffer is discarded when the close() method is
called. The main advantage of StringIO is that it can be used where a
file was expected '''


df = pd.read_csv(buf,index_col=0) # convert to pandas DataFrame
''' the first col contains dates & this is used as the index column '''
print(df.head())
