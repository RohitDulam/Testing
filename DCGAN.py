import tensorflow as tf
import numpy as np
from tensorflow.examples.tutorials.mnist import input_data

mnist = input_data.read_data_sets("MNIST_data/" , one_hot = True)
batch = 64
X_shape = tf.placeholder(tf.float32 , [None , 784])
X = tf.reshape(X_shape , [batch,28,28,1])
Z = tf.placeholder(tf.float32 , [None , 150])


kernel = [3,3,1,32]
kernel2 = [3,3,32,64]
kernel3 = [3,3,64,128]
kernel4 = [4*4*128,1]

stride = [1,2,2,1]

filter1 = tf.Variable(tf.random_normal(kernel , stddev = 0.005))
filter2 = tf.Variable(tf.random_normal(kernel2 , stddev = 0.005))
filter3 = tf.Variable(tf.random_normal(kernel3 , stddev = 0.005))
filter4 = tf.Variable(tf.random_normal(kernel4 , stddev = 0.005))

theta_D = [filter1,filter2,filter3,filter4]


def batch_norm(tnsr):

	 mean , variance = tf.nn.moments(tnsr , axes = [0,1,2])

	 alpha = tf.Variable(tf.constant(0.0 , shape = [tnsr.get_shape().as_list()[-1]]))
	 beta = tf.Variable(tf.constant(1.0 , shape = [tnsr.get_shape().as_list()[-1]]))

	 norm = tf.nn.batch_normalization(tnsr , mean , variance , alpha , beta , 1e-3)
	 #print(norm)

	 return norm


def discriminator(x):

	'''if reuse:
		tf.get_variable_scope().reuse_variables()
	'''
	l1 = tf.nn.relu(batch_norm(tf.nn.conv2d(x , filter1 , strides = stride , padding = 'SAME')))
	#print('l1' + str(l1.get_shape().as_list()))
	l2 = tf.nn.relu(batch_norm(tf.nn.conv2d(l1 , filter2 , strides = stride , padding = 'SAME')))
	#print('l2' + str(l2.get_shape().as_list()))
	l3 = tf.nn.relu(batch_norm(tf.nn.conv2d(l2 , filter3 , strides = stride , padding = 'SAME')))
	#print('l3' + str(l3.get_shape().as_list()))
	l4_shaping = tf.reshape(l3 , [-1 , 4 * 4 * 128])
	#print('l4_shaping' + str(l4_shaping.get_shape().as_list()))
	l4 = tf.nn.relu(tf.matmul(l4_shaping , filter4))
	#print('l4' + str(l4.get_shape().as_list()))
	return tf.nn.sigmoid(l4) , l4


shape = Z.get_shape().as_list()
weight = tf.Variable(tf.random_normal([shape[-1] , 512], stddev = 0.005))
bias = tf.Variable(tf.random_normal([512] , stddev = 0.005))
filter_1 = tf.Variable(tf.random_normal([3,3,16,32] , stddev = 0.005))
filter_2 = tf.Variable(tf.random_normal([3,3,8,16] , stddev = 0.005))
filter_3 = tf.Variable(tf.random_normal([3,3,1,8] , stddev = 0.005))

theta_G = [weight , bias , filter_1 , filter_2 , filter_3]

def generator(z):

	l1 = tf.add(tf.matmul(z , weight) , bias)

	l2_shaping = tf.reshape(l1 , [batch , 4 , 4 , 32]) 
	#print('l2_shaping' + str(l2_shaping.get_shape().as_list()))
	l2_deconv = tf.nn.conv2d_transpose(l2_shaping , filter_1 ,output_shape = [batch , 7 , 7 , 16] ,strides = [1 , 2, 2, 1], padding = 'SAME')
	#print('l2_deconv' + str(l2_deconv.get_shape().as_list()))
	l2 = tf.nn.relu(batch_norm(l2_deconv))
	#print('l2' + str(l2.get_shape().as_list()))
	l3_deconv = tf.nn.conv2d_transpose(l2, filter_2 , output_shape = [batch , 14 , 14 , 8] , strides = [1 , 2, 2, 1], padding = 'SAME')
	#print('l3_deconv', str(l3_deconv.get_shape().as_list()))
	l3 = tf.nn.relu(batch_norm(l3_deconv))
	#print('l3' + str(l3.get_shape().as_list()))
	l4 = tf.nn.conv2d_transpose(l3 , filter_3 , output_shape = [batch , 28 , 28 , 1] , strides = [1 , 2, 2, 1], padding = 'SAME')
	#print('l4' , str(l4.get_shape().as_list()))
	return tf.nn.tanh(l4)

G = generator(Z)
D , D_Logits = discriminator(X)
D_fake , D_fake_Logits = discriminator(G)
#print(D_fake_Logits.get_shape().as_list())

D_loss_real = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=D_Logits, labels=tf.ones_like(D_Logits)))
D_loss_fake = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=D_fake_Logits, labels=tf.zeros_like(D_fake_Logits)))
D_loss = D_loss_real + D_loss_fake
G_loss = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=D_fake_Logits, labels=tf.ones_like(D_fake)))

D_compute = tf.train.AdamOptimizer().minimize(D_loss, var_list = theta_D)
G_compute = tf.train.AdamOptimizer().minimize(G_loss, var_list = theta_G)


init = tf.initialize_all_variables()

def sample_Z(m, n):
    return np.random.uniform(-1., 1., size=[m, n])


Z_dim = 150


with tf.Session() as session:
	session.run(init)

	for i in range(100000):

		X_mb , _ = mnist.train.next_batch(batch)

		data1 = {X_shape : X_mb, Z : sample_Z(batch , Z_dim)}
		data2 = {Z : sample_Z(batch , Z_dim)}

		_, D_loss_curr = session.run([D_compute , D_loss], feed_dict = data1)
		_, G_loss_curr = session.run([G_compute , G_loss], feed_dict = data2)