# -*- coding: utf-8 -*-
"""NAS_AK_Dissertacao

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1_IwABk2iYWFCeuscXwzZIQKQLqsxAzMc
"""

# Commented out IPython magic to ensure Python compatibility.
import os 
import sys
from google.colab import drive
drive.mount('/content/drive')
#!mkdir "/content/drive/My Drive/NAS_Dissertacao/NAS_Vinicius"
# %cd "/content/drive/My Drive/NAS_Dissertacao/NAS_Vinicius"
!pwd
!ls

import pandas as pd
import tensorflow as tf
!pip3 install autokeras
import autokeras as ak
import os
import numpy as np
import pandas as pd
import random
import matplotlib.pyplot as plt
plt.style.use('ggplot')
#plt.style.use('dark_background')
plt.rcParams["figure.figsize"] = (10, 8)
plt.rcParams["hist.bins"] = 50
from keras import optimizers
import tensorflow
from keras.optimizers import adam_v2, nadam_v2
from keras.layers import Dense, LSTM, Flatten, Activation, Conv1D, MaxPooling1D
from keras.models import Model, Sequential
from keras.metrics import RootMeanSquaredError
from keras.engine.input_layer import Input
#from keras.preprocessing.sequence import pad_sequences
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
import warnings
warnings.filterwarnings("ignore")
import datetime

def series_to_supervised(df, n_out=1, dropnan=True):
    '''
    Do algoritmo de experimento de seleção de caracterisitcas.py
    :param n_in: Número de observaçoes defasadas(lag) do input
    :param n_out: Número de observaçoes defasadas(lag) do output
    :param dropnan:
    :return: Dataframe adequado para supervised learning
    '''
    df_sup = df
    for col in df_sup.columns:
        for j in range(0, n_out):
            col_name_2 = str(col+f'_(t-{j})')
            df_sup[col_name_2] = df_sup[col].shift(-j)
        df_sup = df_sup.drop(col, axis=1)
    if dropnan:
        df_sup = df_sup.dropna() # data cleaning
    return df_sup

#random.seed(42)
# Base de Dados Crua
#df = pd.read_excel('dados_artigo_2 - cópia.xlsx', index_col=0).dropna()
df = pd.read_excel('dados_artigo_2019.xlsx', index_col=0)
df = df.fillna(df.median())

#print(df.head())

# Base de Dados adaptada para um problema de aprendizado supervisionado
df_sup = series_to_supervised(df, 6) # 6 Periodos de 4h = 24h
#print(df_sup)

# Características selecionadas no artigo para dados de entrada
feat_selected = ['CEG_(t-1)', 'Prod_PQ_(t-0)', 'Cfix_(t-0)',
                  'pos_dp_03_(t-0)', 'Temp_02_(t-0)', 'Temp_05_(t-0)',
                  'Pres_01_(t-0)', 'Pres_04_(t-0)', 'rpm_03_(t-0)',
                  'Alt_Cam_(t-5)', 'Pres_01_(t-5)','rpm_06_(t-5)']
#X = df_sup[feat_selected]
X = df_sup.drop('CEG_(t-0)', axis=1)
y = df_sup['CEG_(t-0)']
# print(X.head())
# print(y.head())
# pca = PCA(0.98)
# scaler = StandardScaler()
# X_reduced = pca.fit_transform(X)
# X_scaled_reduced = scaler.fit_transform(X_reduced)
# X_normalizado_reduzido = pd.DataFrame(X_scaled_reduced)
# Base de treino e teste
# X_train, X_test, \
# y_train, y_test = train_test_split(X_normalizado_reduzido,
#                                               y,
#                                             random_state=42)
X_train, X_test, \
y_train, y_test = train_test_split(X, y, random_state=42)

# https://livebook.manning.com/book/automated-machine-learning-in-action/chapter-5/48
from keras_tuner.engine import hyperparameters as hp
# MLP
my_callbacks = [
    tf.keras.callbacks.EarlyStopping(patience=2),
    tf.keras.callbacks.TerminateOnNaN()
]
from sklearn.metrics import mean_squared_error
def ts_auto_model_regressor():
# Initialize the structured data regressor.
  input_node = ak.StructuredDataInput()
  output_node = ak.Normalization()(input_node)
  output_node = ak.DenseBlock(num_layers=hp.Choice('num_layers', [10, 100]),
                              num_units=hp.Choice('num_units', [12, 32]),
                              use_batchnorm=False)(output_node)
  # output_node = ak.DenseBlock(num_layers=1,
  #                             num_units=hp.Choice('num_units', [16, 32, 64]),
  #                             use_batchnorm=False)(output_node)                            
  output_node = ak.RegressionHead()(output_node)
  reg = ak.AutoModel(inputs=input_node, 
                     outputs=output_node, 
                     max_trials=5, 
                     overwrite=True,
                     seed=42) #42
  reg.fit(X_train, y_train, epochs=200, callbacks=my_callbacks)
  model = reg.export_model()
  predicted_y = reg.predict(X_test)
  #mse = reg.evaluate(X_test, y_test)[0]  
  mse = mean_squared_error(y_test, predicted_y)
  rmse = mse**0.5
  return rmse, model

