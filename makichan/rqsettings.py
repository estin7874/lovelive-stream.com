#-*- coding: utf-8 -*-

import os
import yaml


config = yaml.load(open(os.path.dirname(os.path.realpath(__file__)) + '/../config/default.yaml'))

REDIS_HOST = config['redis']['host']
REDIS_PORT = config['redis']['port']

QUEUES = ['high', 'normal', 'low']
