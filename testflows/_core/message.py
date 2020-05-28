# Copyright 2019 Katteli Inc.
# TestFlows Test Framework (http://testflows.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json

from collections import namedtuple

from .utils.enum import IntEnum

def namedtuple_with_defaults(*args, defaults=()):
    nt = namedtuple(*args)
    nt.__new__.__defaults__ = defaults
    [setattr(nt, f"_{field}", idx) for idx, field in enumerate(nt._fields)]
    return nt

class Message(IntEnum):
    NONE = 0
    #
    TEST = 1
    RESULT = 2
    #
    EXCEPTION = 3
    NOTE = 4
    DEBUG = 5
    TRACE = 6
    #
    VERSION = 7
    PROTOCOL = 8
    #
    INPUT = 9
    #
    VALUE = 10
    METRIC = 11
    TICKET = 12
    ARGUMENT = 13
    TAG = 14
    ATTRIBUTE = 15
    REQUIREMENT = 16
    EXAMPLE = 17
    #
    NODE = 18
    MAP = 19
    #
    STOP = 20

class MessageObjectType(IntEnum):
    NONE = 0
    TEST = 1 << 0

MessageMap = namedtuple(
        "MessageMap",
        "NONE "
        "TEST RESULT "
        "EXCEPTION NOTE DEBUG TRACE "
        "VERSION PROTOCOL "
        "INPUT "
        "VALUE METRIC TICKET ARGUMENT TAG ATTRIBUTE REQUIREMENT "
        "NODE MAP STOP"
    )

def dumps(o):
    return json.dumps(o, separators=(",", ":"))

def loads(s):
    return json.loads(s)
