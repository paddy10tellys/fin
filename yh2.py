import requests # interaction with the web
from collections import Counter
import os  #  file system operations
import yaml # human-friendly data format
import re  # regular expressions
import pandas as pd # pandas... the best time series library out there
import datetime as dt # date and time functions
import io
import bs4 as bs  # web scraping
import pickle  # object serialization to save list of S&P500 companies
import numpy as np
import pandas_datareader.data as web
import matplotlib.pyplot as plt
from matplotlib import style


style.use('ggplot')

def save_sp500_tickers():
    resp = requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    ''' Beautifulsoup turns html source code into a BeautifulSoup object
    which is more like a typical Python object '''
    soup = bs.BeautifulSoup(resp.text, "lxml")  # the txt of the wiki page source code
    ''' lxml is the htmlparser. Next look for wikitable sortable classes.'''
    table = soup.find('table', {'class':'wikitable sortable'})  # all tables
    ''' of class wikitable sortable nb there is only one on the wiki page '''
    tickers=[]
    #  ('tr')[1:] specifies for each row, after the header row
    for row in table.find_all('tr')[1:]:  # i.e., from 1 onward
        #  the ticker is the "table data" (td), we grab the .text of it
        ticker = row.find_all('td')[0].text  # zeroith col is the 1st col
        ''' the col is a col full of tickers '''
        if ticker.find('_'):
            ticker = ticker.replace('_','-')
            print("trying to read {}".format(ticker))
        mapping = str.maketrans('.','-')
        ticker = ticker.translate(mapping)
        tickers.append(ticker)  # add ticker to the list of tickers
        ''' tr is table row. 1 onward because 1st row contains col
            headers
            td is table data, each col basically. 0 as we want the
            1st i.e., zeroith col'''

    with open("sp500tickers.pickle","wb") as f:
        pickle.dump(tickers, f)
    print(tickers)
    return tickers



def get_cookie_crumb_from_yahoo():
    global cookie
    global crumb
    ''' Cookie=1hi96s1cij3jf&b=3&s=lv, Crumb=pQt.ELGlf4Z
    "CrumbStore":\{"crumb":"(?<crumb>[^"]+)"\}   NB this function only
    needs to be run once a year because the cookie-crumb pair is good
    for twelve months '''
    ticker = 'AAPL' # any ticker would do as we are after a
    ''' cookie-crumb pair in this function not the prices '''
    url = 'https://uk.finance.yahoo.com/quote/'+ticker+'/history'
    r = requests.get(url)  # download page
    print(r)  # <Response [200]>
    # https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
    # new cookie & crumb appears with subsequent download

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

    cookie = r.cookies['B'] # the cookie we're looking for is named 'B'
    ''' http://docs.python-requests.org/en/master/user/quickstart/#cookies
    the requests library has methods that will find cookies '''
    # print('Cookie: ', cookie)
    print('Cookie={}, Crumb={}'.format(cookie, crumb))



