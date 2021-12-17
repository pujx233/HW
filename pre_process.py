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

# 需要跑下列哪些操作
FLAGS = {
    # xlsx转换为csv
    'trans2csv': False,
    # 提取所需列
    'cols': False,
    # 提取江苏省地名用于去噪
    'place_names': False,
    # 去除单位的地名前缀，且分词，提取出重点
    'eliminate': False,
    # 分词
    'tokenize': False,
    # 每一列取频率高的几个token，默认不多于3个
    'filter': True,
}

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
place_set_filename = 'dataset/pre/place-set.json'
target_place_name_filename = 'dataset/pre/target-place-names.csv'
name_eliminated_filename = 'dataset/pre/name-eliminated.csv'


def run():
    jieba.load_userdict("dataset/utils/ext.dic")

    if FLAGS['trans2csv']:
        xlsx_to_csv()
        print('[info] xlsx to csv done')

    if FLAGS['cols']:
        select_cols(select_headers)
        print('[info] select columns done')

    if FLAGS['place_names']:
        get_place_names()
        print('[info] get place name done')

    if FLAGS['eliminate']:
        eliminate_place_names()
        print('[info] eliminate place names done')

    tokenized_prefix = 'dataset/pre/tokenized_'
    if FLAGS['tokenize']:
        tokenize(name_eliminated_filename, 'A4', tokenized_prefix + 'A4.csv')
        tokenize(tokenized_prefix + 'A4.csv', 'A2', tokenized_prefix + 'A2.csv')

    if FLAGS['filter']:
        filter(tokenized_prefix + 'A2.csv', 'A4', 3)
        filter('dataset/pre/new-A4.csv', 'A2', 3)


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


def get_ids():
    ids = get_items('dataset/pre/name-eliminated.csv', ['A0'])
    lst = []
    for item in ids:
        lst.append(item['A0'])
    return lst


def write_to_csv(filename, headers, src):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in src:
            writer.writerow(row)


def get_place_names():
    names = []
    with open(place_set_filename, 'r') as f:
        data = json.load(f)
        for item in data:
            if item['code'].startswith('32'):
                names.append(
                    {place_headers[0]: item['name'], place_headers[1]: item['name'][:-1]})
    write_to_csv(target_place_name_filename, place_headers, names)


def eliminate_place_names():
    selected_cols = get_items(selected_cols_filename)
    place_names = get_items(target_place_name_filename)

    shorts = {}
    units = []
    # A6
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
    write_to_csv(name_eliminated_filename, select_headers, selected_cols)


def select_cols(headers):
    target = get_items(raw_filename, headers)
    write_to_csv(selected_cols_filename, select_headers, target)


def xlsx_to_csv():
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


def read_xlsx():
    workbook = xlrd.open_workbook(raw_excel_filename)
    table = workbook.sheet_by_index(0)
    rows = []
    for row_num in range(3, table.nrows - 3):
        row_value = table.row_values(row_num)
        row = [row_value[3], row_value[6]]
        if row_value[0] == 'A2':
            row.append('0')
        else:
            row.append('1')
        rows.append(row)

    idx = 0
    for row in rows:
        unit = row[1]
        new_unit = ''
        for ch in unit:
            if not (u'\u0041' <= ch <= u'\u005a') and not (u'\u0061' <= ch <= u'\u007a') and ch not in ['省', '市', '县', '区', '镇', '乡', '街道', '村']:
                new_unit += ch
        rows[idx][1] = new_unit
        idx += 1

    dic = {}
    labels = []
    for row in rows:
        if row[1] in dic.keys():
            if row[0] not in dic[row[1]]:
                dic[row[1]].append(row[0])
                labels.append(row[2])
        else:
            dic[row[1]] = [row[0]]
            labels.append(row[2])

    with open('dataset/pre/test.data', 'w', encoding='utf-8') as f:
        index = 0
        for key, value in dic.items():
            for item in value:
                f.write(key + '\t' + item + '\t' + labels[index] + '\n')
                index += 1

    return rows


def set_stop_words(filename):
    result = []
    with open(filename, 'r', encoding='utf-8') as f:
        f.readline()
        for line in f:
            result.extend(line.strip().split(','))

    with open('utils/new_stopwords.txt', 'a', encoding='utf-8') as f:
        for item in result:
            f.write(item + '\n')


def summarize_col(filename, col):
    items = get_items(filename, [col])
    dic = {}
    for item in items:
        if item[col] in dic.keys():
            dic[item[col]] += 1
        else:
            dic[item[col]] = 1
    dic = sorted(dic.items(), key=lambda d: d[1], reverse=True)
    with open('dataset/pre/' + col + '.txt', 'w', encoding='utf-8') as f:
        for key, value in dic:
            print('%s: %d' % (key, value))
            f.write(key + '\n')


def tokenize(f, col, dest):
    probs = []
    items = get_items(f)
    index = 0
    for item in items:
        seg_list = seg.lcut(item[col])
        words = []
        for pair in seg_list:
            if (pair.flag == 'n' or pair.flag == 'nz' or pair.flag == 'vn' or pair.flag == 'an' or pair.flag == 'nr' or pair.flag == 'nt') and len(pair.word) > 1:
                words.append(pair.word)
        words = utils.filter_stop(words)
        if len(words) == 0:
            words = [item[col]]
            probs.append((item['A2'], item['A4'], item['A5'], seg_list))
        items[index][col] = ' '.join(words)
        index += 1

    write_to_csv(dest, select_headers, items)

    print('prob:', len(probs))
    for prob in probs:
        print(prob)


def filter(f, head, limit=3):
    items = get_items(f, ['A2', 'A4', 'A5'])
    dic_a4 = {}
    total_words = 0
    for item in items:
        dic_a4[item['A5']] = dic_a4.get(item['A5'], {})
        words = item[head].split(' ')
        for word in words:
            total_words += 1
            dic_a4[item['A5']][word] = dic_a4[item['A5']].get(word, 0) + 1
        dic_a4[item['A5']]['wc'] = dic_a4[item['A5']].get('wc', 0) + len(words)

    for key, value in dic_a4.items():
        dic_a4[key] = dict(
            sorted(value.items(), key=lambda d: d[1], reverse=True))

    index = 0
    for item in items:
        words = item[head].split(' ')
        new_words = []
        wc = 0
        for word in dic_a4[item['A5']].keys():
            if word in words:
                new_words.append(word)
                wc += 1
                if wc >= limit:
                    break
        items[index][head] = ' '.join(new_words)
        index += 1
    write_to_csv('dataset/pre/new-%s.csv' % head, ['A2', 'A4', 'A5'], items)



if __name__ == '__main__':
    directory = 'dataset/pre'
    if not os.path.exists(directory):
        os.makedirs(directory)
    run()
