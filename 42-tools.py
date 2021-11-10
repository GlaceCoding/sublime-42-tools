import sublime
import sublime_plugin

import os
import re
from html.parser import HTMLParser


class MyHTMLParser(HTMLParser):
    attr = {}
    def handle_starttag(self, tag, attrs):
        for attr in attrs:
            self.attr[attr[0]] = attr[1]


class List42toolsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        line = self.view.substr(self.view.line(self.view.sel()[0]))
        regex = r'^(\s*)(?:(?:\#|\/\/)\s?)?(<!--|\/\*)(.*)(-->|\/\*)$'
        match = re.match(regex, line)

        if match is not None:
            line = re.sub(regex, r'<img \g<3>>', line)

            parser = MyHTMLParser()
            parser.feed(line)

            if not ('path' in parser.attr and 'template' in parser.attr):
                return sublime.status_message('Need 2 arguments path and template.')

            indent = match.group(1)

            template = parser.attr['template']

            prepath = os.path.dirname(self.view.file_name()) + '/'
            prepath = os.path.abspath(prepath + (parser.attr['pre'] or ''))

            path = prepath + '/' + parser.attr['path']
            path = os.path.abspath(path)

            if 'pos' in parser.attr:
                (row, col) = self.view.rowcol(self.view.sel()[0].begin())
                target = self.view.text_point(row + int(parser.attr['pos']), 0)

                self.view.sel().clear()
                self.view.sel().add(sublime.Region(target))

            position = self.view.line(self.view.sel()[0]).end()

            output = ''

            for root, dirs, files in os.walk(path, topdown=False):
                for name in files:
                    match = 1
                    exclude = None
                    if 'match' in parser.attr:
                        regex = re.compile('^' + re.escape(parser.attr['match']).replace('\\*', '.*') + '$')
                        match = re.match(regex, name)
                    if match is not None and 'exclude' in parser.attr:
                        regex = re.compile('(?:^|,) *' + re.escape(name) + ' *(?:$|,)')
                        exclude = re.match(regex, parser.attr['exclude'])
                    if match is not None and exclude is None:
                        src = os.path.relpath(os.path.join(root, name), prepath)
                        src = src.replace('\\', '/')
                        src = ('', '/')[parser.attr['path'][0] == '/'] + src
                        output += printTemplate(indent, src, template)

            if output is not '':
                self.view.insert(edit, position, output)
                sublime.status_message('ok')
        else:
            sublime.status_message('Comment not match.')


def printTemplate(indent, src, template):
    output = '\n' + indent + template.format(src)
    return output
