# 目标: 全自动文件生成

import os
import sys
from pathlib import Path

class FileFoundError(Exception):
    def __init__(self, file_value):
        print('Traceback', end='')
        print('文件已经存在: ', file_value)


# 文件工厂
class Gr_file:
    def __init__(self):
        self.default_path = 'C:\\Users\\Administrator\\Desktop\\'    # 创建默认路径
        self.user_input_filename = input('文件名: ')
        self.user_input_filepath = input('路径为?: ')
        self.re_search = None

    def search_file(self, filename, search_path_value = 'C:\\Users\\Administrator\\Desktop\\'):
        path = Path(search_path_value)
        result = next(path.glob('*.txt'), False)
        target = path / f'{filename}.txt'
        print(f'搜索完成, 找到了{target}')
        return target if target.exists() else False

    def crearte_file(self, user_path_value = 'C:\\Users\\Administrator\\Desktop\\'):
        try:    # 判断存在吗
            search_user_input_filename = self.search_file(self.user_input_filename)
            search_default_filename = self.search_file(self.default_path)
            search_user_input_filepath = self.search_file(self.user_input_filepath)
            if search_user_input_filename and search_user_input_filepath == False:  # 不存在就创建
                f = open(f'C:\\Users\\Administrator\\Desktop\\{self.user_input_filename}.txt', 'w', encoding='UTF-8')  # 创建并写入文件
                user_write_file = input('您需要输入文件内容(不需要默认填充空白请输入None): ')
                if user_write_file not in 'None':
                    f.write(user_write_file)
                    print('文件已经生成在路径', end='\t',sep='内容已经填充')
                    f.close()


                elif user_write_file in 'None':      # 第一种情况： 用户提供了文件路径（无内容）
                    print('文件已经生成在', {f})
                    print('文件已经生成在路径', {f}, end='\t', sep='内容已经填充')
                    f.close()



            elif search_default_filename == False:   # 第二种情况： 没有提供路径 也没有内容
                f = open(f'C:\\Users\\Administrator\\Desktop\\{self.user_input_filename}.txt', 'w', encoding='UTF-8')  # 创建并写入文件
                user_write_file = input('您需要输入文件内容(不需要默认填充空白请输入None): ')
                if user_write_file in 'None':
                    print('文件已经生成在', {f})
                    f.close()



        except FileNotFoundError:
            print(f'尝试再次搜索: {self.user_input_filename}')
            self.re_search = self.search_file(self.user_input_filename)
            try:
                if self.re_search is True:
                    raise FileFoundError(self.re_search)

            except FileFoundError:
                    re_input = input('是否覆盖?(y/n)')

                    if re_input in 'y':
                        self.crearte_file(self.user_input_filename)

                    else:
                        print('Good bye')

        except FileFoundError:
            re_input = input('是否覆盖?(y/n)')

            if re_input in 'y':
                self.crearte_file(self.user_input_filename)

            else:
                print('Good bye')


if __name__ == '__main__':
    gr = Gr_file()
    gr.search_file('test')
    gr.crearte_file('test02')

