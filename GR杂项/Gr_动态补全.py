class Dog:
    def bark(self):
        return '王'
dog = Dog()
dog.bark()


class Cat:
    pass

Cat.meow = lambda self:'ha!'

cat = Cat
print(cat.meow())


