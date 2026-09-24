class C:
    def __init__(self, x):
        self.__x = x
    def set_x(self, x):
        self.__x = x
    def get(self):
        print(self.__x)

class D:
    def __func(self):
        print('hello world!')


if __name__ == '__main__':
    c = C(250)
    c.set_x(520)
    c.get()
    print(c.__dict__)
    c.__y = 250
    print(c.__dict__)
if __name__ == '__main__':
    class Py:
        def __init__(self):
            print('oh god i DO')
    cy_t = Py()
     print(cy_t)