#!/usr/bin/env python3

import configparser
import itertools
import os
import sys
import unittest

from sqlite3 import IntegrityError
from typing import Dict, List, Tuple, Union

p = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
p = os.path.join(p, 'notepath')
if p not in sys.path:
    sys.path.append(p)

from basics import get_data_path, NotePath, sort_notepaths
from database import Database, DatabaseError
from note import Note, get_notes_from_file
from querybuilder import QueryBuilder

DATABASE_PATH = get_data_path('test.sqlite3')
ARCHIVE_PATH  = get_data_path('test_archive.nparch')

class TestSearch():
    def __init__(self):
        self.path_terms = []
        self.text_terms = []
        self.tag_terms = []
        self.field_terms = []
        self.matches = []
    
    def _load_key(self, section: Dict, key: str) -> None:
        if key in section:
            # Whenever we're supposed to search for more than one path,
            # text phrase, tag, or field, each term to search for must
            # appear on its own line in the INI file.
            setattr(self, key, section[key].splitlines())
    
    def load_ini_section(self, section: Dict) -> None:
        keys = ['path_terms', 'text_terms', 'tag_terms',
                'field_terms', 'matches']
        for key in keys:
            self._load_key(section, key)
        

class TestDataLoader():
    '''Load notes (and search criteria) from test files.'''
    def __init__(self) -> None:
        self.path = os.path.dirname(__file__)
    
    def _path(self, basename: str, extension: str) -> str:
        if not basename.endswith(extension):
            basename += extension
        path = os.path.join(self.path, basename)
        return path
    
    def load_notes(self, basename: str) -> Dict[NotePath, Note]:
        path = self._path(basename, '.nptext')
        return get_notes_from_file(path, suppress_warnings = True)
    
    def load_searches(self, basename: str) -> List[TestSearch]:
        path = self._path(basename, '.ini')
        searches = []
        config = configparser.ConfigParser()
        config.read(path)
        for section in config.sections():
            search = TestSearch()
            search.load_ini_section(config[section])
            searches.append(search)
        return searches

