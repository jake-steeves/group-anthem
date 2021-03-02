import re
import sys
import json
import copy
import spacy
from os import listdir
from functools import reduce
import operator as op


def getMessageHeader(message):
  pattern = r"^(?P<date>[0-9]{1,2}/[0-9]{1,2}/[0-9]{1,2}), (?P<hour>[0-9]{1,2}):(?P<minute>[0-9]{1,2}) (?P<code>[AP])M - (?P<name>[^:]+): (?P<line>.*)$"
  match = re.match(pattern, message)
  if match:
    code_diff = 0 if match.group('code') == 'A' else 12
    time = str(int(match.group('hour')) + code_diff) + ':' + match.group('minute')
    return True, {
      'name': match.group('name'),
      'lines': [match.group('line')],
      'date': match.group('date'),
      'time': time
    }
  return False, message


def parseMessages(chatlog):
  prev = None
  parsed_messages = []
  for message in chatlog:
    parsed, result = getMessageHeader(message)
    if parsed:
      if prev:
        parsed_messages.append({ 'msg': prev })

      prev = result
    else:
      if not prev:
        sys.exit("Check input file for proper first line formatting")
      prev['lines'].append(message)

  if parsed_messages[-1] != prev:
    parsed_messages.append({ 'msg': prev })

  return parsed_messages


def getBasicStats(messages):
  author_stats = {}
  overall_stats = { 'msgs': 0, 'chars': 0, 'lines': 0, 'files': 0, 'members_ct': 0 }

  for message_obj in messages:
    message = message_obj['msg']
    name = message['name']
    chars = sum([len(msg) for msg in message['lines']])
    lines = len(message['lines'])
    files_sent = sum(['(file attached)' in msg for msg in message['lines']])
    if not name in author_stats:
      author_stats[name] = { 'msgs': 1, 'chars': chars, 'lines': lines, 'files': files_sent }
      overall_stats['members_ct'] += 1 
    else:
      author_stats[name]['msgs'] += 1
      author_stats[name]['chars'] += chars
      author_stats[name]['lines'] += lines
      author_stats[name]['files'] += files_sent

      overall_stats['msgs'] += 1
      overall_stats['chars'] += chars
      overall_stats['lines'] += lines
      overall_stats['files'] += files_sent

  for author, author_stat in author_stats.items():
    author_stats[author]['msg_portion'] = float(author_stat['msgs']) / overall_stats['msgs'] 
    author_stats[author]['line_portion'] = float(author_stat['lines']) / overall_stats['lines'] 
    author_stats[author]['char_portion'] = float(author_stat['chars']) / overall_stats['chars']
    author_stats[author]['file_portion'] = float(author_stat['files']) / overall_stats['files']

  return overall_stats, author_stats


def parseLine(line, nlp):
  doc = nlp(line)
  shape = [token.shape_ for token in doc]
  deps = [token.dep_ for token in doc]
  parts = [token.pos_ for token in doc]
  return { 'line': line, 'shape': shape, 'deps': deps, 'parts': parts}


def addSpacyNlp(parsed_messages):
  nlp = spacy.load('en_core_web_sm')
  nlp_messages = []
  for message in parsed_messages:
    nlp_message = copy.deepcopy(message)
    nlp_message['msg']['lines'] = [parseLine(line, nlp) for line in nlp_message['msg']['lines']]
    nlp_messages.append(nlp_message)
  return nlp_messages

    
def main(chat, outdir, mediadir):
  with open(chat, 'r') as f:
    chatlog = f.readlines()
  f.closed
  
  parsed_messages = parseMessages(chatlog)

  nlp_messages = addSpacyNlp(parsed_messages)
  overall_stats, author_stats = getBasicStats(parsed_messages)

  with open(outdir + '/messages.json', 'w+') as f:
    json.dump(nlp_messages, f, indent=4)
  f.closed
  with open(outdir + '/overall.json', 'w+') as f:
    json.dump(overall_stats, f, indent=4)
  f.closed
  with open(outdir + '/authors.json', 'w+') as f:
    json.dump(author_stats, f, indent=4)
  f.closed


if __name__ == "__main__":
  if len(sys.argv) < 2:
    sys.exit("Provide one input chat text file")
  chat = sys.argv[1]
  if len(sys.argv) >= 3:
    outdir = sys.argv[2]
  else:
    outdir = None
  if len(sys.argv) >= 4:
    mediadir = sys.argv[3]
  else:
    mediadir = None
  main(chat, outdir, mediadir)