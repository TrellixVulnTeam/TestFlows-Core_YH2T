# Copyright 2020 Katteli Inc.
# TestFlows.com Open-Source Software Testing Framework (http://testflows.com)
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
import re
import base64
import textwrap

from collections import OrderedDict

import testflows._core.cli.arg.type as argtype

from testflows._core.cli.arg.common import epilog
from testflows._core.cli.arg.common import HelpFormatter
from testflows._core.cli.arg.handlers.handler import Handler as HandlerBase
from testflows._core.transform.log.pipeline import ResultsLogPipeline
from testflows._core.cli.arg.handlers.report.copyright import copyright
from testflows._core.testtype import TestType
from testflows._core.name import basename, sep

logo = '<img class="logo" src="data:image/png;base64,%(data)s" alt="logo"/>'
testflows = '<span class="testflows-logo"></span> [<span class="logo-test">Test</span><span class="logo-flows">Flows</span>]'
testflows_em = testflows.replace("[", "").replace("]", "")

template = f"""
<section class="clearfix">%(logo)s%(confidential)s%(copyright)s</section>

---
# %(title)s Test Specification

## Table of Contents

%(table_of_contents)s

## 1. Overview

This test specification contains detailed summary of test procedures for each
executed test including test's unique name, attributes, tags and requirement(s).

%(body)s

---
Generated by {testflows} Open-Source Test Framework

[<span class="logo-test">Test</span><span class="logo-flows">Flows</span>]: https://testflows.com
"""

class Formatter(object):
    def format_logo(self, data):
        if not data["company"].get("logo"):
            return ""
        data = base64.b64encode(data["company"]["logo"]).decode("utf-8")
        return '\n<p>' + logo % {"data": data} + "</p>\n"

    def format_confidential(self, data):
        if not data["company"].get("confidential"):
            return ""
        return f'\n<p class="confidential">Document status - Confidential</p>\n'

    def format_copyright(self, data):
        if not data["company"].get("name"):
            return ""
        return (f'\n<p class="copyright">\n'
            f'{copyright(data["company"]["name"])}\n'
            "</p>\n")

    def format_multiline(self, text, indent=None):
        first, rest = (text.rstrip() + "\n").split("\n", 1)
        first = first.strip()
        if first:
            first += "\n"
        out = f"{first}{textwrap.dedent(rest.rstrip())}".rstrip()
        if indent:
            out = textwrap.indent(out, indent)
        return out

    def format_tests(self, data, toc):
        ss = [""]
        s = []
        s.append("## 2. Procedures\n")
        s.append("\n")
        s.append("This section includes procedures for all the executed tests.\n")
        ss.append("\n".join(s))

        def anchor(heading):
            return re.sub(r"\s+", "-", re.sub(r"[^a-zA-Z0-9-_\s]+", "", heading.lower()))

        for test in data["tests"]:
            s = []

            id = ".".join(["1" if i == 0 else str(int(p) + 1) for i, p in enumerate(test["id"].split(sep)[1:])])
            s.append(f"### 2.{id} {test['keyword'].upper()} **{test['name']}**\n")
            heading = s[-1].lstrip("# ").strip()
            name = f"{test['keyword'].upper()} {test['name']}"
            s.append(f"**Name** `{test['path']}`\n")

            if test["attributes"]:
                s.append("**Attributes**  \n")
                for attr in test["attributes"]:
                    s.append(f'||**{attr["attribute_name"]}**||{attr["attribute_value"]}||')
                s.append("\n")

            if test["tags"]:
                t = []
                for tag in test["tags"]:
                    t.append(f'`{tag["tag_value"]}`')
                s.append(f"**Tags**  {', '.join(t)}")
                s.append("\n")

            if test["description"]:
                s.append("##### DESCRIPTION\n")
                s.append(self.format_multiline(test['description']) if test['description'] else "")
                s.append("\n")

            if test["requirements"]:
                s.append("##### REQUIREMENTS\n")
                for req in test["requirements"]:
                    s.append(f'* **{req["requirement_name"]}**  ')
                    s.append(textwrap.indent(f'<div markdown="1" class="text-small">version: {req["requirement_version"]}</div>', "  "))
                    s.append(textwrap.indent(f'<div markdown="1" class="test-description">{req["requirement_description"].strip()}</div>', "  "))
                s.append("\n")

            def add_steps(s, test, level):
                for step in test["steps"]:
                    s.append(f"{'  ' * level}* **{step['keyword']}**  {step['name']}  ")
                    if step["description"]:
                        s.append(textwrap.indent(f"<div markdown="1" class=\"test-description\">{step['description'].strip()}</div>", "    " * level).rstrip())
                    if getattr(TestType, step["type"]) < TestType.Test:
                        if step["steps"]:
                            add_steps(s, step, level + 1)
                if not test["steps"]:
                    s.append("* None")

            s.append("##### PROCEDURE\n")
            add_steps(s, test, 1)
            s.append("\n")
            ss.append("\n".join(s))

            toc.append(f"{len(id.split('.')) * '  '}* 2.{id} [{name}](#{anchor(heading)})")

        return "\n---\n".join(ss)

    def format(self, data):
        toc = []
        toc.append("* 1 [Overview](#1-overview)")
        toc.append("* 2 [Procedures](#2-procedures)")
        body = self.format_tests(data, toc)
        return template.strip() % {
            "title": data["title"],
            "table_of_contents": "\n".join(toc),
            "logo": self.format_logo(data),
            "confidential": self.format_confidential(data),
            "copyright": self.format_copyright(data),
            "body": body
        }


