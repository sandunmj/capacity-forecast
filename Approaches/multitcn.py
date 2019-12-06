# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from tcn import TCN
from keras.models import Input, Model, Sequential
from keras.layers import Dropout, Dense
from sklearn.model_selection import train_test_split

dfn = pd.read_csv('./../Engine/data/280.csv')
df = dfn
dfn.head()

FEED_LEN = 50
PREDICT_LEN = 6

print('processing data...')
col_to_keep = ['AWS/EC2 NetworkIn', 	'AWS/EC2 NetworkOut', 	'System/Linux MemoryUtilization', 'AWS/EC2 CPUUtilization']
df_dropped = dfn[col_to_keep]
df_dropped -= df_dropped.min()
df_dropped /= df_dropped.max()
df_dropped.head()

features = df_dropped.values
feature_set = np.array(features[:FEED_LEN, :])
feature_set = feature_set.reshape(1, feature_set.shape[0], feature_set.shape[1])

for i in range(FEED_LEN+1, features.shape[0]-PREDICT_LEN):
  temp = features[i-FEED_LEN:i,:]
  temp = temp.reshape(1, FEED_LEN, features.shape[1])
  feature_set = np.concatenate((feature_set, temp), axis=0)

cpu_values = df_dropped['AWS/EC2 CPUUtilization'].values
label_set = np.array(cpu_values[FEED_LEN:FEED_LEN+PREDICT_LEN])
label_set = label_set.reshape(1, PREDICT_LEN)

for i in range(FEED_LEN+PREDICT_LEN+1, features.shape[0]):
  temp = cpu_values[i-PREDICT_LEN:i]
  temp = temp.reshape(1, PREDICT_LEN)
  label_set = np.concatenate((label_set, temp), axis=0)

i = Input(batch_shape=(None, None, 4))
o = TCN(return_sequences=False)(i)
o = Dense(PREDICT_LEN)(o)
m = Model(inputs=[i], outputs=[o])
m.compile(optimizer='adam', loss='mae', metrics=['mae', 'mse', 'mape'])
m.summary()

X_train, x_test, Y_train, y_test = train_test_split(feature_set, label_set, train_size=0.8, shuffle=False)
print(X_train.shape)
print(Y_train.shape)
print(x_test.shape)
print(y_test.shape)

historyTCN = m.fit(X_train, Y_train, epochs=10, batch_size=64, validation_data=(x_test, y_test))

m.save('Models/multi_lstm.h5')

plt.plot(historyTCN.history['loss'])
plt.plot(historyTCN.history['val_loss'])
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.savefig('Results/multi_tcn_model_loss.jpg')
plt.show()

plt.plot(historyTCN.history['mean_squared_error'])
plt.plot(historyTCN.history['val_mean_squared_error'])
plt.title('mean_squared_error')
plt.ylabel('mean_squared_error')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.savefig('Results/multi_tcn_mean_squared_error.jpg')
plt.show()


true = x_test[-1].reshape(1, x_test.shape[1], x_test.shape[2])
for i in range(x_test.shape[0]-2, 0, -PREDICT_LEN):
  temp = x_test[i].reshape(1, x_test.shape[1], x_test.shape[2])
  true = np.concatenate((temp, true), axis=0)

pred = m.predict(true).flatten()

_, actual = train_test_split(cpu_values, train_size=0.8, shuffle=False)
nans = np.empty((PREDICT_LEN))
nans[:] = np.nan
actual = np.concatenate((actual, nans), axis=0)

diff = actual.shape[0] - pred.shape[0]
nans = np.empty((diff))
nans[:] = np.nan
pred = np.concatenate((nans, pred), axis=0)

plt.figure(figsize=(18, 14), dpi=80)
plt.plot(actual, color='blue', label='Actual')
plt.plot(pred, color='red', label='Predicted')
plt.legend()
plt.xlim(pred.shape[0] - 500, pred.shape[0])
plt.title('actual vs predicted')
plt.savefig('Results/multi_tcn_actual_vs_predicted.jpg')
plt.show()

def error_calc(act, prd):
  actNans = np.isnan(act)
  act[actNans] = 0
  prdNans = np.isnan(prd)
  prd[prdNans] = 0
  exceedScore = 0
  optimizeScore = 0
  for i in range(0, act.shape[0], PREDICT_LEN):
    actTemp = act[i: PREDICT_LEN+i]
    prdTemp = prd[i:PREDICT_LEN+i]
    optimizeScore += np.sum(np.abs(actTemp - prdTemp))
    if np.max(actTemp) > np.max(prdTemp):
      exceedScore += np.abs(np.max(actTemp) - np.max(prdTemp)) * PREDICT_LEN
  return (exceedScore/act.shape[0], optimizeScore/act.shape[0])

exceedValue, optimScore = error_calc(actual, pred)
print('Exceeding Score:', exceedValue)
print('Optimize score', optimScore)