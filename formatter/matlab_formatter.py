#!/usr/bin/env python3
import re
import sys

# divide string into three parts by extracting and formatting certain expressions
def extract(part):
    # string
    m = re.match(r'(^|.*[\(\[\{,;=\+])\s*(\'.*\')\s*(\S.*|$)', part)
    if m:
        return (m.group(1), m.group(2), m.group(3))

    # comment
    m = re.match(r'(^|.*\S)\s*(%.*)', part)
    if m:
        return (m.group(1), m.group(2), '')

    # decimal number (e.g. 5.6E-3)
    m = re.match(r'(^|.*[^\d\.]|.*\s)\s*(\d+\.?\d*)([eE][+-]?)(\d+)\s*(\S.*|$)', part)
    if m:
        return (m.group(1) + ' ' + m.group(2), m.group(3), m.group(4) + ' ' + m.group(5))

    # rational number (e.g. 1/4)
    m = re.match(r'(^|.*[^\d\.]|.*\s)\s*(\d+\.?\d*)\s*(\/)\s*(\d+\.?\d*)\s*(\S.*|$)', part)
    if m:
        return (m.group(1) + ' ' + m.group(2), m.group(3), m.group(4) + ' ' + m.group(5))

    # signum (unary - or +)
    m = re.match(r'(^|.*[\(\[\{,;:=])\s*(\+|\-)\s*(\S.*|$)', part)
    if m:
        return (m.group(1), m.group(2), m.group(3))

    # incrementor (++ or --)
    m = re.match(r'(^|.*\S)\s*(\+|\-)\s*(\+|\-)\s*([\)\]\},;].*|$)', part)
    if m:
        return (m.group(1), m.group(2) + m.group(3), m.group(4))

    # colon
    m = re.match(r'(^|.*\S)\s*(:)\s*(\S.*|$)', part)
    if m:
        return (m.group(1), m.group(2), m.group(3))

    # dot-operator-assignmet (e.g. .+=)
    m = re.match(r'(^|.*\S)\s*(\.)\s*(\+|\-|\*|/|\^)\s*(=)\s*(\S.*|$)', part)
    if m:
        return (m.group(1) + ' ', m.group(2) + m.group(3) + m.group(4), ' ' + m.group(5))

    # .power (.^)
    m = re.match(r'(^|.*\S)\s*(\.)\s*(\^)\s*(\S.*|$)', part)
    if m:
        return (m.group(1), m.group(2) + m.group(3), m.group(4))

    # power (^)
    m = re.match(r'(^|.*\S)\s*(\^)\s*(\S.*|$)', part)
    if m:
        return (m.group(1), m.group(2), m.group(3))

    # combined operator (e.g. +=, .+, etc.)
    m = re.match(r'(^|.*\S)\s*(\.|\+|\-|\*|\\|/|=|<|>|\||\&|!|~|\^)\s*(<|>|=|\+|\-|\*|/|\&|\|)\s*(\S.*|$)', part)
    if m:
        return (m.group(1) + ' ', m.group(2) + m.group(3), ' ' + m.group(4))

    # not (~ or !)
    m = re.match(r'(^|.*\S)\s*(!|~)\s*(\S.*|$)', part)
    if m:
        return (m.group(1), m.group(2), m.group(3))

    # single operator (e.g. +, -, etc.)
    m = re.match(r'(^|.*\S)\s*(\+|\-|\*|\\|/|=|!|~|<|>|\||\&)\s*(\S.*|$)', part)
    if m:
        return (m.group(1) + ' ', m.group(2), ' ' + m.group(3))

    # function call
    m = re.match(r'(.*[A-Za-z0-9_])\s*(\()\s*(\S.*|$)', part)
    if m:
        return (m.group(1), m.group(2), m.group(3))

    # parenthesis open
    m = re.match(r'(^|.*)(\(|\[|\{)\s*(\S.*|$)', part)
    if m:
        return (m.group(1), m.group(2), m.group(3))

    # parenthesis close
    m = re.match(r'(^|.*\S)\s*(\)|\]|\})(.*|$)', part)
    if m:
        return (m.group(1), m.group(2), m.group(3))

    # comma/semicolon
    m = re.match(r'(^|.*\S)\s*(,|;)\s*(\S.*|$)', part)
    if m:
        return (m.group(1), m.group(2), ' ' + m.group(3))

    # multiple whitespace
    m = re.match(r'(^|.*\S)(\s{2,})(\S.*|$)', part)
    if m:
        return (m.group(1), ' ', m.group(3))

    return 0


# recursively format string
def format(part):
    m = extract(part)
    if m:
        return format(m[0]) + m[1] + format(m[2])
    return part


# take care of indentation and call format(line)
def formatLine(ilvl, iwidth, line):
    ctrlstart = r'(^|\s*)(function|if|while|for|switch|try)(\s+\S.*|\s*$)'
    ctrlcont = r'(^|\s*)(elseif|else|case|catch|otherwise|catch)(\s+\S.*|\s*$)'
    ctrlend = r'(^|\s*)(end|endfunction|endif|endwhile|endfor|endswitch)(\s+\S.*|\s*$)'

    width = iwidth*' '

    m = re.match(ctrlstart, line)
    if m:
        return (ilvl+1, ilvl*width + m.group(2) + ' ' + format(m.group(3)).strip())

    m = re.match(ctrlcont, line)
    if m:
        return (ilvl, (ilvl-1)*width + m.group(2) + ' ' + format(m.group(3)).strip())

    m = re.match(ctrlend, line)
    if m:
        return (ilvl-1, (ilvl-1)*width + m.group(2) + ' ' + format(m.group(3)).strip())

    return (ilvl, ilvl*width + format(line).strip())


def main(filename, indentwidth, start, end):
    indent_new = 0
    wlines = rlines = []
    blank = True
    with open(filename, 'r') as f:
        rlines = f.readlines()[start-1:end]

    # get initial indent lvl
    p = r'(\s*)(.*)'
    m = re.match(p, rlines[0])
    if m:
        indent_new = len(m.group(1))//indentwidth
        rlines[0] = m.group(2)

    for line in rlines:
        # remove additional newlines
        if re.match(r'^\s*$', line):
            if not blank:
                blank = True
                wlines.append('')
            continue

        # format line
        indent = indent_new
        (indent_new, line) = formatLine(indent, indentwidth, line)

        # add newline before block
        if indent < indent_new and not blank:
            wlines.append('')

        # add formatted line
        wlines.append(line)

        # add newline after block
        if (indent > indent_new):
            wlines.append('')
            blank = True
        else:
            blank = False

    # remove last line if blank
    while wlines and not wlines[-1]:
        wlines.pop()

    # write output
    for line in wlines:
        print(line)


if __name__ == '__main__':

    argc = len(sys.argv)
    options = {'--startLine' : 0, '--endLine' : None, '--indentWidth' : 4}
    if argc < 2:
        print('usage: matlab_formatter.py filename [options...]\n  OPTIONS:\n    --startLine=\\d\n    --endLine=\\d\n    --indentWidth=\\d\n', file=sys.stderr)
    else:
        for arg in sys.argv[2:] :
            key, value = arg.split('=')
            try:
                value = eval(value)
            finally:
                options[key.strip()] = value

        indent = options['--indentWidth']
        start = options['--startLine']
        end = options['--endLine']
        main(sys.argv[1], indent, start, end)
