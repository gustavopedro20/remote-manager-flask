LOCAL_FILE_NAME = 'local_path.txt'
LOCAL_FILE_PATH = f'./{LOCAL_FILE_NAME}'
REMOTE_FILE_NAME = 'remote_path.txt'


def convert_txt_vmstat_to_dict(path):
    f = open(path, 'r')
    line = list(f)[2]
    f.close()
    s = line.split(' ')
    t = [x.strip() for x in s]
    j = [x for x in t if x != '']
    k = ','.join(j).replace(',', ';')
    print('CSV: ', k)
    print('Data:', j)
    if len(j) == 17:
        json = {
            'process': {
                'r': j[0],
                'b': j[1]
            },
            'memory': {
                'swpd': j[2],
                'free': j[3],
                'buff': j[4],
                'cache': j[5]
            },
            'swap': {
                'si': j[6],
                'so': j[7]
            },
            'e/s': {
                'bi': j[8],
                'bo': j[9]
            },
            'system': {
                'in': j[10],
                'cs': j[11]
            },
            'cpu': {
                'us': j[12],
                'sy': j[13],
                'id': j[14],
                'wa': j[15],
                'st': j[16]
            }
        }
        print('Json: ', json)
        return json
    return {}
