from os import popen
from pprint import pprint
import linecache
from termcolor import colored, cprint
import argparse
import time
from datetime import datetime


def run_grep(function_name, path):
    time_start = datetime.now()

    command = 'grep -nr {} {}'.format(function_name, path)
    print(colored('running "{}"'.format(command), 'blue'))
    grep_results = popen(command).read()
    time_diff = round((datetime.now() - time_start).microseconds / 1000000, 2)  # something is busted with this calculation.
    print(colored("grep took {} seconds. Building dependency tree...".format(time_diff), 'blue', attrs=['bold']))

    parse_grep_results(grep_results, function_name + '(')


def parse_grep_results(grep_results, function_name):
    occurrences = {}

    for result in grep_results.split('\n'):
        try:
            filepath, line_number, code = result.split(':')
        except ValueError:
            pass
        else:
            record = {'line_number': int(line_number), 'code': code}
            if filepath not in occurrences:
                occurrences[filepath] = [record]
            else:
                occurrences[filepath].append(record)

    final_results = {}
    for filepath, mentions_list in occurrences.items():
        if 'test_' in filepath:
            continue
        for mention in mentions_list:
            if 'import' in mention['code'] or 'def ' in mention['code']:
                continue
            else:
                if filepath not in final_results:
                    final_results[filepath] = [mention]
                else:
                    final_results[filepath].append(mention)

    for filepath in final_results:
        for occurrence in final_results[filepath]:
            for line_number in reversed(range(occurrence['line_number'])):
                line = linecache.getline(filepath, line_number)
                if 'def ' in line:  # We found the function that calls our function of interest!
                    line = line.replace('def ', '')
                    line = line.split('(')[0]
                    print('In file {}, {} calls our function of interest {} in line {}'.format(
                        colored(filepath, 'green'),
                        line,
                        function_name,
                        line_number
                    ))
                    break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Find all execution flows that lead to calling a Python function.')
    parser.add_argument('-f', '--function_name', dest='function_name', type=str, help='End function')
    parser.add_argument('-p', '--path', dest='path', type=str, default='.', help='Path to search on')
    args = parser.parse_args()

    run_grep(args.function_name, args.path)
