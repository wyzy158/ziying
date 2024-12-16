[24-11-18]:

    1.sorted()函数用法、lambda匿名函数用法:

    (1)
    numbers = [5, 2, 8, 1, 9]
    sorted_numbers = sorted(numbers)
    print(sorted_numbers)  

    (2)
    words = ["apple", "banana", "cherry", "date"]
    sorted_words = sorted(words,reverse=True)
    print(sorted_words)  

    (3)
    points = [(1, 5), (3, 2), (2, 8), (4, 1)]
    sorted_points = sorted(points, key=lambda x: x[1])  # 基于每个元组的第二个元素排序
    print(sorted_points)  

    (4)
    my_dict = {'c': 3, 'a': 1, 'b': 2}
    sorted_keys = sorted(my_dict.keys())
    print(sorted_keys)  

[24-11-15]:

1.enumerate()函数的用法：

    (1)
    fruits = ['apple', 'banana', 'orange']
    for index, fruit in enumerate(fruits):
        print(f"索引 {index}: 水果 {fruit}")

    # 输出结果:
    # 索引 0: 水果 apple
    # 索引 1: 水果 banana
    # 索引 2: 水果 orange

    (2)
    numbers = (10, 20, 30)

    for index, number in enumerate(numbers):
        print(f"索引 {index}: 数字 {number}")

    # 输出结果:
    # 索引 0: 数字 10
    # 索引 1: 数字 20
    # 索引 2: 数字 30

    (3)
    text = "python"
    for index, char in enumerate(text):
        print(f"索引 {index}: 字符 {char}")

    # 输出结果:
    # 索引 0: 字符 p
    # 索引 1: 字符 y
    # 索引 2: 字符 t
    # 索引 3: 字符 h
    # 索引 4: 字符 o
    # 索引 5: 字符 n

    (4)
    colors = ['red', 'green', 'blue']
    for index, color in enumerate(colors, start=5):
        print(f"从 5 开始的索引 {index}: 颜色 {color}")

    # 输出结果:
    # 从 5 开始的索引 5: 颜色 red
    # 从 5 开始的索引 6: 颜色 green
    # 从 5 开始的索引 7: 颜色 blue

2.列表推导式及.join()函数的用法：

    (1)
    value = 'sdfsdf432kj28sdf23'
    num = ''.join([char for char in value if char.isdigit()])

    #[char for char in value if char.isdigit()] 这是一个列表推导式。它遍历 value 字符串中的每个字符 char ，然后通过 isdigit() 方法判断字符是否为数字。如果是数字，就将其包含在生成的新列表中。
    #''.join(...) 方法将上述列表推导式生成的只包含数字字符的列表连接成一个字符串，并将这个字符串赋值给 num 变量。
    #所以，最终 num 变量就存储了从 value 中提取出来的连续的数字部分。
    #第一个char为[]构成新列表中每个字符，第二个char为遍历value值的变量，相当于将遍历value值中符合if条件的变量（第二个char）赋值给新列表(第一个char)

    (2)
    ''.join()函数，将括号中的内容，用''中的字符连接。

3.有序字典的赋值：

    from collections import OrderedDict

    # 方式一：直接创建并赋值
    my_od = OrderedDict([('key1', 'value1'), ('key2', 'value2')])

    # 方式二：先创建空的有序字典，然后通过键逐一赋值
    my_od = OrderedDict()
    my_od['key3'] = 'value3'
    my_od['key4'] = 'value4'

    # 方式三：使用 setdefault 方法，如果键不存在则设置值
    my_od = OrderedDict()
    my_od.setdefault('key5', 'value5')
    my_od.setdefault('key6', 'value6')

