# -*- coding: utf-8 -*-
"""LongShort Term Memory Fully Convolutional Network (LSTM-FCN)."""

__author__ = ["jnrusson1", "solen0id"]

from sktime.networks.base import BaseDeepNetwork
from sktime.utils.validation._dependencies import _check_dl_dependencies

_check_dl_dependencies(severity="warning")


class MLSTMFCNNetwork(BaseDeepNetwork):
    """
    Implementation of MLSTMFCNClassifier from Karim et al (2019) [1].

    Overview
    --------
    Combines an LSTM arm with a CNN arm. Optionally uses an attention mechanism in the
    LSTM which the author indicates provides improved performance. Can handle
    multivariate features as input through the use of Squeeze and Excite Blocks.


    References
    ----------
    .. [1] Karim et al. Multivariate LSTM-FCNs for Time Series Classification, 2019
    https://arxiv.org/pdf/1801.04503.pdf
    """

    _tags = {"python_dependencies": "tensorflow"}

    def __init__(
        self,
        random_state=0,
        dropout=0.8,
        attention=False,
        dilation_rate=2,
        filter_sizes=(64, 128, 64),
        kernel_sizes=(5, 3, 1),
        lstm_size=5,
    ):
        """
        Initialize a new LSTMFCNNetwork object.

        Parameters
        ----------
        kernel_sizes: List[int], default=[8, 5, 3]
            specifying the length of the 1D convolution
         windows
        filter_sizes: List[int], default=[128, 256, 128]
            size of filter for each conv layer
        random_state: int, default=0
            seed to any needed random actions
        lstm_size: int, default=8
            output dimension for LSTM layer
        dropout: float, default=0.8
            controls dropout rate of LSTM layer
        attention: boolean, default=False
            If True, uses custom attention LSTM layer
        """
        self.random_state = random_state
        self.kernel_sizes = kernel_sizes
        self.filter_sizes = filter_sizes
        self.lstm_size = lstm_size
        self.dropout = dropout
        self.attention = attention
        self.dilation_rate = dilation_rate

        super(MLSTMFCNNetwork, self).__init__()

    def build_network(self, input_shape, **kwargs):
        """
        Construct a network and return its input and output layers.

        Parameters
        ----------
        input_shape : tuple
            The shape of the data fed into the input layer

        Returns
        -------
        input_layers : keras layers
        output_layer : a keras layer
        """
        from tensorflow import keras

        from sktime.networks.lstmfcn_layers import (
            make_attention_lstm,
            squeeze_excite_block,
        )

        input_layer = keras.layers.Input(shape=input_shape)

        x = keras.layers.Permute((2, 1))(input_layer)

        if self.attention:
            AttentionLSTM = make_attention_lstm()
            x = AttentionLSTM(self.lstm_size)(x)
        else:
            x = keras.layers.LSTM(self.lstm_size)(x)

        x = keras.layers.Dropout(self.dropout)(x)

        y = keras.layers.Conv1D(
            self.filter_sizes[0],
            self.kernel_sizes[0],
            dilation_rate=self.dilation_rate,
            padding="same",
            kernel_initializer="he_uniform",
        )(input_layer)
        y = keras.layers.BatchNormalization()(y)
        y = keras.layers.Activation("relu")(y)
        y = squeeze_excite_block(y)

        y = keras.layers.Conv1D(
            self.filter_sizes[1],
            self.kernel_sizes[1],
            dilation_rate=self.dilation_rate,
            padding="same",
            kernel_initializer="he_uniform",
        )(y)
        y = keras.layers.BatchNormalization()(y)
        y = keras.layers.Activation("relu")(y)
        y = squeeze_excite_block(y)

        y = keras.layers.Conv1D(
            self.filter_sizes[2],
            self.kernel_sizes[2],
            dilation_rate=self.dilation_rate,
            padding="same",
            kernel_initializer="he_uniform",
        )(y)
        y = keras.layers.BatchNormalization()(y)
        y = keras.layers.Activation("relu")(y)

        y = keras.layers.GlobalAveragePooling1D()(y)

        output_layer = keras.layers.concatenate([x, y])

        return input_layer, output_layer