start = datetime.datetime.now()
list_rmse = []
list_model = []
for _ in range(1):
  rmse, model = ts_auto_model_regressor()
  list_rmse.append(rmse)
  list_model.append(model)
df_results_sdr = pd.DataFrame(list_rmse, columns=['RMSE'])
df_results_sdr['Modelo'] = list_model
end = datetime.datetime.now()
print(f'Duração: {end - start}')

df_results_sdr.sort_values(by='RMSE')

dot_img_file = '/tmp/melhor_modelo_MLP.png'
arquitetura_melhor_modelo = df_results_sdr.Modelo[0]
arquitetura_melhor_modelo
tf.keras.utils.plot_model(model, to_file=dot_img_file)

melhor_modelo = df_results_sdr.Modelo[0]
inicio_predicao = datetime.datetime.now()
predicao_nas = pd.DataFrame(melhor_modelo.predict(X))
fim_predicao = datetime.datetime.now()
print(f"Duracao da Previsao MLP: {fim_predicao - inicio_predicao}")
erro = []
df_results = pd.DataFrame(y.values, columns=['real'])
df_results['predicted'] = predicao_nas
#df_results.to_excel('df_results_NAS_AK_MLP.xlsx')
#df_results.to_excel('df_results_NAS_AK_MLP_2019.xlsx')
for i in range(len(predicao_nas)):
    tmp = predicao_nas.values[i] - y.values[i]
    erro.append(tmp[0])
fig, axs = plt.subplots(1, 2, tight_layout=True)
axs[1].hist(erro, bins=50, facecolor='red')
axs[1].set_title('Histograma de Resíduos - NAS-AK/MLP')
axs[0].scatter(y.values, predicao_nas)
#axs[0].set_ylim([5, 10])
axs[0].set_title('Real x Predito - NAS-AK/MLP')
plt.show()

X_train_conv1d = X_train.values.reshape((X_train.shape[0],
                                         X_train.shape[1], 
                                         1))
X_test_conv1d = X_test.values.reshape((X_test.shape[0],
                                         X_test.shape[1], 
                                         1))
def ts_auto_model_regressor_conv():
# Initialize the structured data regressor.
  input_node = ak.Input()
  output_node = ak.Normalization()(input_node)
  output_node = ak.ConvBlock(num_blocks=hp.Choice('num_blocks', [1, 10]),
                             num_layers=hp.Choice('num_layers', [1, 20]),
                             #filters=hp.Choice('filters', [1, 100]),
                             max_pooling=True)(output_node)
  output_node = ak.RegressionHead()(output_node)
  reg = ak.AutoModel(inputs=input_node, 
                     outputs=output_node, 
                     max_trials=5, 
                     overwrite=True,
                     seed=42) 
  reg.fit(X_train_conv1d, y_train, epochs=200, callbacks=my_callbacks)
  model = reg.export_model()
  predicted_y = reg.predict(X_test_conv1d)
  mse = reg.evaluate(X_test_conv1d, y_test)[0]
  rmse = mse**0.5
  return rmse, model

start = datetime.datetime.now()
list_rmse = []
list_model = []
for _ in range(1):
  rmse, model = ts_auto_model_regressor_conv()
  list_rmse.append(rmse)
  list_model.append(model)
df_results_conv = pd.DataFrame(list_rmse, columns=['RMSE'])
df_results_conv['Modelo'] = list_model
end = datetime.datetime.now()
print(f'Duração: {end - start}')

df_results_conv.sort_values(by='RMSE')

dot_img_file = '/tmp/melhor_modelo_CONV.png'
arquitetura_melhor_modelo = df_results_conv.Modelo[0]
arquitetura_melhor_modelo
tf.keras.utils.plot_model(model, to_file=dot_img_file)

inicio_predicao = datetime.datetime.now()
melhor_modelo = df_results_conv.Modelo[0]
predicao_nas = melhor_modelo.predict(X)
fim_predicao = datetime.datetime.now()
print(f"Duracao da Previsao Conv: {fim_predicao - inicio_predicao}")

erro = predicao_nas - y.values
fig, axs = plt.subplots(1, 2, tight_layout=True)
axs[1].hist(erro, bins=50, facecolor='red')
axs[1].set_title('Histograma de Resíduos - NAS/Conv')
axs[0].scatter(y.values, predicao_nas)
#axs[0].set_ylim([5, 10])
axs[0].set_title('Real x Predito - NAS/Conv')
plt.show()