class Handler(HandlerBase):
    Formatter = Formatter

    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser("specification", help="specification report", epilog=epilog(),
            description="Generate specifiction report.",
            formatter_class=HelpFormatter)

        parser.add_argument("input", metavar="input", type=argtype.logfile("r", bufsize=1, encoding="utf-8"),
                nargs="?", help="input log, default: stdin", default="-")
        parser.add_argument("output", metavar="output", type=argtype.file("w", bufsize=1, encoding="utf-8"),
                nargs="?", help='output file, default: stdout', default="-")
        parser.add_argument("--copyright", metavar="name", help="add copyright notice", type=str)
        parser.add_argument("--confidential", help="mark as confidential", action="store_true")
        parser.add_argument("--logo", metavar="path", type=argtype.file("rb"),
                help='use logo image (.png)')

        parser.set_defaults(func=cls())

    def company(self, args):
        d = {}
        if args.copyright:
            d["name"] = args.copyright
        if args.confidential:
            d["confidential"] = True
        if args.logo:
            d["logo"] = args.logo.read()
        return d

    def title(self, results):
        if results["tests"]:
            title = basename(list(results["tests"].values())[0]["test"]["test_name"])
            if title and title[0].upper() != title[0]:
                title = title.title()
            return title
        return ""

    def test(self, results, test):
        t = {}
        t["path"] = test["test_name"]
        t["level"] = test["test_level"]
        t["keyword"] = test["test_type"]
        t["type"] = test["test_type"]
        t["subtype"] = test["test_subtype"]
        if test["test_subtype"]:
                t["keyword"] = test["test_subtype"]
        t["description"] = test["test_description"]
        t["attributes"] = test["attributes"]
        t["tags"] = test["tags"]
        t["requirements"] = test["requirements"]
        t["name"] = basename(test["test_name"])
        t["id"] = test["test_id"]

        children = results["tests_by_parent"].get(test["test_id"])
        t["steps"] = []
        if children:
            for child in children:
                t["steps"].append(self.test(results, child))
        return t

    def tests(self, results):
        tests = []
        for uname, test in results["tests"].items():
            t = {}
            if getattr(TestType, test["test"]["test_type"]) < TestType.Test:
                continue
            tests.append(self.test(results, test["test"]))
        return tests

    def data(self, results, args):
        d = OrderedDict()
        d["title"] = self.title(results)
        d["tests"] = self.tests(results)
        d["company"] = self.company(args)
        return d

    def generate(self, formatter, results, args):
        output = args.output
        output.write(
            formatter.format(self.data(results, args))
        )
        output.write("\n")

    def handle(self, args):
        results = OrderedDict()
        ResultsLogPipeline(args.input, results).run()
        formatter = self.Formatter()
        self.generate(formatter, results, args)
