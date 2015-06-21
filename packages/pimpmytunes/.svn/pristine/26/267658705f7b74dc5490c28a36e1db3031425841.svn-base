import cStringIO,operator

def printTable(rows, width):
    '''
    Print a table in a nice way. Contains lots of bugs, for free!
    '''

    delim = ' | '
    # Clalculate the with of each cell
    widths = [ 0 for i in xrange(len(rows[0])) ]
    for row in rows:
        for i in xrange(len(row)):
            widths[i] = max(widths[i], len(row[i]) + len(delim))

    # calculate the total width of all columns
    totalWidth = 0
    for w in widths: totalWidth += w

    # calculate the reduction ratio
    red = float(totalWidth) / float(width)

    # Reduce each column by the right amount
    tempWidths = [ float(w) / red for w in widths ]

    # Except the first colum. leave it alone
    tempWidths[0] = widths[0]

    # Now go over the columns again. Round down the figures and keep track of the round-off error
    # once we go over one, give the next column one more character.
    widths = []
    rem = 0.0
    total = 0
    for w in tempWidths:
        rem += w - int(w)
        col = int(w)
        if col < 6:
            rem -= 6 - col
            col = 6
        elif col > 10 and rem < -1.0:
            col += int(rem)
            rem += int(rem) 
        if rem >= 1.0:
            #print '*',
            col += 1
            rem -= 1.0
        widths.append(col)
        total += col
        #print total,

    #print
    #for t in widths: print t,
    #print
    #print "total: %d width: %d" % (total, width)

    # Loop over each cell, chopping it at the necessary length
    new = [ ]
    for row in rows:
        col = []
        for i in xrange(len(row)):
            if len(row[i]) <= widths[i] - len(delim): 
                col.append(row[i])
            else:
                #col.append(row[i][:(widths[i]-len(delim))])
                col.append(row[i][:(widths[i]-(len(delim) + 1))] + '>')
        new.append(col)
           
    #print "012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345"
    #print "          1         2         3         4         5         6         7         8         9         0         1         2         3         4         5"
    print indent(new, True, delim=delim)

def indent(rows, hasHeader=False, headerChar='-', delim=' | ', justify='left',
           separateRows=False, prefix='', postfix='', wrapfunc=lambda x:x):
    """Indents a table by column.
       - rows: A sequence of sequences of items, one sequence per row.
       - hasHeader: True if the first row consists of the columns' names.
       - headerChar: Character to be used for the row separator line
         (if hasHeader==True or separateRows==True).
       - delim: The column delimiter.
       - justify: Determines how are data justified in their column. 
         Valid values are 'left','right' and 'center'.
       - separateRows: True if rows are to be separated by a line
         of 'headerChar's.
       - prefix: A string prepended to each printed row.
       - postfix: A string appended to each printed row.
       - wrapfunc: A function f(text) for wrapping text; each element in
         the table is first wrapped by this function."""
    # closure for breaking logical rows to physical, using wrapfunc
    def rowWrapper(row):
        newRows = [wrapfunc(item).split('\n') for item in row]
        return [[substr or '' for substr in item] for item in map(None,*newRows)]
    # break each logical row into one or more physical ones
    logicalRows = [rowWrapper(row) for row in rows]
    # columns of physical rows
    columns = map(None,*reduce(operator.add,logicalRows))
    # get the maximum of each column by the string length of its items
    maxWidths = [max([len(unicode(item)) for item in column]) for column in columns]
    rowSeparator = headerChar * (len(prefix) + len(postfix) + sum(maxWidths) + \
                                 len(delim)*(len(maxWidths)-1))
    # select the appropriate justify method
    justify = {'center':unicode.center, 'right':unicode.rjust, 'left':unicode.ljust}[justify.lower()]
    output=cStringIO.StringIO()
    if separateRows: print >> output, rowSeparator
    for physicalRows in logicalRows:
        for row in physicalRows:
            print >> output, \
                prefix \
                + delim.join([justify(unicode(item),width) for (item,width) in zip(row,maxWidths)]).encode('utf-8', 'replace') \
                + postfix
        if separateRows or hasHeader: print >> output, rowSeparator; hasHeader=False
    return output.getvalue()

# written by Mike Brown
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/148061
def wrap_onspace(text, width):
    """
    A word-wrap function that preserves existing line breaks
    and most spaces in the text. Expects that existing line
    breaks are posix newlines (\n).
    """
    return reduce(lambda line, word, width=width: '%s%s%s' %
                  (line,
                   ' \n'[(len(line[line.rfind('\n')+1:])
                         + len(word.split('\n',1)[0]
                              ) >= width)],
                   word),
                  text.split(' ')
                 )

import re
def wrap_onspace_strict(text, width):
    """Similar to wrap_onspace, but enforces the width constraint:
       words longer than width are split."""
    wordRegex = re.compile(r'\S{'+unicode(width)+r',}')
    return wrap_onspace(wordRegex.sub(lambda m: wrap_always(m.group(),width),text),width)

import math
def wrap_always(text, width):
    """A simple word-wrap function that wraps text on exactly width characters.
       It doesn't split the text in words."""
    return '\n'.join([ text[width*i:width*(i+1)] \
                       for i in xrange(int(math.ceil(1.*len(text)/width))) ])
    
