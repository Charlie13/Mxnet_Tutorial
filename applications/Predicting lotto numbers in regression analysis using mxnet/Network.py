# -*- coding: utf-8 -*-
import mxnet as mx
import numpy as np
import data_preprocessing as dp
import logging
logging.basicConfig(level=logging.INFO)

def LottoNet(epoch,batch_size,save_period):

    '''data processing'''

    #training data,#test_data
    training_data,test_data,normalization_factor = dp.data_preprocessing()
    tr_i, tr_o = zip(*training_data)
    train_iter = mx.io.NDArrayIter(data={'input' : np.asarray(tr_i)}, label={'output':np.asarray(tr_o)}, batch_size=batch_size,shuffle=True)
    test_iter = mx.io.NDArrayIter(data={'input': test_data})

    '''neural network feedforward'''

    input = mx.sym.Variable('input')
    label = mx.sym.Variable('output')

    affine1 = mx.sym.FullyConnected(data=input,name='fc1',num_hidden=200)
    hidden1 = mx.sym.Activation(data=affine1, name='sigmoid1', act_type="relu")

    affine2 = mx.sym.FullyConnected(data=hidden1, name='fc2', num_hidden=200)
    hidden2 = mx.sym.Activation(data=affine2, name='sigmoid2', act_type="relu")

    affine3 = mx.sym.FullyConnected(data=hidden2, name='fc3', num_hidden=200)
    hidden3 = mx.sym.Activation(data=affine3, name='sigmoid3', act_type="relu")

    affine4 = mx.sym.FullyConnected(data=hidden3, name='fc4', num_hidden=200)
    hidden4 = mx.sym.Activation(data=affine4, name='sigmoid4', act_type="relu")

    affine5 = mx.sym.FullyConnected(data=hidden4, name='fc5', num_hidden=200)
    hidden5 = mx.sym.Activation(data=affine5, name='sigmoid5', act_type="relu")

    affine6 = mx.sym.FullyConnected(data=hidden5, name='fc6', num_hidden=100)
    hidden6 = mx.sym.Activation(data=affine6, name='sigmoid6', act_type="relu")

    out_affine = mx.sym.FullyConnected(data=hidden6, name='out_fc', num_hidden=6)

    output = mx.sym.LinearRegressionOutput(data=out_affine, label=label)
    # LogisticRegressionOutput contains a sigmoid function internally. and It should be executed with xxxx_lbl_one_hot data.
    #output = mx.sym.LogisticRegressionOutput(data=out_affine , label=label)

    print output.list_arguments()

    #weights save
    model_name = 'weights/Lotto_Net'
    checkpoint = mx.callback.do_checkpoint(model_name,period=save_period)

    # training mod
    mod = mx.mod.Module(symbol=output, data_names = ["input"], label_names = ["output"] ,context = mx.gpu(0))
    # test mod
    test = mx.mod.Module(symbol=out_affine , data_names=['input'], label_names=None, context=mx.gpu(0))

    # Network information print
    print mod.data_names
    print mod.label_names
    print train_iter.provide_data
    print train_iter.provide_label

    '''if the below code already is declared by mod.fit function, thus we don't have to write it.
    but, when you load the saved weights, you must write the below code.'''
    mod.bind(data_shapes=train_iter.provide_data,label_shapes=train_iter.provide_label)

    #'''
    # When you want to load the saved weights, uncomment the code below.
    symbol, arg_params, aux_params = mx.model.load_checkpoint(model_name, 10000)

    #the below code needs mod.bind, but If arg_params and aux_params is set in mod.fit, you do not need the code below, nor do you need mod.bind.
    mod.set_params(arg_params, aux_params)
    #'''

    mod.fit(train_iter,
            optimizer='adam',
            optimizer_params={'learning_rate': 0.0001},
            initializer=mx.initializer.Xavier(rnd_type='gaussian', factor_type="avg", magnitude=1),
            eval_metric=mx.metric.MSE(),
            num_epoch=epoch,
            # Once the loaded parameters are declared here,You do not need to declare mod.set_params,mod.bind
            arg_params= None,
            aux_params=None,
            epoch_end_callback=checkpoint)

    print mod.data_shapes
    print mod.label_shapes,
    print mod.output_shapes
    print mod.get_params()
    print mod.get_outputs()
    print mod.score(train_iter, ['mse', 'acc'])

    result = mod.predict(train_iter).asnumpy()
    result1 = np.round(result*normalization_factor)
    result2 = np.rint(result*normalization_factor)
    #print result1
    #print result2
    #'''
    #################################TEST####################################
    symbol, arg_params, aux_params = mx.model.load_checkpoint(model_name, 10000)

    test.bind(data_shapes=test_iter.provide_data,for_training=False)

    '''Annotate only when running test data.'''
    test.set_params(arg_params, aux_params)

    result= test.predict(test_iter)
    result1 = mx.nd.round(normalization_factor*result)
    result2 = mx.nd.rint(normalization_factor*result)

    result1 = result1.asnumpy()
    result2 = result2.asnumpy()
    #print result1
    #print result2

    return [result1,result2]

if __name__=="__main__":
    print "NeuralNet_starting in main"
    net = LottoNet(epoch=10000, batch_size=100, save_period=10000)
    print net[0]
    print net[1]
else:
    print "NeuralNet_imported"
