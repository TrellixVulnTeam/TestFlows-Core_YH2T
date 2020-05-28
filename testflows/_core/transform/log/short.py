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
import textwrap

import testflows.settings as settings

from testflows._core.flags import Flags, SKIP
from testflows._core.testtype import TestType, TestSubType
from testflows._core.message import Message
from testflows._core.objects import ExamplesTable
from testflows._core.name import split, parentname, basename
from testflows._core.cli.colors import color, cursor_up

indent = " " * 2
#: map of tests by name
tests_by_id = {}
#: map of tests by parent
tests_by_parent = {}
#: last message
last_message = [None]

def color_other(other):
    return color(other, "white", attrs=["dim"])

def color_keyword(keyword):
    return color(split(keyword)[-1], "white", attrs=["bold"])

def color_secondary_keyword(keyword):
    return color(split(keyword)[-1], "white", attrs=["bold", "dim"])

def color_test_name(name):
    return color(split(name)[-1], "white", attrs=[])

def color_result(result):
    if result.startswith("X"):
        return color(result, "blue", attrs=["bold"])
    elif result == "OK":
        return color(result, "green", attrs=["bold"])
    elif result == "Skip":
        return color(result, "cyan", attrs=["bold"])
    # Error, Fail, Null
    return color(result, "red", attrs=["bold"])

def format_input(msg, keyword):
    out = f"{indent * (msg['test_id'].count('/'))}"
    out += color("\u270b " + msg["message"], "yellow", attrs=["bold"]) + cursor_up() + "\n"
    return out

def format_multiline(text, indent):
    first, rest = (text.rstrip() + "\n").split("\n", 1)
    first = first.strip()
    if first:
        first += "\n"
    out = f"{first}{textwrap.dedent(rest.rstrip())}".rstrip()
    out = textwrap.indent(out, indent + "  ")
    return out

def format_test_description(msg, indent):
    desc = format_multiline(msg["test_description"], indent)
    desc = color(desc, "white", attrs=["dim"])
    return desc + "\n"

