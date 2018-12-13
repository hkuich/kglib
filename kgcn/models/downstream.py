import tensorflow as tf
import tensorflow.contrib.layers as layers

import kgcn.models.embedding as learners
import kgcn.models.model
import kgcn.preprocess.preprocess as preprocess


# class KGCNLearner:
#     def __init__(self, kgcn: kgcn.models.model2.KGCN, optimizer):
#         """
#         Custom usage of a KGCN instance
#         :param kgcn:
#         :param optimizer:
#         """
#         self._kgcn = kgcn
#         self._optimizer = optimizer
#
#         # General pipeline
#         arrays_dataset, self._placeholders = self._kgcn.build_dataset()
#
#         combined_dataset = tf.data.Dataset.zip((arrays_dataset, labels_dataset))
#
#         self._dataset_initializer, dataset_iterator = self._kgcn.batch_dataset(combined_dataset)
#
#         # TODO This should be called in a loop when using more than one batch
#         batch_arrays, labels = dataset_iterator.get_next()
#
#         encoded_arrays = self._kgcn.encode(batch_arrays)
#
#         self._kgcn_embedding = self._kgcn.embed(encoded_arrays)


class SupervisedKGCNClassifier:

    def __init__(self, kgcn: kgcn.models.model.KGCN, optimizer, num_classes, log_dir, max_training_steps=10000,
                 regularisation_weight=0.0, classification_dropout_keep_prob=0.7, use_bias=True,
                 classification_activation=lambda x: x, classification_regularizer=layers.l2_regularizer(scale=0.1),
                 classification_kernel_initializer=tf.contrib.layers.xavier_initializer()):

        self._log_dir = log_dir
        self._kgcn = kgcn
        self._optimizer = optimizer
        self._num_classes = num_classes
        self._max_training_steps = max_training_steps
        self._regularisation_weight = regularisation_weight
        self._classification_dropout_keep_prob = classification_dropout_keep_prob
        self._use_bias = use_bias
        self._classification_activation = classification_activation
        self._classification_regularizer = classification_regularizer
        self._classification_kernel_initializer = classification_kernel_initializer

        ################################################################################################################
        # KGCN Embeddings
        ################################################################################################################

        self.embeddings, self.labels, self.dataset_initializer, self.array_placeholders, self.labels_placeholder = \
            self._kgcn.embed_with_labels(self._num_classes)

        ################################################################################################################
        # Downstream of embeddings - classification
        ################################################################################################################
        classification_layer = tf.layers.Dense(self._num_classes, activation=self._classification_activation,
                                               use_bias=self._use_bias,
                                               kernel_regularizer=self._classification_regularizer,
                                               kernel_initializer=self._classification_kernel_initializer,
                                               name='classification_dense_layer')

        # tf.summary.histogram('classification/dense/kernel', classification_layer.kernel)  # TODO figure out why this is throwing an error
        # tf.summary.histogram('classification/dense/bias', classification_layer.bias)

        class_scores = classification_layer(self.embeddings)
        tf.summary.histogram('classification/dense/class_scores', class_scores)

        regularised_class_scores = tf.nn.dropout(class_scores, self._classification_dropout_keep_prob,
                                                 name='classification_dropout')

        tf.summary.histogram('evaluate/regularised_class_scores', regularised_class_scores)

        self._class_scores = regularised_class_scores

        labels_winners = tf.argmax(self.labels, -1)
        class_scores_winners = tf.argmax(self.labels, -1)
        self._confusion_matrix = tf.confusion_matrix(labels_winners, class_scores_winners, num_classes=self._num_classes)

        self._loss_op = self.loss(class_scores, self.labels)
        self._train_op = self.optimise(self._loss_op)

        ################################################################################################################
        # Graph initialisation tasks - run after the whole graph has been built
        ################################################################################################################
        self.tf_session = tf.Session()
        # self.summary = tf.summary.merge_all()
        # Add the variable initializer Op.
        init_global = tf.global_variables_initializer()
        init_local = tf.local_variables_initializer()  # Added to initialise tf.metrics.recall
        init_tables = tf.tables_initializer()

        # Instantiate a SummaryWriter to output summaries and the Graph.
        self.summary_writer = tf.summary.FileWriter(self._log_dir, self.tf_session.graph)

        # Run the Op to initialize the variables.
        self.tf_session.run(init_global)
        self.tf_session.run(init_local)
        self.tf_session.run(init_tables)
        self.summary = tf.summary.merge_all()

    def loss(self, logits, labels=None):

        with tf.name_scope('loss') as scope:
            # Get the losses from the various layers
            loss = tf.cast(self._regularisation_weight * tf.losses.get_regularization_loss(), tf.float32)
            tf.summary.scalar('regularisation_loss', loss)

            # classification loss
            raw_loss = tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=labels)
            tf.summary.histogram('loss/raw_loss', raw_loss)
            loss += tf.reduce_mean(raw_loss)

            tf.summary.scalar('loss/final_loss', loss)

        return loss

    def optimise(self, loss):
        grads_and_vars = self._optimizer.compute_gradients(loss)

        for grad, var in grads_and_vars:
            tf.summary.histogram('gradients/' + var.name, grad)

        opt_op = self._optimizer.apply_gradients(grads_and_vars), loss

        return opt_op

    # def train(self, session, concepts, labels):
    #
    #     feed_dict = self.get_feed_dict(session, concepts, labels=labels)
    #     self.train_from_feed_dict(feed_dict)

    # def train_from_feed_dict(self, feed_dict):
    def train(self, feed_dict):
        print("\n\n========= Training =========")
        _ = self.tf_session.run(self.dataset_initializer, feed_dict=feed_dict)
        for step in range(self._max_training_steps):
            if step % int(self._max_training_steps / 20) == 0:
                _, loss_value, confusion_matrix = self.tf_session.run([self._train_op, self._loss_op,
                                                                       self._confusion_matrix])
                summary_str = self.tf_session.run(self.summary, feed_dict=feed_dict)
                self.summary_writer.add_summary(summary_str, step)
                self.summary_writer.flush()
                print(f'\n-----')
                print(f'Step {step}')
                print(f'Loss: {loss_value:.2f}')
                print(f'Confusion Matrix:')
                print(confusion_matrix)
            else:
                _, loss_value = self.tf_session.run([self._train_op, self._loss_op])
        print("\n\n========= Training Complete =========")

    def eval(self, feed_dict):
        print("\n\n========= Evaluation =========")
        _ = self.tf_session.run(self.dataset_initializer, feed_dict=feed_dict)
        loss_value, confusion_matrix = self.tf_session.run([self._loss_op, self._confusion_matrix])
        print(f'Loss: {loss_value:.2f}')
        print(f'Confusion Matrix:')
        print(confusion_matrix)
        print("\n\n========= Evaluation Complete =========")

    def predict(self, session, concepts):
        pass

    def get_feed_dict(self, session, concepts, labels=None):

        # Possibly save/load raw arrays here instead
        raw_arrays = self._kgcn.input_fn(session, concepts)

        feed_dict = preprocess.build_feed_dict(self.array_placeholders, raw_arrays,
                                               labels_placeholder=self.labels_placeholder, labels=labels)
        return feed_dict