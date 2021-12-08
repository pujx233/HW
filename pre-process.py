import csv
import json

def get_items():
    with open('dataset/raw.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=',', quotechar='"')
    
        with open('dataset/pre.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['A0', 'A2', 'A5']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
            writer.writeheader()
            for row in reader:
                writer.writerow({'A0': row['A0'], 'A2': row['A2'], 'A5': row['A5']})


def get_place_names():
    names = []
    with open('dataset/place-set.json', 'r') as f:
        data = json.load(f)
        for item in data:
            if item['code'].startswith('32'):
                names.append(item['name'])

    with open('dataset/place-names.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['full_name', 'simplified_name']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
        writer.writeheader()
        for name in names:
            writer.writerow({'full_name': name, 'simplified_name': name[:-1]})


def eliminate_place_names():
    pre = []
    with open('dataset/pre.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=',', quotechar='"')
        for row in reader:
            pre.append(row)

    place_names = []
    with open('dataset/place-names.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=',', quotechar='"')
        for row in reader:
            place_names.append(row)

    while True:
        index = 0
        cnt = 0
        for item in pre:
            unit = item['A5']
            for name in place_names:
                if unit.startswith(name['full_name']):
                    unit = unit.replace(name['full_name'], '')
                    cnt += 1
                    break
                elif unit.startswith(name['simplified_name']):
                    unit = unit.replace(name['simplified_name'], '')
                    cnt += 1
                    break
            pre[index]['A5'] = unit
            index += 1
        if cnt == 0:
            break

    with open('dataset/pre-name-eliminated.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['A0', 'A2', 'A5']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
        writer.writeheader()
        for row in pre:
            writer.writerow({'A0': row['A0'], 'A2': row['A2'], 'A5': row['A5']})



# get_items()
# get_place_names()
# eliminate_place_names()
