from collections import deque
import pandas as pd
import numpy as np


class Ichimoku:

    def __init__(self, df):
        # if df has an index, we don't want it.
        # Because loc is the best way to select individual elements in the 2D
        # array, since iloc won't let you select the column.
        self.df = df.reset_index()
        self.n = {
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
            "basevolume": "basevolume"
        }
        self.tenkan_highs = deque(maxlen=9)
        self.tenkan_lows = deque(maxlen=9)

        self.kijun_highs = deque(maxlen=26)
        self.kijun_lows = deque(maxlen=26)

        self.chikou_span = deque(maxlen=26)

        self.senkou_b_highs = deque(maxlen=52)
        self.senkou_b_lows = deque(maxlen=52)

        self.df['tenkan_sen'] = pd.Series(np.nan)
        self.df['kijun_sen'] = pd.Series(np.nan)
        self.df['chikou_span'] = pd.Series(np.nan)
        self.df['senkou_a'] = pd.Series(np.nan)
        self.df['senkou_b'] = pd.Series(np.nan)

    @staticmethod
    def avg(highs, lows):
        # Returns the average only if both deques are full
        if len(highs) == highs.maxlen and len(lows) == lows.maxlen:
            return ((max(highs) + min(lows)) / 2)
        return None

    def update_df(self, i, tenkan, kijun, chikou, senkou_a, senkou_b):
        if i - 26 >= 0:
            self.df.loc[i - 26, 'chikou_span'] = chikou

        self.df.loc[i, ['tenkan_sen', 'kijun_sen']] = (tenkan, kijun)
        self.df.loc[i + 26, ['senkou_a', 'senkou_b']] = (senkou_a, senkou_b)

    def run(self):
        for i, row in self.df.iterrows():
            hi = self.df.loc[i, self.n["high"]]
            lo = self.df.loc[i, self.n["low"]]

            self.tenkan_highs.append(hi)
            self.tenkan_lows.append(lo)

            self.kijun_highs.append(hi)
            self.kijun_lows.append(lo)
            tenkan = self.avg(self.tenkan_highs, self.tenkan_lows)
            kijun = self.avg(self.kijun_highs, self.kijun_lows)

            if tenkan and kijun:
                senkou_a = (tenkan + kijun) / 2
            else:
                senkou_a = None

            self.senkou_b_highs.append(hi)
            self.senkou_b_lows.append(lo)

            senkou_b = self.avg(self.senkou_b_highs, self.senkou_b_lows)

            chikou = self.df.loc[i, self.n["close"]]

            self.update_df(i, tenkan, kijun, chikou, senkou_a, senkou_b)

    def analyze(self):
        """
        Checks if there is nothing above chikou_span.
        Then checks if tenkan > kijun > senkou a > senkou b
        For more fine-grained recommendations, might need Tristate class with notes.
        """
        def last(line):
            last_i = self.df[line].last_valid_index()
            last_value = self.df.loc[last_i, line]
            return last_i, last_value

        last_i_chikou, chikou_span = last('chikou_span')
        chikou_all_clear = (chikou_span > self.df.loc[last_i_chikou, 'tenkan_sen']) and \
            (chikou_span > self.df.loc[last_i_chikou, 'kijun_sen']) and \
            (chikou_span > self.df.loc[last_i_chikou, 'senkou_a']) and \
            (chikou_span > self.df.loc[last_i_chikou, 'senkou_b'])

        last_i, tenkan_sen = last('tenkan_sen')
        now_all_clear = (tenkan_sen >= self.df.loc[last_i, 'kijun_sen']) and \
            (tenkan_sen > self.df.loc[last_i, 'senkou_a']) and \
            (tenkan_sen > self.df.loc[last_i, 'senkou_b'])
        return chikou_all_clear and now_all_clear