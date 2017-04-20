# -*- coding: utf-8 -*-
import mxnet as mx
import numpy as np
import data_download as dd
import logging
logging.basicConfig(level=logging.INFO)
import matplotlib.pyplot as plt

'''unsupervised learning -  Autoencoder'''
def to2d(img):
    return img.reshape(img.shape[0],784).astype(np.float32)/255.0

class NoiseIter(mx.io.DataIter):

    def __init__(self, batch_size, ndim):
        self.batch_size = batch_size
        self.ndim = ndim
        self.provide_data = [('noise', (batch_size, ndim))]
        self.provide_label = []

    def iter_next(self):
        return True

    def getdata(self):
        return [mx.random.normal(0, 1.0, shape=(self.batch_size, self.ndim),ctx=mx.gpu(0))]

def Data_Processing(batch_size):

    '''In this Gan tutorial, we don't need the label data.'''
    (train_lbl_one_hot, train_lbl, train_img) = dd.read_data_from_file('train-labels-idx1-ubyte.gz','train-images-idx3-ubyte.gz')
    (test_lbl_one_hot, test_lbl, test_img) = dd.read_data_from_file('t10k-labels-idx1-ubyte.gz','t10k-images-idx3-ubyte.gz')

    '''data loading referenced by Data Loading API '''
    train_iter = mx.io.NDArrayIter(data={'data': to2d(train_img)}, batch_size=batch_size, shuffle=True)  # training data

    return train_iter

def Generator():

    #generator neural networks
    noise = mx.sym.Variable('noise') # The size of noise is 128.
    g_affine1 = mx.sym.FullyConnected(data=noise,name='g_affine1',num_hidden=256)
    generator1 = mx.sym.Activation(data=g_affine1, name='g_sigmoid1', act_type='sigmoid')
    g_affine2 = mx.sym.FullyConnected(data=generator1, name='g_affine2', num_hidden=784)
    g_out= mx.sym.Activation(data=g_affine2, name='g_sigmoid2', act_type='sigmoid')
    return g_out

def Discriminator():

    #discriminator neural networks
    data = mx.sym.Variable('data') # The size of data is 784(28*28)
    d_affine1 = mx.sym.FullyConnected(data=data,name='d_affine1',num_hidden=256)
    discriminator1 = mx.sym.Activation(data=d_affine1,name='d_sigmoid1',act_type='sigmoid')
    d_affine2 = mx.sym.FullyConnected(data=discriminator1,name = 'd_affine2' , num_hidden=1)
    discriminator2 = mx.sym.Activation(data=d_affine2, name='d_sigmoid2', act_type='sigmoid')

    '''expression-1'''
    #out1 = mx.sym.MakeLoss(mx.symbol.log(discriminator2),grad_scale=-1.0,name="loss1")
    #out2 = mx.sym.MakeLoss(mx.symbol.log(1.0-discriminator2),grad_scale=-1.0,name='loss2')

    '''expression-2'''
    out1 = mx.sym.MakeLoss(-mx.symbol.log(discriminator2),name="loss1")
    out2 = mx.sym.MakeLoss(-mx.symbol.log(1.0-discriminator2),name='loss2')

    group=mx.sym.Group([out1,out2])

    return group

