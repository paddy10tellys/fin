import bs4 as bs  # web scraping
import datetime as dt
import os   # to create directories
import pandas as pd
import pandas_datareader.data as web
#import pandas.io.data as web
import pickle  # object serialization to save list of S&P500 companies
import requests
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

def get_data_from_google(reload_sp500=False):
    if reload_sp500:
        tickers = save_sp500_tickers()
    else:
        with open("sp500tickers.pickle","rb") as f:
            tickers = pickle.load(f)


    if not os.path.exists('stock_dfs'):  # directory doesn't  exist?
        os.makedirs('stock_dfs')  # then create it

    start = dt.datetime(2000, 1, 1)
    end = dt.datetime(2016, 12, 31)

    for ticker in tickers:
        if not os.path.exists('stock_dfs/{}.csv'.format(ticker)): # csv exists?
            #df=web.DataReader(ticker.strip('\n'), 'google', start, end)
            #df=web.DataReader("ticker", 'google', start, end)
            #df.to_csv('stock_dfs/{}.csv'.format(ticker))
            print(ticker)
        else:
            print('Already have {}'.format(ticker))


# get_data_from_google()

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
get_data_from_google()
# compile_data()
# visualize_data()
