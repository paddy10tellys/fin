import requests # interaction with the web
import os  #  file system operations to create directories
import yaml # human-friendly data format
import re  # regular expressions
import pandas as pd # pandas... the best time series library out there
import datetime as dt # date and time functions
import io
import bs4 as bs  # web scraping
import pandas_datareader.data as web
#import pandas.io.data as web
import pickle  # object serialization to save list of S&P500 companies
import matplotlib.pyplot as plt
from matplotlib import style
style.use('ggplot')

def save_sp500_tickers():
    resp = requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = bs.BeautifulSoup(resp.text, "lxml")  # the txt of the wiki page source code
    ''' lxml is the htmlparser '''
    table = soup.find('table', {'class':'wikitable sortable'})
    tickers=[]

    for row in table.find_all('tr')[1:]:
        ticker = row.find_all('td')[0].text
        if ticker.find('_'):
            ticker = ticker.replace('_','-')
            print("trying to read {}".format(ticker))
        mapping = str.maketrans('.','-')
        ticker = ticker.translate(mapping)
        tickers.append(ticker)
        ''' tr is table row. 1 onward because 1st row contains col
            headers
            td is table data, each col basically. 0 as we want the
            1st zeroith col'''

    with open("sp500tickers.pickle","wb") as f:
        pickle.dump(tickers, f)

    print(tickers)

    return tickers

#save_sp500_tickers()

def get_data_from_yahoo(reload_sp500=False):
    if reload_sp500:
        tickers = save_sp500_tickers()
    else:
        with open("sp500tickers.pickle","rb") as f:
            tickers = pickle.load(f)
            print('loading pickle')


    if not os.path.exists('stock_dfs'):  # directory doesn't  exist?
        os.makedirs('stock_dfs')  # then create it
        print('stock_dfs directory created')

    for ticker in tickers[:5]:
        if not os.path.exists('stock_dfs/{}.csv'.format(ticker)): # csv exists?
            url = 'https://uk.finance.yahoo.com/quote/ticker/history' # url for a ticker symbol, with a download link
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

            buf = io.StringIO(data.text)
            ''' An in-memory stream for text I/O is assigned to buf which acts as a
            buffer for the text. The buffer is discarded when the close() method is
            called. The main advantage of StringIO is that it can be used where a
            file was expected '''


            df = pd.read_csv(buf,index_col=0) # convert to pandas DataFrame
            ''' the first col contains dates & this is used as the index column '''
            print(df.head())




def compile_data():
    with open("sp500tickers.pickle", "rb") as f:
        tickers = pickle.load(f)

    main_df = pd.DataFrame()  # create an empty dataframe obj without cols or index

    for count,ticker in enumerate(tickers):  # enumerate through an interable
        df = pd.read_csv('stock_dfs/{}.csv'.format(ticker))
        df.set_index('Date', inplace=True)

        df.rename(columns = {'Close': ticker}, inplace=True)
        df.drop(['Open','High','Low','Volume'], 1, inplace=True)  # df just Close price

        if main_df.empty:
            main_df = df  # boom! now it's not empty
        else:
            main_df= main_df.join(df, how='outer')

            '''form a single dataframe by joining all the individual
            dataframes together into one big df that just contains cols
            of the sp500 tickers close prices as cols of close prices
            how = outer fills in any blanks in the various cols with naN
            data so making everything compatible '''

            if count % 10 == 0: # every 10th
                print(count)

    print(main_df.head())
    main_df.to_csv('sp500_joined_closes.csv')

def visualize_data():
    df = pd.read_csv('sp500_joined_closes.csv')
    # df['AAPL'].plot()
    # plt.show()
    df_corr = df.corr()  # correlates everything nb paid services!
    print(df_corr.tail())

# save_sp500_tickers()
get_data_from_yahoo()
# compile_data()
# visualize_data()
