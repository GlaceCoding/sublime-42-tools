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

            pos = 1
            if 'pos' in parser.attr:
                pos += int(parser.attr['pos']) 
            
            (row, col) = self.view.rowcol(self.view.sel()[0].begin())
            point = self.view.text_point(row + pos, 0)
            position = self.view.line(sublime.Region(point)).begin()

            if 'match' in parser.attr:
                regex = re.escape(parser.attr['match']).replace('\\*', '.*')
                regexMatch = re.compile('^' + regex + '$')
                regex = '(' + regex + ')'
                regexErase = re.compile('^' + re.escape(indent + template.format('{0}')).replace('\\{0\\}', regex) + '$')
            else:
                regexErase = re.compile('^' + re.escape(indent + template.format('{0}')).replace('\\{0\\}', '(.*)') + '$')

            while True:
                point = self.view.text_point(row + pos, 0)
                line = self.view.substr(self.view.line(point))
                match = re.match(regexErase, line)
                if line is '' or match is None:
                    break
                exclude = None
                if 'exclude' in parser.attr:
                    regex = re.compile('(?:^|,) *(' + re.escape(match.group(1)) + ') *(?:$|,)')
                    exclude = re.search(regex, parser.attr['exclude'])
                if exclude is not None:
                    break
                region = self.view.line(point)
                region = sublime.Region(region.begin(), region.end() - 1)
                self.view.erase(edit, self.view.full_line(region))

            output = ''

            for root, dirs, files in os.walk(path, topdown=False):
                for name in files:
                    match = 1
                    exclude = None
                    if 'match' in parser.attr:
                        match = re.match(regexMatch, name)
                    if match is not None:
                        src = os.path.relpath(os.path.join(root, name), prepath)
                        src = src.replace('\\', '/')
                        src = ('', '/')[parser.attr['path'][0] == '/'] + src
                        if 'exclude' in parser.attr:
                            regex = re.compile('(?:^|,) *' + re.escape(src) + ' *(?:$|,)')
                            exclude = re.match(regex, parser.attr['exclude'])
                        if exclude is None:
                            output += printTemplate(indent, src, template)

            if output is not '':
                self.view.insert(edit, position, output)
                sublime.status_message('ok')
        else:
            sublime.status_message('Comment not match.')


def printTemplate(indent, src, template):
    output = indent + template.format(src) + '\n'
    return output
