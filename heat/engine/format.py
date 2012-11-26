# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import re
import yaml
import json


def _construct_yaml_str(self, node):
    # Override the default string handling function
    # to always return unicode objects
    return self.construct_scalar(node)
yaml.Loader.add_constructor(u'tag:yaml.org,2002:str', _construct_yaml_str)
yaml.SafeLoader.add_constructor(u'tag:yaml.org,2002:str', _construct_yaml_str)


def parse_to_template(tmpl_str):
    '''
    Takes a string and returns a dict containing the parsed structure.
    This includes determination of whether the string is using the
    JSON or YAML format.
    '''
    if tmpl_str.startswith('{'):
        return json.loads(tmpl_str)
    try:
        return yaml.load(tmpl_str)
    except yaml.scanner.ScannerError as e:
        raise ValueError(e)


def convert_json_to_yaml(json_str):
    '''Convert a string containing the AWS JSON template format
    to an equivalent string containing the Heat YAML format.'''

    global key_order
    # Replace AWS format version with Heat format version
    json_str = re.sub('"AWSTemplateFormatVersion"\s*:\s*"[^"]+"\s*,',
        '', json_str)

    # insert a sortable order into the key to preserve file ordering
    key_order = 0

    def order_key(matchobj):
        global key_order
        key = '%s"__%05d__order__%s" :' % (
            matchobj.group(1),
            key_order,
            matchobj.group(2))
        key_order = key_order + 1
        return key
    key_re = re.compile('^(\s*)"([^"]+)"\s*:', re.M)
    json_str = key_re.sub(order_key, json_str)

    # parse the string as json to a python structure
    tpl = yaml.load(json_str)

    # dump python structure to yaml
    yml = "HeatTemplateFormatVersion: '2012-12-12'\n" + yaml.safe_dump(tpl)

    # remove ordering from key names
    yml = re.sub('__\d*__order__', '', yml)
    return yml