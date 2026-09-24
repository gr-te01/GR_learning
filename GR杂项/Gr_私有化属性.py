# import random
#
# # property  and 装饰器
# class Person(object):
#     def __init__(self,object):
#         self._age = random.randint(0,1)
#         print(self._age)
#
#     @property
#     def age(self):
#         return self._age
#     @age.setter
#     def age(self, parms):
#         if parms <= 0:
#             print('错误: 年龄为0')
#             raise ZeroDivisionError
#
#         else:
#             self._age = parms
#             print('你是', self._age, '岁')
#
#
#
#
#
# # 装饰器
#
#
#
#
#
#
#
#
#
#
#
#
#
#
# if __name__ == '__main__':
#
#     Gr = Person('Gr')
#     Gr.getAge()
#     Gr.age = 20
#     print(Gr.age)
#     del Person
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#     # def getAge(self):
#     #     return self._age
#     #
#     # def setAge(self, age):
#     #     if age <= 0:
#     #         print('错误: 年龄为0')
#     #         raise ZeroDivisionError
#     #
#     #     else:
#     #         self._age = age
#     #         print('你是', self._age, '岁')
#     # age = property(getAge, setAge)
#
#
#
# # def getAge(self):
# #     return self._age
# #
# # def setAge(self, age):
# #      age = property(getAge, setAge)
#
#


import random


class Person(object):
    def __init__(self, object):
        self._age = random.randint(0, 1)
        print(self._age)

    @property
    def age(self):
        return self._age

    @age.setter
    def age(self, parms):
        if parms <= 0:
            print('错误: 年龄为0')
            raise ZeroDivisionError
        else:
            self._age = parms
            print('你是', self._age, '岁')


if __name__ == '__main__':
    Gr = Person('Gr')
    print(Gr.age)  # 用 Gr.age 代替 Gr.getAge()
    Gr.age = random.randint(0, 1)  # 用 Gr.age = x 代替 Gr.setAge(x)
    print(Gr.age)
