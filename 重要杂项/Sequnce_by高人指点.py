import os
from collections.abc import Callable
from io import TextIOWrapper
from pathlib import Path
from typing import TypeVar


T = TypeVar('T')


class Search:
    def __init__(self) -> None:
        self.default: list[Path] = [Path(r'C:\Users'), Path(r'D:\\')]

    def directly_search_txt(self) -> TextIOWrapper:
        """虽说不知道为何危险但还是写上这个注释吧"""
        path = Path(input("请输入吧: "))
        if not path.exists():
            print('Error: 无效路径')
            raise FileNotFoundError(f'Not found{path}')
        elif path.is_dir():
            print('目录文件如下: ')
            for name in os.listdir(path):
                print(name)

        else:
            print('已经返回文件对象')
            return open(path, 'r+', encoding='utf-8')

    def search_text(self, accssor: Callable[[TextIOWrapper], T]) -> T:
        """这次是安全的"""
        with self.directly_search_txt() as f:
            return accssor(f)


if __name__ == '__main__':
    s = Search()
    s.search_text(lambda _: None)
