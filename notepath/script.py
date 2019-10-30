#!/usr/bin/env python3
# The function annotations in this module require Python 3.5 or higher.

import argparse
import os
import sys
import time

from typing import List

# Explicitly put the current directory in the import path, so that the main
# script can use this file as a module without causing the "import" lines
# below to trigger ModuleNotFoundErrors.
_here_ = os.path.realpath(os.path.dirname(__file__))
if _here_ not in sys.path:
    sys.path.append(_here_)

from basics import get_data_path, FilePath, Object
from database import Database, DEFAULT_DATABASE_FILENAME
from license import print_license
from note import get_notes_from_file
from querybuilder import QueryBuilder
from utils import (get_readable_filesize, get_readable_moddate,
                   timestamp_for_journal, timestamp_for_logging)


class Script(Object):
    def run(self) -> None:
        self._init_options()
        self.args = self.parser.parse_args()
        
        if self.args.license:
            print_license()
            sys.exit(0)

        path = get_data_path(DEFAULT_DATABASE_FILENAME)
        self.db = Database(path)

        if self.args.database:
            self.db.print_sqlite_info()
            sys.exit(0)

        if self.args.list_queries:
            self.db.print_saved_query_names()
            sys.exit(0)

        # Save notes first, so the query can include them.
        if self.args.save_notes:
            self.save_notes(self.args)

        # Run the query and retrieve the notes.
        if self.args.remove_query:
            self.db.remove_saved_query(self.args.remove_query[0])
        start_time = time.time()
        if self.args.query:
            notes = self.db.run_saved_query(self.args.query[0])
        else:
            notes = self.db.run_query_from_args(self.args)
        elapsed = time.time() - start_time

        # Output notes sorted by notepath.
        paths = sorted(list(notes.keys()))

        # But output statistics and query info before outputting any notes.
        summary = QueryBuilder().summarize_query_from_args(self.args)
        if summary:
            path = self.db.get_file_path()
            size = get_readable_filesize(path)
            moddate = get_readable_moddate(path)
            print(summary)
            print('')
            print('DATABASE SIZE:    ', size)
            print('DATABASE MODIFIED:', moddate)
            print('WHEN SEARCHED:    ', timestamp_for_journal())
            print('SEARCH DURATION:  ', '{0:.4f}'.format(elapsed), 'seconds')
            print('NOTES FOUND:      ', '{:,}'.format(len(notes)))
            word_count = sum(notes[path].count_words() for path in paths)
            print('WORD COUNT:       ', '{:,}'.format(word_count))
            print('')
        else:
            print('NO SEARCH WAS MADE.')

        # Output notes last.
        for path in paths:
            if self.args.paths_only:
                print(path)
            else:
                print(notes[path])

    def save_notes_from_args(self, args: object) -> None:
        filepaths = self._flatten_arg(args.save_notes)
        self.save_notes_from_filepaths(filepaths)
    
    def save_notes_from_filepaths(self, filepaths: List[FilePath]) -> None:
        # Broken out to make testing a little easier.
        notes = {}
        print('SAVING NOTES INTO DATABASE FROM FILES:')
        number = 1

        for filepath in filepaths:
            prefix = '{:,}'.format(number) + '. '
            print(prefix, filepath)
            
            # Make one big dictionary of all the notes from all the files.
            # This is in case notes in different files have the same path,
            # as when the same note was exported in different queries. (Worst
            # case scenario should be that you'll end up with some notes with
            # the text repeated twice.)
            notes = get_notes_from_file(filepath, notes)

        self.db.save_notes(notes)

    def _init_options(self):
        t = ('For moving notes between text files and a SQLite database.'
             ' NOTE: All query options match whole words and ignore case,'
             ' so "cat" matches "CAT" but does not match "catalog".')
        parser = argparse.ArgumentParser(description=t)
        a = 'append'

        t = 'notepath 0.1'
        parser.add_argument('-v', '--version', action='version', version=t)
        
        t = 'Print the software license under which this program is released.'
        parser.add_argument('-L', '--license', help=t, action='store_true')

        t = 'Print SQLite settings.'
        parser.add_argument('-d', '--database', help=t, action='store_true')
        
        t = ('Print only the paths of matching notes. (If this option is not'
             ' specified, each note is printed in full.)')
        parser.add_argument('-P', '--paths-only', help=t, action='store_true')

        t = ('Print notes whose text has certain words or phrases. '
             'This program matches whole words and ignores case.')
        parser.add_argument('-t', '--text', help=t, action=a, nargs='+',
                            metavar='phrase')
        
        t = ('Print only notes whose path begins with "part" --- i.e.,'
             ' specify a "root" path for all matching notes.')
        parser.add_argument('-r', '--root', help=t, nargs=1, metavar='part')

        t = 'Print notes whose path has certain phrases.'
        parser.add_argument('-p', '--path', help=t, action=a, nargs='+',
                            metavar='phrase')

        t = 'Print notes that have specific tags (keywords).'
        parser.add_argument('-g', '--tag', help=t, action=a, nargs='+',
                            metavar='word')
        
        t = ('Print notes where field X has a certain value. Supports ten'
             ' operators (= == != <> < <= > >= has regexp). For example:'
             ' year>=1980 or lastname=asimov')
        parser.add_argument('-f', '--field', help=t, action=a, nargs='+',
                            metavar='X=Y')
        
        t = 'Give this query a name and save it for future re-use.'
        parser.add_argument('-n', '--name-query', help=t, nargs=1,
                            metavar='name')

        t = 'Find notes matching a named query already saved.'
        parser.add_argument('-q', '--query', help=t, nargs=1, metavar='name')

        t = 'List the names of all saved queries in alphabetical order.'
        parser.add_argument('-l', '--list-queries', help=t, action='store_true')

        t = 'Save notes from files into the database.'
        parser.add_argument('-s', '--save-notes', help=t, action=a, nargs='+',
                            metavar='path')
        
        t = 'Remove named query from the database.'
        parser.add_argument('-x', '--remove-query', help=t, nargs=1,
                            metavar='name')

        self.parser = parser


if __name__ == '__main__':
    Script().run()

