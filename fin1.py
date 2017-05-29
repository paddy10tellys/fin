import datetime as dt
import matplotlib.pyplot as plt
from matplotlib import style
from matplotlib.finance import candlestick_ohlc
import matplotlib.dates as mdates
import pandas as pd
import pandas_datareader.data as web

style.use('ggplot')

# start = dt.datetime(2000, 1, 1)  # year, month, day
# end = dt.datetime(2016, 12, 31)  # year, month, day

# df = web.DataReader('TSLA', 'yahoo', start, end)
# df.to_csv('tsla.csv')
''' csv just cols so make the date col an index by setting the index on
that col by using index_col=0 & parse_dates = True. See docs'''
df = pd.read_csv('tsla.csv', parse_dates = True, index_col=0)
#df['100ma'] = df['Adj Close'].rolling(window=100).mean()

'''take ohlc data every 10/7 - this will shink the dataset '''
df_ohlc = df['Adj Close'].resample('10D').ohlc()
df_volume = df['Volume'].resample('10D').sum()

''' we need the col headers & the index as opp to just the values in the
df which is why this next line is necessary. If we reset the index then
date is now a col '''
df_ohlc.reset_index(inplace=True)
''' now covert date to mdates which is what matplotlib uses .maps a
datetime object to an mdate number'''
df_ohlc['Date'] = df_ohlc['Date'].map(mdates.date2num)



''' 6 rows, 1 col. starts  at 0,0 the top left corner'''
ax1 = plt.subplot2grid((6,1), (0,0), rowspan=5, colspan=1)

''' using sharex does not mean the x axes are the same it just links
zooming so when we zoom in on one we automatically zoom in on the other '''
ax2 = plt.subplot2grid((6,1), (5,0), rowspan=1, colspan=1, sharex=ax1)
''' x is the date given by the date index. y is the adjusted close price'''

'''xaxis_date() displays the mdates on the x axis '''
ax1.xaxis_date()

''' graph candlestick data against the dates'''
candlestick_ohlc(ax1, df_ohlc.values, width=2, colorup='g')

''' fill_between is nicer than the bars for visualising the volume
data. The three parameters are x, y, fill from zero to y'''
ax2.fill_between(df_volume.index.map(mdates.date2num), df_volume.values, 0)
plt.show()