def GAN(epoch,noise_size,batch_size,save_period):

    save_weights=True
    save_path="Weights/"
    train_iter= Data_Processing(batch_size)
    noise_iter = NoiseIter(batch_size, noise_size)

    column_size=10
    row_size=2

    '''
    Generative Adversarial Networks

    <structure>
    generator - 128 - 256 - (784 image generate)

    discriminator -  784 - 256 - (1 Identifies whether the image is an actual image or not)

    cost_function - MIN_MAX cost_function
    '''
    '''Network'''

    generator=Generator()
    discriminator=Discriminator()

    '''In the code below, the 'inputs_need_grad' parameter in the 'mod.bind' function is very important.'''

    # =============module G=============
    modG = mx.mod.Module(symbol=generator, data_names=['noise'], label_names=None, context= mx.gpu(0))
    modG.bind(data_shapes=noise_iter.provide_data,label_shapes=None,for_training=True)
    modG.init_params(initializer=mx.init.Normal(0.02))
    modG.init_optimizer(optimizer='adam',optimizer_params={'learning_rate': 0.01})

    # =============module discriminator[0],discriminator[1]=============
    modD_0 = mx.mod.Module(symbol=discriminator[0], data_names=['data'], label_names=None, context= mx.gpu(0))
    modD_0.bind(data_shapes=train_iter.provide_data,label_shapes=None,for_training=True,inputs_need_grad=True)
    modD_0.init_params(initializer=mx.init.Normal(0.02))
    modD_0.init_optimizer(optimizer='adam',optimizer_params={'learning_rate': 0.01})

    modD_1 = mx.mod.Module(symbol=discriminator[1], data_names=['data'], label_names=None, context= mx.gpu(0))
    modD_1.bind(data_shapes=train_iter.provide_data,label_shapes=None,for_training=True,inputs_need_grad=True,shared_module=modD_0)

    # =============generate image=============
    test_mod = mx.mod.Module(symbol=generator, data_names=['noise'], label_names=None, context= mx.gpu(0))


    ####################################training loop############################################

    # =============train===============
    for epoch in xrange(1,epoch+1,1):
        print "epoch : {}".format(epoch)
        train_iter.reset()
        for batch in train_iter:
            ################################updating only parameters related to modD.########################################
            # updating discriminator on real data
            '''MAX : modD_0 : -mx.symbol.log(discriminator2)  real data Discriminator update , bigger and bigger discriminator2'''
            modD_0.forward(batch, is_train=True)
            modD_0.backward()
            modD_0.update()

            # update discriminator on noise data
            '''MAX : modD_1 :-mx.symbol.log(1-discriminator2)  - noise data Discriminator update , bigger and bigger -> smaller and smaller discriminator2'''
            noise = noise_iter.next()
            modG.forward(noise, is_train=True)
            modG_output = modG.get_outputs()

            modD_1.forward(mx.io.DataBatch(modG_output,None), is_train=True)
            modD_1.backward()
            modD_1.update()

            ################################updating only parameters related to modG.########################################
            # update generator on noise data
            '''MIN : modD_0 : -mx.symbol.log(discriminator2) - noise data Discriminator update  , bigger and bigger discriminator2'''
            modD_0.forward(mx.io.DataBatch(modG_output,None), is_train=True)
            modD_0.backward()
            diff_v= modD_0.get_input_grads()
            modG.backward(diff_v)
            modG.update()


        #Save the data
        if save_weights and epoch%save_period==0:
            print('Saving weights')
            modG.save_params(save_path+"modG-{}.params" .format(epoch))
            modD_0.save_params(save_path+"modD_0-{}.params"  .format(epoch))

    #################################Generating Image####################################
    arg_params, aux_params=modG.get_params()
    ''' At first I thought I would not have to write SHARED_MODULE = MODG and write the sentence below and the above sentence.
     However, after learning SHARED_MODULE = MODG, I found that it took time to process result.asnumpy (). I do not know why....'''

    test_mod.bind(data_shapes=[mx.io.DataDesc(name='noise', shape=(column_size*row_size,noise_size))],label_shapes=None, for_training=False,grad_req='null')
    test_mod.set_params(arg_params=arg_params, aux_params=aux_params)

    '''test_method-1'''
    '''
    noise = noise_iter.next()
    test_mod.forward(noise, is_train=False)
    result = test_mod.get_outputs()[0]
    result = result.asnumpy()
    print np.shape(result)
    '''

    '''test_method-2'''
    #'''
    test_mod.forward(data_batch=mx.io.DataBatch(data=[mx.random.normal(0, 1.0, shape=(column_size*row_size, noise_size))],label=None))
    result = test_mod.get_outputs()[0]
    print result
    #result = result.asnumpy()
    #print result

    #'''
    '''
    #visualization
    fig ,  ax = plt.subplots(int(row_size/2.0), column_size, figsize=(column_size, int(row_size/2.0)))
    #fig ,  ax = plt.subplots(row_size, column_size, figsize=(column_size, row_size))

    for i in xrange(column_size):
        #show 10 image

        ax[i].set_axis_off()
        ax[i].imshow(np.reshape(result[i],(28,28)))

        #show 20 image
        #ax[0][i].set_axis_off()
        #ax[1][i].set_axis_off()
        #ax[0][i].imshow(np.reshape(result[i], (28, 28)))
        #ax[1][i].imshow(np.reshape(result[i+10], (28, 28)))
    plt.show()
    '''
if __name__ == "__main__":

    print "NeuralNet_starting in main"
    GAN(epoch=2, noise_size=100, batch_size=100, save_period=100)

else:

    print "NeuralNet_imported"
