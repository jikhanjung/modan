#!/usr/bin/env python
# -*- coding: utf-8 -*-
from libpy.conf import ModanConf
from libpy.dbi import ModanDBI


class MdModel:
    def __init__(self):
        mdconf = ModanConf()
        self.conf = mdconf.item
        self.sql = mdconf.sql

    def get_dbi(self):
        try:
            return self.dbi
        except:
            self.dbi = ModanDBI()
            return self.dbi

    def get_sql(self, keyword):
        try:
            return self.sql[keyword]
        except:
            mdconf = ModanConf()
            self.sql = mdconf.sql
            return self.sql[keyword]
