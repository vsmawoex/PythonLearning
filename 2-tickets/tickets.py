# coding: utf-8

"""命令行火车票查看器

Usage:
    tickets.py [-gdtkz] <from> <to> <date>

Options:
    -h,--help   显示帮助菜单
    -g          高铁
    -d          动车
    -t          特快
    -k          快速
    -z          直达

Example:
    tickets.py 北京 上海 2016-10-10
    tickets.py -dg 成都 南京 2016-10-10
"""
from docopt import docopt
from prettytable import PrettyTable
from stations import stations
import requests
import re
from colorama import init, Fore
requests.packages.urllib3.disable_warnings()


class TrainsCollection:

    header = '车次 车站 时间 历时 商务特等座 一等座 二等座 高级软卧 软卧 硬卧 硬座 无座'.split()

    def __init__(self, available_trains, station_map, options):
        """查询到的火车班次集合

        :param available_trains: 一个列表, 包含着所有车次的信息
        :param station_map: 一个字典，包含不同代号对应的站点
        :param options: 查询的选项, 如高铁, 动车, etc...
        """
        self.available_trains = available_trains
        self.station_map = station_map
        self.options = options

    def geturation(self, duration):
        duration = duration.replace(':', '小时') + '分'
        if duration.startswith('00'):
            return duration[4:]
        if duration.startswith('0'):
            return duration[1:]
        return duration

    @property
    def trains(self):
        for raw_train in self.available_trains:
            # 利用正则表达式得到列车的类型
            train_type = re.findall('[\u4e00-\u9fa5]+\|\w+\|(\w)', raw_train)[0].lower()
            if train_type in self.options and '售' not in raw_train and '停运' not in raw_train:
                station = re.findall('(\w+)\|(\w+)\|\d+:', raw_train)[0]    # 元组，保存始发站和终点站的代号
                s_station = station[0]   # 始发站的代号
                e_station = station[1]   # 终点站的代号
                train = [
                    # 车次
                    re.findall('[\u4e00-\u9fa5]+\|\w+\|(\w+)', raw_train)[0],
                    # 始发站和终点站
                    '\n'.join([Fore.MAGENTA+self.station_map[s_station]+Fore.RESET,
                               Fore.BLUE+self.station_map[e_station]+Fore.RESET]),
                    # 发车时间和到站时间
                    '\n'.join([Fore.MAGENTA+re.findall('\|(\d+:\d+)', raw_train)[0]+Fore.RESET,
                               Fore.BLUE+re.findall('\|(\d+:\d+)', raw_train)[1]+Fore.RESET]),
                    self.geturation(re.findall('\|(\d+:\d+)', raw_train)[-1]),  # 行驶总时间
                    re.findall('(\d){8}\|(\w*\|){18}(\w*)', raw_train)[0][-1],  # 商务特等座
                    re.findall('(\d){8}\|(\w*\|){17}(\w*)', raw_train)[0][-1],  # 一等座
                    re.findall('(\d){8}\|(\w*\|){16}(\w*)', raw_train)[0][-1],  # 二等座
                    re.findall('(\d){8}\|(\w*\|){7}(\w*)', raw_train)[0][-1],   # 高级软卧
                    re.findall('(\d){8}\|(\w*\|){9}(\w*)', raw_train)[0][-1],   # 软卧
                    re.findall('(\d){8}\|(\w*\|){14}(\w*)', raw_train)[0][-1],  # 硬卧
                    re.findall('(\d){8}\|(\w*\|){15}(\w*)', raw_train)[0][-1],  # 硬座
                    re.findall('(\d){8}\|(\w*\|){12}(\w*)', raw_train)[0][-1]   # 无座
                ]
                yield train

    def pretty_print(self):
        pt = PrettyTable()
        pt._set_field_names(self.header)
        for train in self.trains:
            pt.add_row(train)
        print(pt)


def cli():
    """command-line interface"""
    arguments = docopt(__doc__)
    from_station = stations.get(arguments['<from>'])
    to_station = stations.get(arguments['<to>'])
    date = arguments['<date>']
    # 构建 URL
    url = 'https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date={}&leftTicketDTO.from_station=' \
          '{}&leftTicketDTO.to_station={}&purpose_codes=ADULT'.format(date, from_station, to_station)
    options = ''.join([
        key for key, value in arguments.items() if value is True
    ])
    r = requests.get(url, verify=False)
    available_trains = r.json()['data']['result']
    station_map = r.json()['data']['map']
    TrainsCollection(available_trains, station_map, options).pretty_print()


if __name__ == '__main__':
    cli()
