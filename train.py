import sys

sys.path.insert(0, '/home/eecs568/miniconda3/envs/tensorflow/lib/python3.5/site-packages')
import preprocess            
import numpy as np
import random
import tensorflow as tf
from tqdm import tqdm
import cv2
import vgg
#import data
import pdb

class trainer():
    
    def __init__(self,path_to_weight, path_to_data):

        self.image_inputs = tf.placeholder(tf.float32, [None, 224, 224, 3])
        self.label_inputs = tf.placeholder(tf.float32, [None, 7])
        self.sess = tf.Session()
        self.network = vgg.VGG16({'data': self.image_inputs})
        self.load_weight(path_to_weight)
        self.init_data_handler(path_to_data)
        self.regen_regression_network()
        self.build_loss()

        self.saver = tf.train.Saver()


        self.merged_summary = tf.summary.merge_all()
        self.train_writer = tf.summary.FileWriter('./summary/train', self.sess.graph)
        self.test_writer = tf.summary.FileWriter( './summary/test') 
        


    def init_data_handler(self,path_to_data):
        self.data_handler = preprocess.preprocess(path_to_data)

    def load_weight(self,path_to_weight):
        self.network.load(path_to_weight, self.sess)
        #self.saver.restore(self.sess, path_to_weight)
        print("Model Restored")

    def regen_regression_network(self):
        graph = tf.get_default_graph()
        fc_out = graph.get_tensor_by_name("fc7/fc7:0")

        with tf.variable_scope("fc8", reuse=tf.AUTO_REUSE) as scope:
            input_shape = fc_out.get_shape()

            feed_in, dim = (fc_out, input_shape[-1].value)
            weights = tf.get_variable('weights', [dim, 7])
            biases =  tf.get_variable('biases', [7])
            self.init_op = tf.variables_initializer([weights, biases])
            op = tf.nn.xw_plus_b
            fc8 = op(feed_in, weights, biases, name=scope.name)
        self.regression_out = fc8
        tf.summary.histogram('activations',fc8)
    
    def build_loss(self):
        self.loss = tf.nn.l2_loss(self.regression_out - self.label_inputs)
        self.variable_summaries(self.loss)
        self.train_op = tf.train.AdamOptimizer(learning_rate=0.001).minimize(self.loss)

    # TODO: for each layer's weight && bias, add summaries
    def variable_summaries(self, var):
        """Attach a lot of summaries to a Tensor (for TensorBoard visualization)."""
        with tf.name_scope('summaries'):
            mean = tf.reduce_mean(var)
            tf.summary.scalar('mean', mean)
        with tf.name_scope('stddev'):
            stddev = tf.sqrt(tf.reduce_mean(tf.square(var - mean)))
            tf.summary.scalar('stddev', stddev)
        tf.summary.scalar('max', tf.reduce_max(var))
        tf.summary.scalar('min', tf.reduce_min(var))
        tf.summary.histogram('histogram', var)

    def train(self, batch_size, epochs):

        # initialise the variables
        self.sess.run(self.init_op)
        total_loss = 0
        total_batch = int(self.data_handler.numSamples() / batch_size)
        print("[trainer] Start Training")
        for epoch in range(epochs):
            avg_cost = 0
            for i in range(total_batch):
                one_batch_image , one_batch_label = self.data_handler.fetch(batch_size)
                loss, _ = self.sess.run([self.loss, self.train_op], 
                                feed_dict={self.image_inputs: one_batch_image, self.label_inputs: one_batch_label })
                print("[trainer] Train one batch: "+str(loss))
            avg_loss = (total_loss + loss)/total_batch
            self.saver.save(self.sess, "./model_epoch_"+str(epoch)+".ckpt")
            print("[trainer] Epoch ", (epoch ), " ends, avg loss =", "{:.3f}".format(avg_lost))


if __name__ == "__main__":
    argv = sys.argv
    if len(sys.argv) < 3:
        argv = ['', '', '']
        argv[1] = './vgg.data'
        argv[2] = './ShopFacade/'
    train_thread = trainer(argv[1], argv[2])
    pdb.set_trace()
    train_thread.train(64, 10)