''' reload_sp500 is a flag that can be set to true or false elsewhere  '''
def get_data_from_yahoo(reload_sp500=False):
    cookie = '1hi96s1cij3jf&b=3&s=lv'
    crumb = 'pQt.ELGlf4Z'

    if reload_sp500:  # if reload_sp500 flag set to true
        tickers = save_sp500_tickers()  # run function to get tickers
    else:  # if reload_sp500 flag is set to false
        with open("sp500tickers.pickle","rb") as f:
            tickers = pickle.load(f)  # get the tickers from the pickle
            print('loading pickle')

    if not os.path.exists('stock_dfs'):  # directory doesn't exist?
        os.makedirs('stock_dfs')  # then create it
        print('stock_dfs directory created')

    for ticker in tickers:  # does individual ticker .csv already exist?
        if not os.path.exists('stock_dfs/{}.csv'.format(ticker)): # no?
            print('Saving stock_dfs/{}.csv'.format(ticker))
            # start with tuples ...
            start = (2009,1,1)
            end = (2017,5,20) #  print(type(end))   <class 'tuple'>
            '''
            you can use * and ** when calling functions , like *args & **kwargs.
            This is a shortcut that allows you to pass multiple arguments to a
            function directly by using * to reference a list/tuple, or ** to
            reference a dictionary. See lines below
            '''


            # convert to seconds since epoch
            start = int(dt.datetime(*start).timestamp())
            ''' argument after * must be an iterable, not an int. We have
            to present the value of the tuple "start" to datetime, call
            timsestamp() on it & then cast the result to an int '''

            end = int(dt.datetime(*end).timestamp())
            #  print(start, "seconds since epoch")  # 1230768000 seconds since epoch
            #  print(end, "seconds since epoch")  # 1495234800 seconds since epoch

            # prepare input data as a tuple
            data = (start, end, crumb)
            #  print(data)

            url = "https://query1.finance.yahoo.com/v7/finance/download/"+ticker+"?period1={0}&period2={1}&interval=1d&events=history&crumb={2}".format(*data)

            data = requests.get(url, cookies={'B':cookie})
            ''' gives the cookie back to the server on subsequent requets '''

            print('requesting ticker data -- http status code ', data)

            buf = io.StringIO(data.text)
            ''' An in-memory stream for text I/O is assigned to buf which acts as a
            buffer for the text. The buffer is discarded when the close() method is
            called. The main advantage of StringIO is that it can be used where a
            file was expected '''

            # print("buffer = ",buf)


            df = pd.read_csv(buf,index_col=0) # convert to pandas DataFrame
            ''' the first col contains dates & this is used as the index column '''
            print(df.head())
            df.to_csv('stock_dfs/{}.csv'.format(ticker))
        else:
            print('Already have {}'.format(ticker))


        print('***********************************************')




def compile_data():
    with open("sp500tickers.pickle", "rb") as f:
        tickers = pickle.load(f)
    # this function was causing hassle. This warning kept occurring
    ''' sys:1: DtypeWarning: Columns (129,151,208,218,219,225,231,232,
    249,258,270,284,308,314,328,347,355,374,388,392,393,403,416,424,429
    ,431,448,450,451,473,489) have mixed types. Specify dtype option on
    import or set low_memory=False.  Dtype Guessing (very bad). See
    https://stackoverflow.com/questions/24251219/pandas-read-csv-low-memory-and-dtype-options
    for the solution implemented below which was to use a converter on
    the Adjusted Close column'''
    def conv(val):  # this was the solution
        if not val:
            return 0
        try:
            return np.float64(val)
        except:
            return np.float64(0)
    main_df = pd.DataFrame()  # create an empty dataframe obj without cols or index
    for count,ticker in enumerate(tickers):  # enumerate through an interable
        df = pd.read_csv('stock_dfs/{}.csv'.format(ticker),converters={'Adj Close':conv})
        df.set_index('Date', inplace=True)
        df.rename(columns={'Adj Close': ticker}, inplace=True)  # what
        ''' used to be Adjusted Close is now ticker '''
        df.drop(['Open','High','Low', 'Close','Volume'], 1, inplace=True)
        ''' drop everything else on axes 1 which is the columns'''
        if main_df.empty:
            main_df = df  # boom! now it's not empty
        else:
            main_df = main_df.join(df, how="outer")
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
    #  df['AAPL'].plot()
    plt.show()
    df_corr = df.corr()  # correlates everything nb paid services!
    print(df_corr.tail())
    data = df_corr.values  # the inner values of the df - everything
    ''' except the index & the headers - a numpy array of the cols & rows '''
    fig = plt.figure()  # figure is the top level container that
    ''' matplotlib uses to contain & plot all of the plot elements '''
    ax = fig.add_subplot(1,1,1)  # 1x1 & is plot number 1
    heatmap = ax.pcolor(data, cmap=plt.cm.RdYlGn)  # to plot some colours
    ''' This heatmap is made using a range of colors, which can be a
    range of anything to anything, and the color scale is generated from
    the cmap that we use. RdYlGn, is a colormap that goes from red on the
    low side, yellow for the middle, and green for the higher part of the
    scale, which will give us red for negative correlations, green for
    positive correlations, and yellow for no-correlations. We'll add a
    side-bar that is a colorbar as a sort of "scale" for us: '''
    fig.colorbar(heatmap)  # a legend to depict ranges
    #  plot colours on a grid, company tick-marks at half-marks 0.5, 1.5
    ''' & so on '''
    ax.set_xticks(np.arange(data.shape[0]) + 0.5, minor=False)
    ax.set_yticks(np.arange(data.shape[1]) + 0.5, minor=False)

    ax.invert_yaxis()  # This will flip our yaxis, so that the graph is
    ''' a little easier to read, since there will be some space between
    the x's and y's. Generally matplotlib leaves room on the extreme
    ends of your graph since this tends to make graphs easier to read,
    but, in our case, it doesn't. Then we also flip the xaxis to be at
    the top of the graph, rather than the traditional bottom, again to
    just make this more like a correlation table should be '''
    ax.xaxis.tick_top()

    column_labels = df_corr.columns
    row_labels = df_corr.index
    ax.set_xticklabels(column_labels)
    ax.set_yticklabels(row_labels)
    plt.xticks(rotation=90)
    heatmap.set_clim(-1,1)  # colour density limits
    plt.tight_layout()
    #plt.savefig("correlations.png", dpi = (300))
    plt.show()


