import numpy as np
class Logger():
    """A class for adaptive choices of maximal allowed epsilon.

    It uses an adapted kneedle algorithm. It takes the pair of arrays (x, y), where x
    is the current max epsilon, and y is the current cumulative number of reduced points.
    Since the reducers are however working on multiple threads, one must synchronize the
    resulting updates.
    """
    def __init__(self, poly_size: int, smooth : bool = True, window : int = 10, scale : int = 1, 
                 loss_values : np.ndarray = np.arange(0, 100, 1) * 1e-4, 
                 min_iter : int = 5):
        #the current total possible reduction for each eps
        self.vals : np.ndarray =  poly_size * np.ones(loss_values.shape, dtype = int)
        self.stop_condition = False
        self.max_eps_idx = 0
        self.smooth = smooth
        self.min_iter = min_iter
        #an array of current buckets of eps, progressively increasing
        self.loss_values : np.ndarray = loss_values

        self.smoother_window = window
        self.smoother_scale = scale

    def update(self, new_eps : float):
        if self.stop_condition:
            return
        
        mask = self.loss_values  >= new_eps
        #we exceeded maximum epsilon
        if np.sum(mask) == 0:
            print("mask condition true")
            self.stop_condition = True
        self.vals[mask] = self.vals[mask] - 1

        #update best epsilon
        if np.argmax(mask) > self.max_eps_idx:
            self.max_eps_idx = np.argmax(mask)

        self.check()

    def check(self):
        if self.max_eps_idx < self.min_iter:
            pass
        else:
            x, y = self.transform()
            if y[-1] < y[-2]:
                self.stop_condition = True
            
    def query(self, eps_val : float) -> bool:
        if self.stop_condition and eps_val >= self.loss_values[self.max_eps_idx]:
            return True
        else:
            return False

    def transform(self):
        #to transform the curve into the right shape
        x = self.loss_values[:self.max_eps_idx + 1]
        y = self.vals[:self.max_eps_idx + 1]
        if self.smooth:
            y = np.log(y)

        #invert it
        y = np.max(y) - y

        #and once again by convolving with kernel
        y = self.gauss_smoother(y, self.smoother_window, self.smoother_scale)
        x, y = self.normalize(x, y)
        return x, (y - x)
    
    def normalize(self, x : np.ndarray, y : np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        curve : np.ndarray = np.stack([x, y])
        a_min, a_max = np.min(curve, axis = 1), np.max(curve, axis = 1)
        a_min = a_min.reshape(-1,1)
        a_max = a_max.reshape(-1,1)
        norm_arr = (curve - a_min) / (a_max - a_min)
        return (norm_arr[0, :], norm_arr[1, :])

    @staticmethod
    def gauss_smoother(data : np.ndarray, window : int, scale : float) -> np.ndarray:
        if window % 2 == 0:
            window += 1  # enforce odd window
        if window < 3:
            return data
        pad : int = window // 2
        y_pad = np.pad(data, (pad, pad), mode="edge")
        kern = np.exp(-np.linspace(-2,2,window)**2/scale)
        kern = kern/np.sum(kern)
        return np.convolve(y_pad, kern, mode="valid")
    