def format_requirements(msg, indent):
    out = [f"{indent}{' ' * 2}{color_secondary_keyword('Requirements')}"]
    for req in msg.requirements:
        out.append(color(f"{indent}{' ' * 4}{req.name}", "white", attrs=["dim"]))
        out.append(color(f"{indent}{' ' * 6}version {req.version}", "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def format_attribute(msg):
    _indent = indent * (msg["test_id"].count('/') - 1)
    if last_message[0] and not last_message[0]["message_keyword"] == Message.ATTRIBUTE.name:
        out = [f"{_indent}{' ' * 2}{color_secondary_keyword('Attributes')}"]
    else:
        out = []
    out.append(color(f"{indent}{' ' * 2}{msg['attribute_name']}", "white", attrs=["dim"]))
    out.append(color(f"{indent}{' ' * 4}{msg['attribute_value']}", "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def format_tags(msg, indent):
    out = [f"{indent}{' ' * 2}{color_secondary_keyword('Tags')}"]
    for tag in msg.tags:
        out.append(color(f"{indent}{' ' * 4}{tag.value}", "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def format_examples(msg, indent):
    examples = ExamplesTable(*msg.examples)
    out = [f"{indent}{' ' * 2}{color_secondary_keyword('Examples')}"]
    out.append(color(textwrap.indent(f"{examples}", prefix=f"{indent}{' ' * 4}"), "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def format_arguments(msg, indent):
    out = [f"{indent}{' ' * 2}{color_secondary_keyword('Arguments')}"]
    for arg in msg.args:
        out.append(color(f"{indent}{' ' * 4}{arg.name}", "white", attrs=["dim"]))
        out.append(color(textwrap.indent(f"{arg.value}", prefix=f"{indent}{' ' * 6}"), "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def get_type(msg):
    return getattr(TestType, msg["test_type"])

def get_subtype(msg):
    return getattr(TestSubType, str(msg["test_subtype"]), 0)

def and_keyword(msg, parent_id, keyword, subtype):
    """Handle processing of Given, When, Then, But, By and Finally
    keywords and convert them to And when necessary.
    """
    prev = tests_by_parent[parent_id][-2] if len(tests_by_parent.get(parent_id, [])) > 1 else None
    if prev and get_subtype(prev) == subtype and tests_by_parent.get(prev["test_id"]) is None:
        keyword = "And"
    parent = tests_by_id.get(parent_id)
    if parent and get_subtype(parent) == subtype and len(tests_by_parent.get(parent_id, [])) == 1:
        keyword = "And"
    return keyword

def format_test(msg, keyword, tests_by_parent, tests_by_id):
    # add test to the tests map
    parent = parentname(msg["test_id"])
    if tests_by_parent.get(parent) is None:
        tests_by_parent[parent] = []
    tests_by_parent[parent].append(msg)
    tests_by_id[msg["test_id"]] = msg

    test_type = get_type(msg)
    test_subtype = get_subtype(msg)

    if test_type == TestType.Module:
        keyword += "Module"
    elif test_type == TestType.Suite:
        if test_subtype == TestSubType.Feature:
            keyword += "Feature"
        else:
            keyword += "Suite"
    elif test_type == TestType.Iteration:
        keyword += "Iteration"
    elif test_type == TestType.Step:
        if test_subtype == TestSubType.And:
            keyword += "And"
        elif test_subtype == TestSubType.Given:
            keyword += and_keyword(msg, parent, "Given", TestSubType.Given)
        elif test_subtype == TestSubType.When:
            keyword += and_keyword(msg, parent, "When", TestSubType.When)
        elif test_subtype == TestSubType.Then:
            keyword += and_keyword(msg, parent, "Then", TestSubType.Then)
        elif test_subtype == TestSubType.By:
            keyword += and_keyword(msg, parent, "By", TestSubType.By)
        elif test_subtype == TestSubType.But:
            keyword += and_keyword(msg, parent, "But", TestSubType.But)
        elif test_subtype == TestSubType.Finally:
            keyword += and_keyword(msg, parent, "Finally", TestSubType.Finally)
        else:
            keyword += "Step"
    else:
        if test_subtype == TestSubType.Scenario:
            keyword += "Scenario"
        elif test_subtype == TestSubType.Background:
            keyword += "Background"
        else:
            keyword += "Test"

    _keyword = color_keyword(keyword)
    _name = color_test_name(split(msg["test_name"])[-1])
    _indent = indent * (msg["test_id"].count('/') - 1)
    out = f"{_indent}{_keyword} {_name}\n"
    if msg["test_description"]:
        out += format_test_description(msg, _indent)
    return out

def format_result(msg):
    result = msg["result_type"]

    _result = color_result(result)
    _test = color_test_name(basename(msg["result_test"]))

    _indent = indent * (msg["test_id"].count('/') - 1)
    out = f"{_indent}{_result}"

    if result in ("Fail", "Error", "Null"):
        out += f" {_test}"
        if msg["result_message"]:
            out += color_test_name(",")
            out += f" {color(format_multiline(msg['result_message'], _indent).lstrip(), 'yellow', attrs=['bold'])}"
    elif result.startswith("X"):
        out += f" {_test}"
        if msg["result_reason"]:
            out += color_test_name(",")
            out += f" {color(msg['result_reason'], 'blue', attrs=['bold'])}"
    return out + "\n"

formatters = {
    Message.INPUT.name: (format_input, f""),
    Message.TEST.name: (format_test, f"", tests_by_parent, tests_by_id),
    Message.RESULT.name: (format_result,),
    Message.ATTRIBUTE.name: (format_attribute,)
}

def transform():
    """Transform parsed log line into a short format.
    """
    line = None
    while True:
        if line is not None:
            msg = line
            formatter = formatters.get(line["message_keyword"], None)
            if formatter:
                flags = Flags(line["test_flags"])
                if flags & SKIP and settings.show_skipped is False:
                    line = None
                else:
                    line = formatter[0](line, *formatter[1:])
                    last_message[0] = msg
            else:
                line = None
        line = yield line