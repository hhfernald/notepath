#!/usr/bin/env python3
# The function annotations in this module require Python 3.5 or higher.

import re

from typing import Dict, List

from basics import Object, FilePath, NotePath

_TEXT_FILE_LINE_WIDTH = 80

class NoteError(Exception): pass

class Note(Object):
    def __init__(self, first_line: str = '') -> None:
        self.path        = ''
        self.textlines   = []
        self.tags        = []
        self.fields      = [] # each field should be a tuple: (name, value)
        self.directive   = ''
        self.line_number = 0
        
        # These variables are used only by _add_line().
        #
        # self.in_note is False until a header line (beginning with exactly
        # one backslash) is encountered. Non-header lines are ignored while
        # self.in_note is False --- so that any lines at the top of a file,
        # before the start of the first note in the file, are ignored. (This
        # means that the top of a note file can be reserved for temporary text
        # such as the terms of the query that produced the file, the number of
        # notes matching the query, when the query was run, etc.)
        #
        # self.in_text is False until a plain-text (non-header) line is
        # encountered (if self.in_note is True). The first blank line will
        # set self.in_text to True, but no lines are added to the note's text
        # until the first nonblank (non-header) line is found. Thus a note
        # may have only a header block and no text, but as long as a blank
        # line separates this block from the start of the next note, the
        # header line that begins the next note will be recognized as the
        # beginning of the next note.
        self.in_note = False
        self.in_text = False

        if first_line:
            self._add_line(first_line)

    def __eq__(self, other: 'Note') -> bool:
        if isinstance(other, Note):
            if (self.path == other.path
                and self.textlines == other.textlines
                and self.tags == other.tags
                and self.fields == other.fields):
                return True
            return False
    
    def __str__(self) -> str:
        parts = []

        # Create the note's header block.
        divider = '\\' + ('=' * (_TEXT_FILE_LINE_WIDTH - len('\\')))
        parts.append(divider + '\n')
        parts.append('\\ ' + self.path + '\n')
        parts.append('\\ @' + self.directive + '\n')
        parts.extend(self._write_tags_and_fields())
        parts.append('\n')

        # Create the note's text.
        for line in self.textlines:
            parts.append(line)
        
        # Return it all as a string.
        return ''.join(parts)

    def _field_or_tag_or_directive(self, line: str) -> None:
        if '=' in line:
            # Line is a single field (name = value).
            name, value = line.split('=', maxsplit=1)
            name, value = name.strip(), value.strip()
            
            # Value is a string. If it is numeric, it should be a float.
            try:
                value = float(value)
            except ValueError:
                pass            

            tup = (name, value)
            if tup not in self.fields:
                self.fields.append(tup)
        
        elif line.startswith('@'):
            # Line is a directive, telling us what to do with the record
            # when the note is re-imported into the database.
            self.directive = line[len('@'):].lstrip()

        else:
            # Line is one or more tags, separated by commas
            # or semicolons.
            line = line.replace(';', ',')
            tags = line.split(',')
            for tag in tags:
                if tag not in self.tags:
                    self.tags.append(tag.strip())

    def _add_line(self, line: str) -> bool:
        '''Add line to the note, or return False if it can't be added..
        
        More precisely: The line is a line of text read from (say) a text file.
        If the note has text in it, and the line signals the start of a new
        note, return False. Otherwise, update the note data as appropriate and
        return True.
        '''
        if line.startswith('\\'):
            if line.startswith('\\\\'):
                if self.in_note:
                    # If the line begins with two or more backslashes, count
                    # the line as text.
                    self.in_text = True
                    self.textlines.append(line)
                return True

            elif self.in_text:
                # If we've found a new header line after having found even a
                # single blank line, we've found the start of the next note and
                # therefore we cannot accept any more lines.
                return False

            else:
                # Remove initial backslash, see if anything is left.
                line = line[len('\\'):].strip()
                if not line:
                    # If the line is blank, ignore it. (This means you can have
                    # blank header lines between the initial divider line and
                    # the notepath line, or between any other pair of lines in
                    # the note's header block.)
                    return True
                else:
                    # Any header line (including a divider line) means we are
                    # in a header block.
                    #
                    # (CONSEQUENCE: This means that a note can have a header
                    # block with a divider line and NO PATH. Although the data-
                    # base table "notes" defines the "path" column as NOT NULL
                    # (meaning SQLite will throw an error if Note.path is None),
                    # SQLite will NOT throw an error if the path is a blank
                    # string ("" != None). So the database can contain a note
                    # whose path is "". On the other hand, this note cannot
                    # contain any tags or fields, because the first non-blank
                    # header line in the block that is not a divider line is
                    # always the path and never a list of tags or a field.)
                    self.in_note = True

                    # Check for a divider line. If the text after the backslash
                    # is just eight or more of the same non-alphanumeric ASCII
                    # character, then the line is a divider line. Ignore it.
                    c = line[0]
                    if c in '!@#$%^&*()_+-=`~[]{}\\|;:\'",<.>/?':
                        if len(line) >= 8 and len(line.replace(c, '')) == 0:
                            return True

                # The notepath comes first in the note's header block.
                if self.path:
                    self._field_or_tag_or_directive(line)
                else:
                    self.path = line
        elif self.in_note:
            self.in_text = True
            
            # If there are already lines in self.textlines, or if self.textlines
            # is empty but the line is not blank, add the line to self.textlines
            # --- in other words, do not begin self.text with a blank line.
            if self.textlines or line.strip():
                self.textlines.append(line)
        return True

    def _write_tags_and_fields(self) -> List[str]:
        '''Return list of parts of a text note's header block.'''
        parts = []
        
        # If the note has tags or fields, add a line with just a backslash
        # (to separate the notepath from the tags and fields).
        if self.tags or self.fields:
            parts.append('\\\n')

            # Write multiple tags to a line, but make sure no single line
            # is wider than the preferred maximum width of a line.
            if self.tags:
                taglines = []
                tagline = []
                sep = ', '
                width = 0
                for tag in self.tags:
                    if not tag:
                        continue
                    width += len(tag) + len(sep)
                    if width > _TEXT_FILE_LINE_WIDTH:
                        if tagline:
                            taglines.append(sep.join(tagline))
                        else:
                            # (In case the user manages to come up with a tag
                            # longer than the preferred maximum line width.)
                            taglines.append(tag)
                        tagline = []
                        width = 0
                    tagline.append(tag)
                if tagline:
                    taglines.append(sep.join(tagline))
                for line in taglines:
                    parts.append('\\ ' + line + '\n')

            # Pad each field name to the length of the longest name.
            length = 0
            for name, _ in self.fields:
                if len(name) > length:
                    length = len(name)
            
            # But if the longest name is unreasonably long,
            # pad shorter names to a more reasonable length.
            MAX_FIELD_NAME_LENGTH = 24
            length = min(length, MAX_FIELD_NAME_LENGTH)
            
            # Put each name/value pair on its own line. Do not split overly
            # wide names or values between lines.
            for name, value in self.fields:
                p = ['\\ ', name.ljust(length), ' = ', str(value), '\n']
                parts.append(''.join(p))
        
        return parts

    def clone(self) -> 'Note':
        note = Note()
        note.path = self.path
        note.textlines = self.textlines
        note.tags = self.tags
        note.fields = self.fields
        return note

    def merge(self, other: 'Note') -> None:
        if not isinstance(other, Note):
            raise NoteError('cannot merge notes with non-notes')
        if self.path != other.path:
            raise NoteError('cannot merge notes with different notepaths')

        # When notes with the same notepath are merged, sometimes the text will
        # be the same in both notes. Thus there is the risk that notes will
        # occasionally be resaved to the database with its text repeated. We can
        # alleviate this risk by refusing to merge the notes' texts if they have
        # EXACTLY the same text. (If the texts differ by so much as a single
        # space, though, then you may see this "note bloat" from time to time.)
        if self.textlines != other.textlines:
            self.textlines.append('\n')
            self.textlines.extend(other.textlines)
        
        for tag in other.tags:
            if tag not in self.tags:
                self.tags.append(tag)
        
        for name, value in other.fields:
            # A field name can occur more than once in a note, but each
            # combination of field name and field value should be unique
            # within the note.
            if (name, value) not in self.fields:
                self.fields.append((name, value))

    def set_from_string(self, multiline_string: str) -> str:
        '''Set note data from a string; return unused string portion.
        
        This splits the string up into lines and keeps adding lines to the
        note until a line is found that would begin the next note, at which
        point the line, and all of the rest of the lines, are returned as a
        rejoined string, which can be passed to the set_from_string() method
        of the next Note object.
        '''
        lines = multiline_string.splitlines(keepends=True)
        for i, line in enumerated(lines):
            if not self._add_line(line):
                return ''.join(lines[i:])

    def read(self, file_handle) -> str:
        '''Set note data from a text file; return first line of next note.'''
        while True:
            line = file_handle.readline()
            if not line:
                # A blank line at least ends with a newline character;
                # an empty string indicates the end of the file.
                return line
            if not self._add_line(line):
                return line

    def write(self, file_handle):
        '''Write note data in text format to the file handle.'''
        s = str(self)
        file_handle.write(s)

    def set_text(self, text: str):
        '''Set note text from the text pulled from the database.
        
        This sets ONLY the text (not the path, tags, or fields),
        unlike set_from_string().
        '''
        self.textlines = []
        lines = text.splitlines(keepends=True)
        while len(lines[0].strip()) == 0:
            lines.pop(0)
        self.textlines = lines
    
    def get_text(self) -> str:
        return ''.join(self.textlines)

    def get_field_values(self, field_name: str) -> List[str]:
        '''Return list of values assigned to the field name (case ignored).'''
        values = []
        sought = field_name.lower()
        for name, value in self.fields:
            if name.lower() == sought:
                values.append(value)
        return values

    def count_words(self) -> int:
        return sum([len(re.findall(r'\w+', line)) for line in self.textlines])


def get_notes_from_file(filepath: FilePath,
                        notes: Dict[NotePath, Note] = None,
                        suppress_warnings: bool = False
                        ) -> Dict[NotePath, Note]:
    if not notes:
        notes = {}
        note = Note()
    try:
        with open(filepath, mode='r', encoding='utf-8') as file:
            while True:
                line = note.read(file)
                if note.path in notes:
                    if not suppress_warnings:
                        t = 'WARNING: notepath used more than once: '
                        self._error(t + note.path)
                    notes[note.path].merge(note)
                else:
                    notes[note.path] = note
                if line:
                    note = Note(line)
                else:
                    break
    except FileNotFoundError:
        pass
    return notes

