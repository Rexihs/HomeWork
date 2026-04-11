class LinearInterpolator:
    """
    Линейный интерполятор.
    
    Параметры
    ----------
    x : list
        Узловые точки (отсортированы по возрастанию).
    y : list
        Значения функции в узловых точках.
    """

    def __init__(self, x, y):

        if len(x) == len(y):
            self.x = x
            self.y = y

        else:
            print(f'Attention - количество x,y не совпадает, x,y:{len(x),len(y)}')
            self.x = None
            self.y = None

    def predict(self, xp):
        """
        Вычисление интерполированного значения y_xp для заданного xp.

        Параметры
        ----------
        xp : float
            Точка, в которой нужно найти значение.

        Возвращает
        ----------
        float
            Интерполированное значение y_xp.
        """

        # if not(np.isscalar(xp)): # проверка на иттерабильность
        #     xp = np.asarray(xp)
        #     return np.array([self.predict(i) for i in xp])

        if not isinstance(xp, (int, float)):
            return [self.predict(i) for i in xp]

        if xp < min(self.x) or xp > max(self.x):
            print(f'Attention - xp({xp}) лежит за пределами диапазона x:{max(self.x),min(self.x)},\n'
                  f'Будет произведена экстрополяция')

            if xp < min(self.x):
                x1, y1 = self.x[0], self.y[0]
                x2, y2 = self.x[1], self.y[1]

            if xp > max(self.x):
                x1, y1 = self.x.iloc[-2], self.y.iloc[-2]
                x2, y2 = self.x.iloc[-1], self.y.iloc[-1]

            return y1 + (xp - x1) * (y2 - y1) / (x2 - x1)

        # --- Бинарный поиск O(log n)
        left = 0
        right = len(self.x) - 1

        while right - left > 1:
            mid = (left + right) // 2

            if self.x[mid] == xp:
                return self.y[mid]

            elif self.x[mid] < xp:
                left = mid
            else:
                right = mid

        x1 = self.x[left]
        x2 = self.x[right]
        y1 = self.y[left]
        y2 = self.y[right]

        return y1 + (xp - x1) * (y2 - y1) / (x2 - x1)