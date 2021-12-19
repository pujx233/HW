import os
import csv
import json
import xlrd
import math
import datetime
import jieba
import jieba.posseg as seg
from dataset.utils import utils

# 请使用requirements.txt中指定的模块以及版本
xlrd.xlsx.ensure_elementtree_imported(False, None)
xlrd.xlsx.Element_has_iter = True

# 原始数据路径，需指定原始excel文件路径，需放在dataset目录下
raw_excel_filename = 'dataset/pre/raw.xlsx'
raw_filename = 'dataset/pre/raw.csv'

# 需要选定的列
all_headers = ['A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6']
select_headers = ['A0', 'A2', 'A4', 'A5']
place_headers = ['full_name', 'short_name']

# 选择特定列（A2 A3 ...）后的数据集
selected_cols_filename = 'dataset/pre/selected_cols.csv'

# 地名数据，选出江苏省县市地名，用于去除单位的地名前缀
target_place_name_filename = 'dataset/pre/target-place-names.csv'
name_eliminated_filename = 'dataset/pre/name-eliminated.csv'


def run():
    jieba.load_userdict("dataset/utils/ext.dic")

    train_to_csv()
    test_to_csv()
    print('[info] xlsx to csv done')

    select_cols(select_headers)
    print('[info] select columns done')

    eliminate_place_names(selected_cols_filename, name_eliminated_filename, select_headers)
    eliminate_place_names('dataset/pre/raw.1.csv', 'dataset/pre/el.valid.csv', ['A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6'])
    print('[info] eliminate place names done')
    
    generate_train()
    generate_test()
    print('[info] data formatting done')


def generate_train():
    items = get_items('dataset/pre/name-eliminated.csv')
    a2 = {}
    a4 = {}
    for item in items:
        a2[item['A5']] = a2.get(item['A5'], set())
        a2[item['A5']].add((item['A2'], '1'))
        a4[item['A5']] = a4.get(item['A5'], set())
        a4[item['A5']].add((item['A4'], '1'))
    
    for key1 in a2.keys():
        for key2 in a2.keys():
            if key1 == key2:
                continue
            count = 0
            for value in a2[key2]:
                if (value[0], '1') not in a2[key1]:
                    a2[key1].add((value[0], '0'))
                    count += 1
                if count >= 2:
                    break

    for key1 in a4.keys():
        for key2 in a4.keys():
            if key1 == key2:
                continue
            count = 0
            for value in a4[key2]:
                if (value[0], '1') not in a4[key1]:
                    a4[key1].add((value[0], '0'))
                    count += 1

    with open('dataset/pre/zw.train.data', 'w') as f:
        for key, value in a2.items():
            for v in value:
                f.write(key + '\t' + v[0] + '\t' + v[1] + '\n')

    with open('dataset/pre/zw.a4.train.data', 'w') as f:
        for key, value in a4.items():
            for v in value:
                f.write(key + '\t' + v[0] + '\t' + v[1] + '\n')


def generate_test():
    items = get_items('dataset/pre/el.valid.csv')
    a2 = []
    a4 = []
    for item in items:
        is_nom = 1
        is_nom = 0 if item['A0'] == 'A2' else 1
        a2_item = ('%s\t%s\t%d\n' % (item['A5'], item['A2'], is_nom))
        a4_item = ('%s\t%s\t%d\n' % (item['A5'], item['A4'], 1))
        a2.append(a2_item)
        a4.append(a4_item)

    with open('dataset/pre/zw.valid.data', 'w') as f:
        for k in a2:
            f.write(k)

    with open('dataset/pre/zw.test.data', 'w') as f:
        for k in a2:
            f.write(k)

    with open('dataset/pre/zw.a4.valid.data', 'w') as f:
        for k in a2:
            f.write(k)


def get_items(filename, headers=None):
    result = []
    with open(filename, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=',', quotechar='"')
        if headers is None:
            for row in reader:
                result.append(row)
        else:
            for row in reader:
                target = {}
                for header in headers:
                    target[header] = row[header]
                result.append(target)
    return result


def write_to_csv(filename, headers, src):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in src:
            writer.writerow(row)


def eliminate_place_names(src, dest_path, h):
    selected_cols = get_items(src)
    place_names = get_items(target_place_name_filename)

    shorts = {}
    units = []
    with open('dataset/pre/unit-dict.txt', 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#'):
                key, value = line.split(':')
                shorts[key.strip()[1:]] = value.strip()
            else:
                units.append(line.strip())
                break
        for line in f:
            units.append(line.strip())

    while True:
        index = 0
        cnt = 0
        for item in selected_cols:
            unit = item['A5']
            for name in place_names:
                if unit.startswith(name[place_headers[0]]):
                    unit = unit.replace(name[place_headers[0]], '')
                    cnt += 1
                    break
                elif unit.startswith(name[place_headers[1]]):
                    unit = unit.replace(name[place_headers[1]], '')
                    cnt += 1
                    break
            selected_cols[index]['A5'] = unit
            index += 1
        if cnt == 0:
            break

    for unit in units:
        index = 0
        for item in selected_cols:
            u = item['A5']
            if unit in u:
                u = unit
                selected_cols[index]['A5'] = u
            index += 1

    index = 0
    for item in selected_cols:
        u = item['A5']
        if u in shorts.keys():
            u = shorts[u]
            selected_cols[index]['A5'] = u
        index += 1

    index = 0
    for item in selected_cols:
        u = item['A5']
        u = u.replace('局', '')
        u = u.replace('处', '')
        seg_list = seg.lcut(u)
        words = []
        for pair in seg_list:
            if len(pair.word) > 1:
                words.append(pair.word)
        words = utils.filter_stop(words)
        selected_cols[index]['A5'] = ' '.join(words)
        index += 1

    print('[info] total row count:', len(selected_cols))
    write_to_csv(dest_path, h, selected_cols)


def select_cols(headers):
    target = get_items(raw_filename, headers)
    write_to_csv(selected_cols_filename, select_headers, target)


def train_to_csv():
    workbook = xlrd.open_workbook(raw_excel_filename)
    table = workbook.sheet_by_index(1)
    with open(raw_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=all_headers)
        writer.writeheader()
        for row_num in range(1, table.nrows):
            row_value = table.row_values(row_num)
            row_value[0] = int(row_value[0])
            row_value[-1] = datetime.datetime(*xlrd.xldate_as_tuple(
                row_value[-1], workbook.datemode)).strftime("%m/%d/%Y")
            writer.writerow(dict(zip(all_headers, row_value)))


def test_to_csv():
    workbook = xlrd.open_workbook(raw_excel_filename)
    table = workbook.sheet_by_index(0)
    with open('dataset/pre/raw.1.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=all_headers)
        writer.writeheader()
        for row_num in range(3, table.nrows - 3):
            row_value = table.row_values(row_num)
            row_value[1] = row_value[0]
            row_value[-1] = datetime.datetime(*xlrd.xldate_as_tuple(
                row_value[-1], workbook.datemode)).strftime("%m/%d/%Y")
            writer.writerow(dict(zip(all_headers, row_value[1:])))


if __name__ == '__main__':
    directory = 'dataset/pre'
    if not os.path.exists(directory):
        os.makedirs(directory)
    run()