# MACHINE LEARNING STRATEGY
    ''' correlated companies rise & fall IN SYNC, some lead, some lag.
    ML can model this (classifier). Rise 2% buy, fall 2% sell, otherwise
    hold. Each model is on a per company basis but takes into account ALL
    other companies in the S&P500  '''

def process_data_for_labels(ticker):
    hm_days = 7  # going up, down, sideways in next 7/7 ???
    df = pd.read_csv('sp500_joined_closes.csv', index_col=0)
    tickers = df.columns.values.tolist()  # !!!!!!!!!!!!!!!!!!!!!!!!
    df.fillna(0,inplace=True)
    '''PERCENT CHANGE FORMULA (new - old)/old '''
    for i in range(1,hm_days+1):
        df['{}_{}d'.format(ticker,i)] = (df[ticker].shift(-i) - df[ticker]) / df[ticker]
    df.fillna(0, inplace=True)
    return tickers, df


'''args are the % changes that have been predicted for the coming 7/7 '''
def buy_sell_hold(*args):
    cols = [c for c in args]
    requirement = 0.02
    for col in cols:
        if col > requirement:
            return 1
        if col < -requirement:
            return -1
    return 0
    # this is mapped to a pandas dataframe - see below

def extract_featuresets(ticker):
    tickers, df = process_data_for_labels(ticker)  # the function returns
    ''' tickers & df remember nb see implentation above '''
      # create a new col using the mapped output from the buy_sell_hold()
    df['{}_target'.format(ticker)] = list(map( buy_sell_hold,
                                               df['{}_1d'.format(ticker)],
                                               df['{}_2d'.format(ticker)],
                                               df['{}_3d'.format(ticker)],
                                               df['{}_4d'.format(ticker)],
                                               df['{}_5d'.format(ticker)],
                                               df['{}_6d'.format(ticker)],
                                               df['{}_7d'.format(ticker)] ))
    ''' A Counter is a dict subclass for counting hashable objects. It is
    an unordered collection where elements are stored as dictionary keys
    and their counts are stored as dictionary values. Counts are allowed
    to be any integer value including zero or negative counts. The Counter
    class is similar to bags or multisets in other languages. Elements are
    counted from an iterable or initialized from another mapping (or counter): '''

    vals = df['{}_target'.format(ticker)].values.tolist()
    str_vals = [str(i) for i in vals]
    print('Data spread:', Counter(str_vals))
    df.fillna(0, inplace=True)
    df = df.replace([np.inf, -np.inf], np.nan)  # replace really big
    ''' infinite price changes with nan '''
    df.dropna(inplace=True)
    df_vals = df[[ticker for ticker in tickers]].pct_change()
    #df_vals = df[[ticker_name for ticker_name in tickers[0]]].pct_change()
    df_vals = df_vals.replace([np.inf, -np.inf], 0)
    df_vals.fillna(0, inplace=True)
    X = df_vals.values
    y = df['{}_target'.format(ticker)].values
    return X, y, df




#save_sp500_tickers()
#get_data_from_yahoo()
# compile_data()
#visualize_data()
#process_data_for_labels('XOM')
extract_featuresets('XOM')
