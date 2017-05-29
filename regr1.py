import pandas as pd
import numpy as np
import quandl, math, datetime
from sklearn import preprocessing, cross_validation, svm
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt  # graphing
from matplotlib import style
import pickle  # for serialisation of python objects. Like a file. Open
#  it, use it, save it, reuse it

style.use('ggplot')
# features are descriptive attributes, labels are what you are trying to predict

df = quandl.get('WIKI/GOOGL')

df = df[['Adj. Open', 'Adj. High', 'Adj. Low', 'Adj. Close','Adj. Volume']]

#  HL_PCT is a proxy for the trend
df['HL_PCT'] = (df['Adj. High'] - df['Adj. Low']) / df['Adj. Low'] * 100.0
''' HL_PCT is the +ve or -ve percentage daily change of the low price.
If the % change is a positive one then the trend line is up. If the
%change is negative then the trend line is down '''

# PCT_change is a proxy for the daily volatility
df['PCT_change'] = (df['Adj. Close'] - df['Adj. Open']) / df['Adj. Open'] * 100.0

df = df[['Adj. Close', 'HL_PCT','PCT_change', 'Adj. Volume']]  # these are
''' key features that we speculate will allow us to accurately predict the
close price in the future '''
#print(df.head())
forecast_col = 'Adj. Close'  # this declared like this so it can be
''' conveniently changed prn if later we decide to forecast based on some
other feature'''
df.fillna(-99999, inplace=True)  # fill in missing data nb is treated
''' as an outlier eg NaN not a number becomes 99999'''

forecast_out = int(math.ceil(0.01*len(df)))  # math.ceil just rounds
''''the float that .ceil returns to the nearest whole number & this is
 used for the numbers of days out. Here 0.01 means 1% of the entire
 length of the dataset held in the dataframe. Use int as days. The next
 line creats a new col for the label which is the future  price predicted
 by forecast_out. This has to be shifted up. The neg sign shifts up '''
df['label']=df[forecast_col].shift(-forecast_out)  #  shifts column UP
''' so now each row now has a label forecast column holding the adj close
price we are predicting in the future '''

''' NB TYPICAL MACHINE LEARNING CONVENTION: Is to define X (capital x),
as the features, and y (lowercase y) as the label that corresponds to
the features'''

X = np.array(df.drop(['label', 'Adj. Close'],1)) # 1 is the axis number (0 for rows
''' and 1 for columns). So X is everything except the label column
converted to a numpy array '''

X = preprocessing.scale(X)  # data features now in range -1 to +1

X_lately = X[-forecast_out:]  # X_lately is the X's from negative
''' forecast_out i.e., the most recent features that we predict against
to obtain the y's we haven't got yet. When he have the y's we can get the
m & c from the graph y= mX + c & so we have done linear regression '''

X = X[:-forecast_out]  # X is X to the point of negative forecast_out

df.dropna(inplace=True)  # drop any remaining NaN information
y = np.array(df['label'])  # define our y variable, which is our label,
''' as simply the label column of the dataframe, converted to a numpy
array '''

X_train, X_test, y_train, y_test = cross_validation.train_test_split(X, y, test_size=0.2)
'''Scikit-learn has a collection of classes which can be used to generate
randomly split lists of train/test indices for each iteration of the chosen
cross-validation strategy. The data is shuffled but the X, y bindings are
are retained. NB Test error = ave error found on testing new data not used
to train the model. Flexibility = degrees of freedom available to fit the
model to the training data. LR is v inflexible as it only allows 2doF
wheras a high-degree polynomial is v flexible as it has many. The goal of
cross-validation is to accurately *estimate* the test error which we
never actually know in practice. Another goal is to select the optimal
flexibility of the chosen method in order to minimise the errors associated
with bias and variance. K-fold cross-validation improves upon the
validation set approach by dividing the n observations into k mutually
exclusive, and approximately equally sized, subsets known as "folds".
The first fold becomes a validation set, while the remaining k−1 folds
(aggregated together) become the training set. The model is fit on the
training set and its test error is estimated on the validation set. This
procedure is repeated k times, with each repetition holding out a fold
as the validation set, while the remaining k−1 are used for training.'''

# clf = svm.SVR()  #  a regression classifier
clf = LinearRegression(n_jobs=-1)  # a better regression classifier nb
'''the parameter -1 specifies the use of all available threads '''

clf.fit(X_train, y_train)  # fit the training features & training labels
''' nb fit is synonymous with train, score is synonymous with test '''

''' purpose of saving a classifier is to avoid doing the training step '''
with open('linearregression.pickle', 'wb') as f:
    pickle.dump(clf, f)  # saves the trained classifier in f

pickle_in = open('linearregression.pickle', 'rb')
clf = pickle.load(pickle_in)  # effectively redefined the classifier here
''' Pickling is a mini-language that can be used to convert the relevant
state from a python object into a string, where this string uniquely
represents the object. Then (un)pickling can be used to convert the
string to a live object, by "reconstructing" the object from the saved
state represented in the string. Note also that there are different
variants of the pickling language. The default is protocol 0, which is
more human-readable. There's also protocol 2, shown below (and 1,3, and
4, depending on the version of python you are using). '''

accuracy = clf.score(X_test, y_test)

forecast_set = clf.predict(X_lately)
print(forecast_set, accuracy, forecast_out)
df['Forecast'] = np.nan  # this col is full of not a number data

last_date = df.iloc[-1].name  # -1 is the end position, the last date
''' iloc is purely integer-location based indexing for selection by
position '''
last_unix = last_date.timestamp()
one_day = 86400
next_unix = last_unix + one_day

''' iterate through the forecast_set.Take each forecast & day,
    setting the values in the dataframe, making those future "features"
    NaNs'''
for i in forecast_set:
    next_date = datetime.datetime.fromtimestamp(next_unix)
    next_unix += one_day
    # create a date index
    df.loc[next_date] = [np.nan for _ in range(len(df.columns)-1)] + [i]
    ''' fill all the dataframe columnswithNaN as we don't have info on
    that data as its all in the future - see print(df.tail()) below
    [i] is a column to hold the forecast - we do have that, well we have
    a prediction for it might me'''
print(df.tail())
df['Adj. Close'].plot()  # plots as far as we have it (red)
df['Forecast'].plot()  # then the blue bit which is the forecast
plt.legend(loc=4)
plt.xlabel('Date')
plt.ylabel('Price')
plt.show()
