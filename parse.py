import re
import sys
import pprint
from os import listdir


def getMessageHeader(message):
  pattern = r"^(?P<date>[0-9]{1,2}/[0-9]{1,2}/[0-9]{1,2}), (?P<hour>[0-9]{1,2}):(?P<minute>[0-9]{1,2}) (?P<code>[AP])M - (?P<name>[^:]+): (?P<msg>.*)$"
  match = re.match(pattern, message)
  if match:
    code_diff = 0 if match.group('code') == 'A' else 12
    time = str(int(match.group('hour')) + code_diff) + ':' + match.group('minute')
    return True, {
      'name': match.group('name'),
      'msgs': [match.group('msg')],
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
        parsed_messages.append(prev)

      prev = result
    else:
      if not prev:
        sys.exit("Check input file for proper first line formatting")
      prev['msgs'].append(message)

  if parsed_messages[-1] != prev:
    parsed_messages.append(prev)

  return parsed_messages

def getStats(messages):
  author_stats = {}
  overall_stats = { 'msgs': 0, 'chars': 0, 'lines': 0, 'files': 0, 'members_ct': 0 }

  for message in messages:
    name = message['name']
    chars = sum([len(msg) for msg in message['msgs']])
    lines = len(message['msgs'])
    files_sent = sum(['(file attached)' in msg for msg in message['msgs']])
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


def main(chat, media_dir):
  with open(chat, 'r') as f:
    chatlog = f.readlines()
  f.closed

  parsed_messages = parseMessages(chatlog)
  overall_stats, author_stats = getStats(parsed_messages)

  pprint.pprint(overall_stats)
  pprint.pprint(author_stats)


if __name__ == "__main__":
  if len(sys.argv) < 2:
    sys.exit("Provide one input chat text file")
  chat = sys.argv[1]
  if len(sys.argv) <= 3:
    media_dir = sys.argv[2]
  else:
    media_dir = None
  main(chat, media_dir)