class Test_Database(unittest.TestCase):
    def _delete_archive_file(self) -> None:
        if os.path.exists(ARCHIVE_PATH):
            os.remove(ARCHIVE_PATH)
    
    def _save_and_verify_note(self,
                              db: Database,
                              note: Note,
                              merged: bool = False
                              ) -> None:
        notes = {note.path: note}
        db.save_notes(notes)
        notes = db.get_notes_by_path(note.path)
        self.assertEqual(len(notes), 1)
        self.assertTrue(note.path in notes)
        
        # If it is expected that the note being saved will be merged with a
        # note in the database, then we cannot expect the note retrieved to
        # be the same as the note saved.
        if not merged:
            self.assertTrue(notes[note.path] == note)

    def _verify_note_archived(self, old_note: Note) -> None:
        notes = get_notes_from_file(ARCHIVE_PATH)
        archived_note = notes[old_note.path]
        self.assertEqual(archived_note.textlines, old_note.textlines)
        self.assertEqual(archived_note.tags, old_note.tags)

        # (The archived note will have one field that the old note lacks,
        # namely '{archive_date}'.)
        name = '{archive_date}'
        self.assertEqual(len(archived_note.fields), len(old_note.fields) + 1)

        names = [field[0] for field in archived_note.fields]
        self.assertTrue(name in names)

        names = [field[0] for field in old_note.fields]
        self.assertFalse(name in names)

        # Make sure that, other than the archive date, the note archived is
        # the same as the old note:
        #
        # (1) Remove the archive date.
        fields = [f for f in archived_note.fields if f[0] != name]
        archived_note.fields = fields
        
        # (2) Compare.
        self.assertEqual(old_note, archived_note)

    def test_01_set_up_database(self):
        '''Verify notes retrieved == notes saved.'''
        if os.path.exists(DATABASE_PATH):
            os.remove(DATABASE_PATH)
        
        loader = TestDataLoader()
        loaded_notes = loader.load_notes('test_1')
        
        db = Database(DATABASE_PATH, ARCHIVE_PATH)
        db.save_notes(loaded_notes)
        
        for notepath in loaded_notes:
            loaded_note = loaded_notes[notepath]
            saved_notes = db.get_notes_by_path(notepath)
            saved_note = saved_notes[notepath]
            self.assertEqual(loaded_note, saved_note)
    
    def test_02_ini_searches(self):
        loader = TestDataLoader()
        searches = loader.load_searches('test_1')
        db = Database(DATABASE_PATH, ARCHIVE_PATH)
        qb = QueryBuilder()
        for search in searches:
            expected_paths = sort_notepaths(search.matches)
            sql = qb.build_sql_from_lists(search.path_terms, search.text_terms,
                                          search.tag_terms, search.field_terms)
            saved_notes = db._get_notes(sql)
            actual_paths = sort_notepaths(list(saved_notes.keys()))
            self.assertListEqual(expected_paths, actual_paths)

    def test_03_inserting_note_with_same_notepath_raises_error(self):
        loader = TestDataLoader()
        loaded_notes = loader.load_notes('test_1')
        notepath = list(loaded_notes.keys())[0]
        loaded_note = loaded_notes[notepath]

        db = Database(DATABASE_PATH, ARCHIVE_PATH)
        notetext = 'This note has a duplicate notepath.'
        notetag = 'test'

        # See if we can bypass our own code, and force a note into the
        # database with the same path as a note already there. (This needs
        # to throw an exception; notes.path should have been defined as
        # UNIQUE when the notes table was created.)
        cursor = db.connection.cursor()
        sql = 'INSERT INTO notes (path, text) VALUES (?, ?)'
        self.assertRaises(IntegrityError, cursor.execute,
                          sql, (notepath, notetext))
        cursor.close()
    
    def test_04_edit_and_resave_notes(self) -> None:
        db = Database(DATABASE_PATH, ARCHIVE_PATH)
        note = Note()
        
        initial_path   = 'some/path'
        note.path      = initial_path
        note.textlines = ['Some text.']
        note.tags      = ['test']
        note.directive = 'merge'
        
        # Verify that the note isn't in the database, then save the note.
        notes = db.get_notes_by_path(note.path)
        self.assertEqual(len(notes), 0)
        self._save_and_verify_note(db, note)
        
        # TEST DIRECTIVE: @replace:
        old_note = db.get_notes_by_path(note.path)[note.path]
        note.textlines = ['Text changed.']
        note.directive = 'replace'
        self._delete_archive_file()
        self._save_and_verify_note(db, note)
        self._verify_note_archived(old_note)
        
        # TEST DIRECTIVE: @rename <new path>:
        # (The note's path is still initial_path.)
        old_note = db.get_notes_by_path(note.path)[note.path]
        new_path = 'other path'
        note.directive = 'rename ' + new_path
        self._delete_archive_file()
        self._save_and_verify_note(db, note)
        
        # Verify that the note with the initial_path is gone from the database.
        notes = db.get_notes_by_path(initial_path)
        self.assertEqual(len(notes), 0)

        # Verify that the note with the new_path is present in the database.
        notes = db.get_notes_by_path(new_path)
        self.assertEqual(len(notes), 1)
        
        # Verify that the note with the initial_path was archived.
        self._verify_note_archived(old_note)

        # TEST DIRECTIVE: @newpath:
        old_note = db.get_notes_by_path(note.path)[note.path]
        note.directive = 'newpath ' + initial_path
        self._delete_archive_file()
        self._save_and_verify_note(db, note)
        
        # Verify that note with new_path is gone from database.
        notes = db.get_notes_by_path(new_path)
        self.assertEqual(len(notes), 0)
        
        # Verify that the note with the initial_path is present in the database.
        notes = db.get_notes_by_path(initial_path)
        self.assertEqual(len(notes), 1)

        # Verify that the note with the new_path was archived.
        self._verify_note_archived(old_note)

        # TEST DIRECTIVE: @add (should throw an exception if note exists)
        old_note = db.get_notes_by_path(note.path)[note.path]
        phrases = [note.textlines[0].strip(), 'Note to be merged.']
        note.textlines = [phrases[1]]
        note.directive = 'add'
        self._delete_archive_file()
        self.assertRaises(DatabaseError, self._save_and_verify_note,
                          db, note, merged=True)
        
        # TEST DIRECTIVE: @merge
        note.directive = 'merge'
        self._save_and_verify_note(db, note, merged=True)
        notes = db.get_notes_by_path(note.path)
        text = notes[note.path].get_text()
        for phrase in phrases:
            self.assertTrue(phrase in text)
        self._verify_note_archived(old_note)
        
        # TEST DIRECTIVE: @delete
        old_note = db.get_notes_by_path(note.path)[note.path]
        note.directive = 'delete'
        notes = {note.path: note}
        self._delete_archive_file()
        db.save_notes(notes)
        notes = db.get_notes_by_path(note.path)
        self.assertEqual(len(notes), 0)
        self._verify_note_archived(old_note)
    

class Test_Note(unittest.TestCase):
    def test_99_adding_metadata_line_to_note_in_text_mode_fails(self):
        # [_] TODO:
        # It doesn't matter if the note has text or not. If the note has
        # received no text lines except blank ones, the note will have no
        # text but will still be "in text mode," so that the note will
        # reject the next metadata line it receives, and the note object's
        # content will be the same after the rejection as it was before.
        pass
    
    def test_99_notepath_is_populated_before_tags_or_fields(self):
        # [_] TODO:
        pass
    
    def test_99_add_line(self):
        # [_] TODO:
        # Keep adding lines to a note.
        # Ensure that note path, tags, fields, and text are populated
        #     when they should be.
        # When the note has text and you pass a backslash line, the
        #     note should always reject it.
        pass

def tearDownModule():
    # Clean up after yourself. Delete the database and archive test files.
    files = [DATABASE_PATH, ARCHIVE_PATH]
    for file in files:
        if os.path.exists(file):
            os.remove(file)


if __name__ == '__main__':
    unittest.main()

