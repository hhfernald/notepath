#!/usr/bin/env python3
# The function annotations in this module require Python 3.5 or higher.

from typing import Dict
from basics import FilePath, NotePath, Object, get_data_path, sort_notepaths
from note import Note
from utils import timestamp_for_logging

ARCHIVE_FILENAME = 'archive.nparch'
ARCHIVE_FIELD = '{archive_date}'

class Archiver(Object):
    '''Appends old records from the database to the archive file.
    
    The archive file is really just a text file in "notepath format",
    but with an additional "{archive_date}" field assigned to each
    note in the file.
    
    Whenever a note in the database is to be changed or deleted, it is
    first exported to the archive file as a backup.
    '''
    def __init__(self, path: FilePath = None) -> None:
        if not path:
            path = ARCHIVE_FILENAME
        self.path = get_data_path(path)
    
    def append_notes(self, notes: Dict[NotePath, Note]) -> None:
        notepaths = sort_notepaths(list(notes.keys()))
        with open(self.path, mode='a', encoding='utf-8') as file:
            # Do not modify the original notes; clone each note and add the
            # {archive_date} field to the clone.
            for notepath in notepaths:
                clone = notes[notepath].clone()
                name, value = ARCHIVE_FIELD, timestamp_for_logging()
                clone.fields.append((name, value))
                clone.write(file)


