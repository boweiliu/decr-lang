#!/usr/bin/env python
# a Decr interpreter.
# usage: parser.py SRC_FILE

import sys
if (sys.version_info <= (3, 0)):
  reload(sys)
  sys.setdefaultencoding('utf-8')
from pprint import pprint


DESCRIPTION = """
All symbols must be separated by spaces.
Valid symbols are:
<< VAR (write integers to stdout)
>> VAR (read integers from stdin)
< VAR (write ascii to stdout)
> VAR (read ascii from stdin)
VAR ++ (increment)
VAR = 0 (declare variable and/or assign 0)
VAR = OTHERVAR (declare variable and/or assign OTHERVAR to it)
loop VAR (execute the following block VAR times. Blocks are denoted python-style using indentation.)
# Comments start with # .
For cli-mode (reading from '-'), use 'exit' to terminate the program and begin reading input.
"""

def main(argv):
  if len(argv) < 2 or argv[1] == '-h':
    print("Usage: {} SRC_FILE".format(argv[0]))
    print("Language semantics: ")
    print(DESCRIPTION)
    sys.exit(1)

  if argv[1] == '-': # reading from stdin
    lines = []
    while True:
      lines.append(sys.stdin.readline())
      if lines[-1].strip() == 'exit':
        lines = lines[:-1]
        break
  else:
    with open(argv[1]) as f:
      lines = [ l for l in f ]
 
  # first we remove those now as well as empty lines. TODO(bowei): this mangles line numbers for debugging
  lines = [ l for l in lines if l.strip() != '' and l.strip()[0] != '#' ] + ['']
 
  # keep global state of all variable names and their current values
  decr_vars = {} 
  # keep global state of loops stack. stores tuples (indent state, line number of LOOP command, and number of loop iterations remaining)
  decr_loops = []
  lineno = 0
  while lineno < len(lines) - 1: # skip the last sentinel empty line
    l = lines[lineno]
    tokens = l.strip().split()
    # decide what sort of statement it is
    #if tokens[0] == '#':
    #  lineno += 1
    #  continue
    if '>>' in tokens:
      if tokens[0] == '>>' and len(tokens) == 2:
        # read in from stdin
        varname = tokens[1]
        check_reserved(varname, lineno)
        raw_val = None
        try:
          raw_val = sys.stdin.readline()
          decr_vars[varname] = int(raw_val)
        except Exception as e:
          print('Error reading in integer value on line {}:'.format(lineno))
          print('Value {} could not be stored in variable {}'.format(repr(raw_val), varname))
          break
      else:
        print('Error parsing statement, invalid integer read command:')
        print('{}:  {}'.format(lineno, l))
        break
    elif '>' in tokens:
      if tokens[0] == '>' and len(tokens) == 2:
        # read in from stdin
        varname = tokens[1]
        check_reserved(varname, lineno)
        raw_val = None
        try:
          raw_val = sys.stdin.readline()
          decr_vars[varname] = ord(raw_val[0])
        except Exception as e:
          print('Error reading in ascii value on line {}:'.format(lineno))
          print('Value {} could not be stored in variable {}'.format(repr(raw_val), varname))
          break
      else:
        print('Error parsing statement, invalid ascii read command:')
        print('{}:  {}'.format(lineno, l))
        break
    elif '<<' in tokens:
      if tokens[0] == '<<' and len(tokens) == 2:
        varname = tokens[1]
        #check_reserved(varname, lineno)
        if varname not in decr_vars:
          print('Error printing value on line {}:'.format(lineno))
          print('Variable {} does not exist!'.format(varname))
          break
        else:
          print(str(decr_vars[varname]))
      else:
        print('Error parsing statement, invalid integer write command:')
        print('{}:  {}'.format(lineno, l))
        break
    elif '<' in tokens:
      if tokens[0] == '<' and len(tokens) == 2:
        varname = tokens[1]
        #check_reserved(varname, lineno)
        if varname not in decr_vars:
          print('Error printing value on line {}:'.format(lineno))
          print('Variable {} does not exist!'.format(varname))
          break
        else:
          print(chr(decr_vars[varname]))
      else:
        print('Error parsing statement, invalid ascii write command:')
        print('{}:  {}'.format(lineno, l))
        break
    elif '=' in tokens:
      if tokens[1] == '=' and len(tokens) == 3:
        varname = tokens[0]
        check_reserved(varname, lineno)
        if tokens[2] not in decr_vars and tokens[2] != '0':
          print('Error in assignment statement on line {}:'.format(lineno))
          print('Rvalue {} does not exist!'.format(tokens[2]))
          break
        else:
          decr_vars[varname] = 0 if tokens[2] == '0' else decr_vars[tokens[2]]
      else:
        print('Error parsing statement, invalid assignment command:')
        print('{}:  {}'.format(lineno, l))
        break
    elif '++' in tokens:
      if tokens[1] == '++' and len(tokens) == 2:
        varname = tokens[0]
        #check_reserved(varname, lineno)
        if varname not in decr_vars:
          print('Error incrementing value on line {}:'.format(lineno))
          print('Variable {} does not exist!'.format(varname))
          break
        else:
          decr_vars[varname] += 1
      else:
        print('Error parsing statement, invalid increment command:')
        print('{}:  {}'.format(lineno, l))
        break
    elif 'loop' in tokens:
      if tokens[0] == 'loop' and len(tokens) == 2:
        varname = tokens[1]
        if varname not in decr_vars:
          print('Error looping for value on line {}:'.format(lineno))
          print('Variable {} does not exist!'.format(varname))
          break
        else:
          # check indentation
          if count_spaces(lines[lineno + 1]) <= count_spaces(l):
            print('Error parsing indentation after loop:')
            print('{}:  {}'.format(lineno, l))
            print('{}:  {}'.format(lineno + 1, lines[lineno + 1]))
            break
          # special logic to handle zero loop iterations
          if decr_vars[varname] == 0:
            # go to one before next line with at most this level of indentation
            num_indent = count_spaces(l)
            while count_spaces(lines[lineno + 1]) > num_indent:
              lineno += 1
          #else:
          decr_loops.append([count_spaces(l), lineno, decr_vars[varname]])
      else:
        print('Error parsing statement, invalid loop command:')
        print('{}:  {}'.format(lineno, l))
        break
    else:
      print('Error parsing statement, not a valid command. Perhaps you are missing some spaces?')
      print('{}:  {}'.format(lineno, l))
      break
      

    if count_spaces(lines[lineno + 1]) > count_spaces(l) and 'loop' not in tokens:
      print('Error parsing increase in indentation without loop:')
      print('{}:  {}'.format(lineno, l))
      print('{}:  {}'.format(lineno + 1, lines[lineno + 1]))
      break
    elif count_spaces(lines[lineno + 1]) >= count_spaces(l):
      lineno += 1
    elif count_spaces(lines[lineno + 1]) < count_spaces(l):
      # logic for if we ended a loop
      next_indent = count_spaces(lines[lineno + 1])
      # successively pop loop objects off the loop stack
      while len(decr_loops) > 0 and next_indent <= decr_loops[-1][0] and decr_loops[-1][2] <= 1:
        decr_loops = decr_loops[:-1]
      if len(decr_loops) == 0:
        lineno += 1
      elif next_indent > decr_loops[-1][0]:
        lineno += 1
      elif decr_loops[-1][2] > 1:
        lineno = decr_loops[-1][1] + 1
        decr_loops[-1][2] -= 1
    #print('line no is {}'.format(lineno))
    #pprint(decr_loops)
    #pprint(decr_vars)

def check_reserved(varname, lineno):
  RESERVED = set(['++', '<<', '>>', '=', '0', 'loop'])
  if varname in RESERVED:
    print('Error parsing statement on line {}:'.format(lineno))
    print('Variable name {} is reserved!'.format(varname))

def count_spaces(l):
  for i in range(len(l)):
    if l[i] != ' ':
      return i
  return len(l)

if __name__ == '__main__':
  main(sys.argv)