X_train_rnn = X_train.values.reshape(X_train.shape[0] , X_train.shape[1], 1)
X_test_rnn = X_test.values.reshape(X_test.shape[0] , X_test.shape[1], 1)
X_rnn = X.values.reshape(X.shape[0] , X.shape[1], 1)
y_train_rnn = y_train.values.reshape(y_train.shape[0] , 1, 1)

def ts_auto_model_regressor_lstm():
# Initialize the structured data regressor.
  input_node = ak.Input()
  #output_node = ak.Normalization()(input_node)
  output_node = ak.RNNBlock(return_sequences=False,
                            num_layers=hp.Choice('num_layers', [1, 20]),
                            layer_type='lstm')(input_node)
  output_node = ak.DenseBlock()(output_node)
  output_node = ak.RegressionHead()(output_node)
  reg = ak.AutoModel(inputs=input_node, 
                     outputs=output_node, 
                     max_trials=5, 
                     overwrite=True,
                     seed=42) 
  reg.fit(X_train_rnn, y_train, epochs=200, callbacks=my_callbacks)
  model = reg.export_model()
  predicted_y = reg.predict(X_test_rnn)
  mse = reg.evaluate(X_test_rnn, y_test)[0]
  rmse = mse**0.5
  return rmse, model

start = datetime.datetime.now()
list_rmse = []
list_model = []
for _ in range(1):
  rmse, model = ts_auto_model_regressor_lstm()
  list_rmse.append(rmse)
  list_model.append(model)
df_results_lstm = pd.DataFrame(list_rmse, columns=['RMSE'])
df_results_lstm['Modelo'] = list_model
end = datetime.datetime.now()
print(f'Duração: {end - start}')

df_results_lstm.sort_values(by='RMSE')

dot_img_file = '/tmp/melhor_modelo_LSTM.png'
arquitetura_melhor_modelo = df_results_lstm.Modelo[0]
arquitetura_melhor_modelo
tf.keras.utils.plot_model(model, to_file=dot_img_file)

melhor_modelo = df_results_lstm.Modelo[0]
inicio_predicao = datetime.datetime.now()
predicao_nas = melhor_modelo.predict(X)
fim_predicao = datetime.datetime.now()
print(f"Duracao da Previsao LSTM: {fim_predicao - inicio_predicao}")

erro = predicao_nas - y.values
fig, axs = plt.subplots(1, 2, tight_layout=True)
axs[1].hist(erro, bins=50, facecolor='red')
axs[1].set_title('Histograma de Resíduos - NAS/LSTM')
axs[0].scatter(y.values, predicao_nas)
#axs[0].set_ylim([5, 10])
axs[0].set_title('Real x Predito - NAS/LSTM')
plt.show()

def ts_auto_model_regressor_rnn():
# Initialize the structured data regressor.
  input_node = ak.Input()
  #output_node = ak.Normalization()(input_node)
  output_node = ak.RNNBlock(return_sequences=True,
                            num_layers=hp.Choice('num_layers', [10, 100]))(input_node)
  output_node = ak.DenseBlock()(output_node)
  output_node = ak.RegressionHead()(output_node)
  reg = ak.AutoModel(inputs=input_node, 
                     outputs=output_node, 
                     max_trials=5, 
                     overwrite=True,
                     seed=42) 
  reg.fit(X_train_rnn, y_train, epochs=200, callbacks=my_callbacks)
  model = reg.export_model()
  predicted_y = reg.predict(X_test_rnn)
  mse = reg.evaluate(X_test_rnn, y_test)[0]
  rmse = mse**0.5
  return rmse, model

start = datetime.datetime.now()
list_rmse = []
list_model = []
for _ in range(1):
  rmse, model = ts_auto_model_regressor_rnn()
  list_rmse.append(rmse)
  list_model.append(model)
df_results_rnn = pd.DataFrame(list_rmse, columns=['RMSE'])
df_results_rnn['Modelo'] = list_model
end = datetime.datetime.now()
print(f'Duração: {end - start}')

df_results_rnn.sort_values(by='RMSE')

dot_img_file = '/tmp/melhor_modelo_RNN.png'
arquitetura_melhor_modelo = df_results_rnn.Modelo[0]
arquitetura_melhor_modelo
tf.keras.utils.plot_model(model, to_file=dot_img_file)

melhor_modelo = df_results_rnn.Modelo[0]
predicao_nas = melhor_modelo.predict(X)
erro = predicao_nas - y.values
fig, axs = plt.subplots(1, 2, tight_layout=True)
axs[1].hist(erro, bins=50, facecolor='red')
axs[1].set_title('Histograma de Resíduos - NAS/RNN')
axs[0].scatter(y.values, predicao_nas)
#axs[0].set_ylim([5, 10])
axs[0].set_title('Real x Predito - NAS/RNN')
plt.show()

