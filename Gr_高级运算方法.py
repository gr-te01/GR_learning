# class S(str):
#     def __add__(self, other):
#         return  len(self) + len(other)
#
# class S1(str):
#     def __add__(self, other):
#         return NotImplemented
#
# class S2(str):
#     def __radd__(self, other):
#         return len(self) + len(other)
#
# if __name__ == '__main__':
#     s1 = S('Gr')
#     s2 = S('grr')
#     s3 = S1('Gr')
#     s4 = S2(123)
#     print(s1 + s2)
#     print('Gr' + s1)
#     print(s3 + s4)



class S1(str):
    def __iadd__(self, other):
        return len(self) + len(other)

if __name__ == '__main__':
    s1 = S1(123)
    s2 = S1(123)
    s1 += s2
    print(type(s1))
    print(type(s2))
