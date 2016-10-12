# -*- coding: utf-8 -*-
"""
Created on Mon Oct 10 14:37:01 2016

@author: oreilly
"""

import json
def prettyPrintJSON(jsonRepr):
    if isinstance(jsonRepr, list):
        return "[\n" + "\n".join([json.dumps(s, sort_keys=True, indent=4, separators=(',', ': ')) for s in jsonRepr])  + "\n]"
    elif isinstance(jsonRepr, dict):
        return json.dumps(jsonRepr, sort_keys=True,
                          indent=4, separators=(',', ': '))