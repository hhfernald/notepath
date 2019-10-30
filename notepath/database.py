#!/usr/bin/env python3
# The function annotations in this module require Python 3.5 or higher.

import re
import sqlite3

from typing import Dict, List, Union

from basics import (FilePath, NotePath, Object, sort_notepaths,
                    SQLSelectStatement)
from archiver import Archiver
from note import Note
from querybuilder import QueryBuilder

# Type aliases
NoteID = int

DEFAULT_DATABASE_FILENAME = 'notes.sqlite3'


def _regexp(pattern, text: str) -> bool:
    return bool(re.search(pattern, text))

class DatabaseError(Exception): pass

class Database(Object):
    def __init__(self, db_path: FilePath, archive_path: FilePath = None) -> None:
        # Permitting an alternative filename for the database allows
        # us to create a dummy database for testing purposes.
        if not db_path:
            t = 'cannot create or open a database without a filepath'
            raise FileNotFoundError(t)
        self.db_path = db_path
        
        # Also permit an alternative path for the archive file.
        self._archive_path = archive_path
        
        self.connection = sqlite3.connect(self.db_path)
        self.connection.create_function("REGEXP", 2, _regexp)
        try:
            self.create_tables()
            self.create_indexes()
        except sqlite3.OperationalError:
            # While writing this script, sometimes I'd doublecheck the contents
            # of the database with another program, e.g., DB Browser for SQLite,
            # and try to run this script again without closing the program, and
            # the "database is locked" error would come up.
            t = "Database is locked (apparently another program is using it)."
            self._error(t)
            sys.exit(1)

    def _create_index(self, cursor, clause: str) -> None:
        t = 'CREATE INDEX IF NOT EXISTS ' + clause + ';'
        cursor.execute(t)

    def _get_notes(self, sql: SQLSelectStatement) -> Dict[NotePath, Note]:
        # If the SQL string is blank, return an empty dict.
        if not sql.strip():
            return {}
        
        cursor = self.connection.cursor()

        # Get a list of the IDs of all the notes to gather.
        cursor.execute(sql)
        records = cursor.fetchall()
        note_ids = [row[0] for row in records]
        notes = self._get_notes_by_id(note_ids, cursor)
        
        # Each method that opens a cursor should close the cursor.
        cursor.close()
        return notes

    def _get_notes_by_id(self,
                         note_ids: List[NoteID],
                         cursor
                         ) -> Dict[NotePath, Note]:
        notes = {}
        idlist = ', '.join(str(i) for i in note_ids)
        
        # Request note paths and texts.
        sql = 'SELECT id, path, text FROM notes WHERE id in (' + idlist + ');'
        cursor.execute(sql)
        while True:
            record = cursor.fetchone()
            if record == None:
                break
            
            note_id, path, text = record[0], record[1], record[2]
            
            # We should (usually) have exactly one note for each notepath
            # pulled from the database.
            if path not in notes:
                notes[path] = Note()
                notes[path].path = path

            # If the database should have two or more notes with the same
            # notepath, merge the notes together. (We don't have a second
            # note to pass to the first note's merge() method; we only have
            # the second note's text, so we merge that directly here.)
            note = notes[path]
            if note.textlines:
                text = ''.join(note.textlines) + '\n' + text
            note.set_text(text)

            # Any note copied from the database (and later edited) should
            # REPLACE the original record when re-imported (unless the user
            # overrides the directive, of course).
            note.directive = 'replace'

        # Request note tags and fields.
        # (Use a LEFT OUTER JOIN because the notes table should have ONE row
        # for each note, but the tags table may have zero, one, two, or more
        # rows, and we want ALL of the tag-and-field rows to be returned.)
        sql = ('SELECT notes.path, tags.name, tags.value'
               ' FROM notes LEFT OUTER JOIN tags ON notes.id = tags.id'
               ' WHERE notes.id in (' + idlist + ');')
        cursor.execute(sql)
        while True:
            row = cursor.fetchone()
            if row == None:
                break
            
            # Note that we don't have a second note to merge with the note
            # already in the dictionary; we're simply pulling up any tags and
            # values associated with the note ID and adding them to the note
            # associated with the notepath.
            path, name, value = row[0], row[1], row[2]
            note = notes[path]
            if value is None:
                if name is not None:
                    if name not in note.tags:
                        note.tags.append(name)
            else:
                if (name, value) not in note.fields:
                    note.fields.append((name, value))

        return notes

    def _archive_and_delete_notes(self,
                                  notepaths: Union[NotePath, List[NotePath]],
                                  cursor
                                  ) -> None:
        if isinstance(notepaths, NotePath):
            notepaths = [notepaths]

        # Archive the notes before deleting them from the database.
        note_ids = self._get_note_ids(notepaths, cursor)
        archiver = Archiver(self._archive_path)
        old_notes = self._get_notes_by_id(note_ids, cursor)
        if old_notes:
            archiver.append_notes(old_notes)

        self._delete_notes_by_path(notepaths, cursor)

    def _delete_notes_by_path(self,
                      notepaths: Union[NotePath, List[NotePath]],
                      cursor
                      ) -> None:
        note_ids = self._get_note_ids(notepaths, cursor)
        idlist = ', '.join(str(i) for i in note_ids)
        sql = 'DELETE FROM notes WHERE id IN (' + idlist + ');'
        cursor.execute(sql)
        sql = 'DELETE FROM tags WHERE id IN (' + idlist + ');'
        cursor.execute(sql)

    def _get_note_id(self, notepath: NotePath, cursor) -> Union[NoteID, None]:
        sql = 'SELECT id FROM notes WHERE path = ?;'
        cursor.execute(sql, (notepath,))
        record = cursor.fetchone()
        return record[0] if record else None

    def _get_note_ids(self, notepaths: Union[NotePath, List[NotePath]], cursor
                  ) -> List[NoteID]:
        if isinstance(notepaths, NotePath):
            notepaths = [notepaths]
        paths = [QueryBuilder.escape(path) for path in notepaths]
        p = ', '.join(paths)
        sql = 'SELECT id FROM notes WHERE path in (' + p + ');'
        cursor.execute(sql)
        ids = []
        while True:
            record = cursor.fetchone()
            if record:
                ids.append(record[0])
            else:
                return ids

    def _insert_tags(self, note_id: NoteID, note: Note, cursor) -> None:
        sql = 'DELETE FROM tags WHERE id = ?;'
        cursor.execute(sql, (note_id,))

        for tag in note.tags:
            sql = 'INSERT INTO tags (id, name, value) VALUES (?, ?, NULL);'
            cursor.execute(sql, (note_id, tag))

        for name, value in note.fields:
            sql = 'INSERT INTO tags (id, name, value) VALUES (?, ?, ?);'
            cursor.execute(sql, (note_id, name, value))

    def _insert_note(self, note: Note, cursor) -> None:
        sql = 'INSERT INTO notes (path, text) VALUES (?, ?);'
        cursor.execute(sql, (note.path, note.get_text()))
        note_id = cursor.lastrowid
        self._insert_tags(note_id, note, cursor)

    def _replace_note(self, note: Note, cursor) -> None:
        '''Archive existing note, then replace it with the note passed.
        
        (If there is no existing note, the new note is simply inserted.)
        '''
        self._archive_and_delete_notes(note.path, cursor)
        self._insert_note(note, cursor)

    def _insert_or_merge_note(self, note: Note, cursor) -> None:
        old_notes = self.get_notes_by_path(note.path)
        if old_notes:
            old_note = old_notes[note.path]
            old_note.merge(note)
            note = old_note
            self._archive_and_delete_notes(note.path, cursor)
        self._insert_note(note, cursor)

    def _save_note(self, note: Note, cursor) -> None:
        directive = note.directive
        if not directive:
            # If no directive was specified, and a note with the same path
            # already exists, the safest course is to merge the new note
            # with the existing note, so that no data is lost. (We DON'T
            # rename the note and save it as a new record, because that
            # will break the connection between the text-file note and
            # the database note. As always, it is best to rerun queries
            # and refresh the text files being edited after notes are
            # written to the database.)
            directive = 'merge'
        if directive == 'replace':
            self._replace_note(note, cursor)
        elif directive == 'delete':
            self._archive_and_delete_notes(note.path, cursor)
        elif directive == 'merge':
            self._insert_or_merge_note(note, cursor)
        elif directive == 'add':
            old_notes = self.get_notes_by_path(note.path)
            if old_notes:
                t = 'Cannot add note; path is in use: ' + note.path
                self.connection.commit()
                raise DatabaseError(t)
            else:
                self._insert_note(note, cursor)
        else:
            words = directive.split(maxsplit=1)
            if len(words) > 1 and words[0] in ['rename', 'newpath']:
                self._archive_and_delete_notes(note.path, cursor)
                new_path = words[1].strip()
                note.path = new_path
                self._insert_or_merge_note(note, cursor)
            else:
                self._error('Unrecognized directive:', directive)
                self._error('--- adding or replacing note:', note.path)
                self._replace_note(note, cursor)
    
    def print_sqlite_info(self):
        cursor = self.connection.cursor()

        query = 'select sqlite_version();'
        cursor.execute(query)
        version = cursor.fetchone()[0]
        print("Database engine: SQLite [version", version + '].')

        query = 'pragma compile_options;'
        cursor.execute(query)
        record = cursor.fetchall()
        print("Available options:")
        for item in record:
            print('---', item)

        cursor.close()
    
    def create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute('BEGIN TRANSACTION;')
        
        t = ('CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY,'
             ' path TEXT NOT NULL UNIQUE,'
             ' text TEXT);')
        cursor.execute(t)

        # Most field values will be strings or NULL, but if we give the "value"
        # column what SQLite calls "REAL affinity"[1], then numeric values are
        # stored as floating-point (and can be compared numerically) while text
        # values that can't be interpreted as numbers are still stored (and
        # compared) as text.
        #
        # [1]: https://www.sqlite.org/datatype3.html
        t = ('CREATE TABLE IF NOT EXISTS tags (id INTEGER,'
             ' name TEXT,'
             ' value REAL);')
        cursor.execute(t)
        
        t = ('CREATE TABLE IF NOT EXISTS config (category TEXT,'
             ' name TEXT,'
             ' value TEXT);')
        cursor.execute(t)
        
        cursor.execute('END TRANSACTION;')
        
        # Each method that opens a cursor should close it.
        cursor.close()

    def create_indexes(self):
        cursor = self.connection.cursor()
        cursor.execute('BEGIN TRANSACTION;')

        self._create_index(cursor, 'path_index ON notes (path)')
        self._create_index(cursor, 'name_index ON tags (name)')
        self._create_index(cursor, 'value_index ON tags (value)')
        self._create_index(cursor, 'config_index ON config (category, name)')
        
        cursor.execute('END TRANSACTION;')
        cursor.close()

    def get_file_path(self):
        return self.db_path

    def save_query(self, query_name: str, sql: SQLSelectStatement) -> None:
        if not query_name or not sql:
            return

        self.remove_saved_query(query_name)

        cursor = self.connection.cursor()
        sql = "INSERT INTO config (category, name, value) VALUES (?, ?, ?);"
        cursor.execute(sql, ('queries', query_name, sql))
        cursor.close()
    
    def remove_saved_query(self, query_name: str) -> None:
        if not query_name:
            return

        cursor = self.connection.cursor()
        sql = "DELETE FROM config WHERE category = 'queries' AND name = ?;"
        cursor.execute(sql, (query_name,))
        cursor.close()
    
    def print_saved_query_names(self) -> None:
        sql = "SELECT name FROM config WHERE category = 'queries';"
        cursor = self.connection.cursor()
        cursor.execute(sql)
        
        print('QUERIES SAVED:')
        namecount = 0
        for row in cursor:
            print('-', '"' + row[0]) + '"'
            namecount += 1
        cursor.close()
        print('One query' if namecount == 1 else namecount, 'queries')

    def run_saved_query(self, query_name: str) -> Dict[NotePath, Note]:
        '''Run the stored query given and return the notes selected.'''
        sql = ("SELECT value FROM config WHERE category = 'queries'"
               " AND name = ?;")
        cursor = self.connection.cursor()
        cursor.execute(sql, (query_name,))
        record = cursor.fetchone()
        if record:
            sql = record[0]
            notes = self._get_notes(sql)
        cursor.close()
        return notes
    
    def run_query_from_args(self, args: object) -> Dict[NotePath, Note]:
        qb = QueryBuilder()
        sql = qb.build_sql_from_args(args)
        if args.name_query:
            if sql:
                self.save_query(args.name_query[0], sql)
            else:
                self._error('cannot save query with no parameters')
        return self._get_notes(sql)

    def get_notes_by_path(self,
                          notepaths: Union[NotePath, List[NotePath]]
                          ) -> Dict[NotePath, Note]:
        cursor = self.connection.cursor()
        if isinstance(notepaths, NotePath):
            notepaths = [notepaths]
        note_ids = self._get_note_ids(notepaths, cursor)
        notes = self._get_notes_by_id(note_ids, cursor)
        cursor.close()
        return notes

    def save_notes(self, notes: Dict[NotePath, Note]):
        cursor = self.connection.cursor()
        cursor.execute('BEGIN TRANSACTION;')

        notepaths = sort_notepaths(list(notes.keys()))
        for notepath in notepaths:
            self._save_note(notes[notepath], cursor)

        cursor.execute('END TRANSACTION;')
        cursor.close()

    def close(self) -> None:
        self.connection.commit()
        self.connection.close()
    

