#!/usr/bin/env python3
# The function annotations in this module require Python 3.5 or higher.

import re

from typing import List, Tuple

from basics import Object, SQLSelectStatement

# Type aliases
SQLFragment = str
ErrorMessage = str


class QueryBuilder(Object):
    '''Convert command-line arguments into SQL SELECT statements.'''
    @classmethod
    def escape(cls, value: str) -> SQLFragment:
        '''Sanitize the given value, making it safe to include in SQL.'''
        # If the value is already enclosed in single quotes, it's probably OK,
        # but make sure by scanning it for more single quotes.
        if value.startswith("'") and value.endswith("'"):
            parts = re.split(r"('+)", value[1:-1])
            for i, part in enumerate(parts):
                # Any instance of an odd number of single quotes will have
                # an extra single quote appended. This is more about keeping
                # the database safe than trying to make the value make sense.
                if part.startswith("'") and len(part) % 2:
                    parts[i] += "'"
            value = ''.join(parts)
        else:
            value = value.replace("'", "''")
        return "'" + value + "'"
    
    def _regexify(self, text: str) -> str:
        """Convert a literal-text search pattern into a regular expression.
        """
        # Certain punctuation marks and other special characters
        # should be "escaped" so that they are interpreted as
        # literal characters, not regular-expression codes.
        pattern = text.replace('\\', '\\\\')
        specials = '^$.|?*+/()[]{}'
        pattern = ''.join('\\'+c if c in specials else c for c in pattern)
        
        # Each space in the text sought should match any span
        # of whitespace in the text being searched.
        pattern = re.sub(r'\s+', r'\\s+', pattern)

        # The text sought should always match whole words.
        if re.search(r'\w', pattern[0]):
            pattern = r'\b' + pattern
        if re.search(r'\w', pattern[-1]):
            pattern = pattern + r'\b'
    
        # Ignore case.
        pattern = r'(?i)' + pattern
    
        return pattern
    
    def _parse_split(self,
                     field: str,
                     pattern: str,
                     regexify: bool = False
                     ) -> List[SQLFragment]:
        '''Split field string into [name, op, value] and return the list.
        
        Both the field name and the field value are escaped --- enclosed in
        single quotes, with embedded single quotes doubled --- to make them
        safe to include in a SQL statement.
        '''
        terms = re.split(pattern, field)
        NAME, VALUE = 0, 2
        if len(terms) > 3:
            terms[VALUE] = ''.join(terms[2:])
        
        if len(terms) == 3:
            terms[NAME]  = terms[NAME].strip()
            terms[VALUE] = terms[VALUE].strip()
            if terms[NAME]:
                terms[NAME] = self.escape(terms[NAME])
            if terms[VALUE]:
                if regexify:
                    terms[VALUE] = self._regexify(terms[VALUE])

                # If value is a number, don't enclose it in quotes.
                v = None
                try:
                    v = int(terms[VALUE])
                except ValueError:
                    try:
                        v = float(terms[VALUE])
                    except ValueError:
                        pass
                if v is None:
                    terms[VALUE] = self.escape(terms[VALUE])
        return terms
    
    def _parse_field_op(self, field: str) -> Tuple[SQLFragment, ErrorMessage]:
        '''Convert field string to SQL snippet; return SQL and error message.
        '''
        operators = ['=', '==', '!=', '<>', '<', '<=', '>', '>=']
        terms = self._parse_split(field, r'([=!<>]+)')
        if not terms[0] or not terms[2]:
            return ('', '')
        
        if len(terms) == 3:
            if terms[1] in operators:
                name, op, value = terms[0], terms[1], terms[2]
                sql = "name = " + name + " and value " + op + " " + value
                return (sql, '')
            else:
                return ('', 'BAD FIELD: OPERATOR NOT SUPPORTED: ' + field)
        return ('', '')
    
    def _parse_field_regexp(self, field: str)->Tuple[SQLFragment, ErrorMessage]:
        '''Convert field string to SQL snippet; return SQL and error message.
        
        If the user specified REGEXP as the operator, then the field value is
        presumed to be a regular expression, and run through self.escape()
        but not processed further.
        '''
        terms = self._parse_split(field, r'((?i) re )')
        if len(terms) == 3:
            name, op, value = terms[0], 'REGEXP', terms[2]
            sql = "name = " + name + " and value " + op + " " + value
            return (sql, '')
        return ('', '')
    
    def _parse_field_has(self, field: str) -> Tuple[SQLFragment, ErrorMessage]:
        '''Convert field string to SQL snippet; return SQL and error message.
        
        If the user specified HAS as the operator, then the second item is
        presumed NOT to be a regular expression but should be converted into
        one. Specifically, the second item is taken as one or more whole words
        to be matched in the field value. Spans of whitespace within the item
        will match spans of whitespace within the field value, and case will be
        ignored.
        '''
        terms = self._parse_split(field, r'((?i) has )', regexify=True)
        if len(terms) == 3:
            name, op, value = terms[0], 'REGEXP', terms[2]
            sql = "name = " + name + " and value " + op + " " + value
            return (sql, '')
        return ('', '')
    
    def _parse_field(self, field: str) -> Tuple[SQLFragment, ErrorMessage]:
        '''Convert field string to SQL snippet; return SQL and error message.
        '''
        if not field:
            return '', ''
        
        sql, error = self._parse_field_op(field)
        if sql or error:
            return sql, error
        
        sql, error = self._parse_field_regexp(field)
        if sql or error:
            return sql, error
    
        sql, error = self._parse_field_has(field)
        if sql or error:
            return sql, error
        
        return ('', 'BAD FIELD: OPERATOR NOT FOUND: ' + field)

    def _parse_tag(self, tag: str) -> SQLFragment:
        '''Convert tag string to SQL clause to find tag; return the clause.'''
        tag = tag.strip()
        if tag:
            sql = "name = " + self.escape(tag) + " and value is NULL"
        else:
            sql = ''
        return sql
    
    def _parse_path(self, path: str) -> SQLFragment:
        path = path.strip()
        sql = None
        STARTING_ANCHOR = '^'
        root = True if path.startswith(STARTING_ANCHOR) else False
        prefix = 'path REGEXP '
        if path:
            if root:
                path = path[len(STARTING_ANCHOR):]
            term = self.escape(self._regexify(path))
            if root:
                find = "'(?i)"
                replacement = find + STARTING_ANCHOR
                term = term.replace(find, replacement)
            sql = prefix + term
        return sql
    
    def _parse_text(self, text: str) -> SQLFragment:
        text = text.strip()
        if text:
            sql = "text REGEXP " + self.escape(self._regexify(text))
        return sql
    
    def _make_tags_clauses(self,
                           fields: List[str],
                           tags: List[str]
                           ) -> List[SQLFragment]:
        tags_clauses = []
        if fields: # to guard against TypeError if fields == None.
            for field in fields:
                sql, error = self._parse_field(field)
                if error:
                    self._error(error)
                elif sql:
                    tags_clauses.append(sql)
        if tags: # to guard against TypeError if tags == None.
            for tag in tags:
                sql = self._parse_tag(tag)
                if sql:
                    tags_clauses.append(sql)
        return tags_clauses
    
    def _make_notes_clauses(self,
                            paths: List[str],
                            texts: List[str]
                            ) -> List[SQLFragment]:
        notes_clauses = []
        if paths:
            for path in paths:
                sql = self._parse_path(path)
                if sql:
                    notes_clauses.append(sql)
        if texts:
            for text in texts:
                sql = self._parse_text(text)
                if sql:
                    notes_clauses.append(sql)
        return notes_clauses
    
    def _make_query(self,
                    notes_clauses: List[str],
                    tags_clauses: List[str]
                    ) -> SQLSelectStatement:
        clauses = ([('notes', clause) for clause in notes_clauses]
                   + [('tags', clause) for clause in tags_clauses])
        middle = ' AND id IN ('
        s = []
        if clauses:
            last_table, last_clause = clauses.pop()
            for table, clause in clauses:
                s.append('SELECT DISTINCT id FROM ')
                s.append(table)
                s.append(' WHERE ')
                s.append(clause)
                s.append(middle)
            s.append('SELECT DISTINCT id FROM ')
            s.append(last_table)
            s.append(' WHERE ')
            s.append(last_clause)
            s.append(')' * len(clauses))
        sql = ''.join(s)
        return sql

    def _flatten_args(self, args: object) -> Tuple[List, List, List, List]:
        items = [self._flatten_arg(args.path)]
        items.append(self._flatten_arg(args.text))
        items.append(self._flatten_arg(args.tag))
        items.append(self._flatten_arg(args.field))
        
        lists = [item if item != None else [] for item in items]
        if args.root:
            lists[0].append('^' + args.root[0])
        return tuple(lists)

    def build_sql_from_lists(self,
                             paths: List[str],
                             texts: List[str],
                             tags: List[str],
                             fields: List[str]
                             ) -> SQLSelectStatement:
        tags_clauses = self._make_tags_clauses(fields, tags)
        notes_clauses = self._make_notes_clauses(paths, texts)
        sql = self._make_query(notes_clauses, tags_clauses)
        return sql

    def build_sql_from_args(self, args: object) -> SQLSelectStatement:
        paths, texts, tags, fields = self._flatten_args(args)
        return self.build_sql_from_lists(paths, texts, tags, fields)

    def summarize_query_from_args(self, args: object) -> str:
        if args.query:
            return 'SAVED QUERY: ' + self.args.query[0]
        else:
            parts = []
            paths, texts, tags, fields = self._flatten_args(args)
            width = 32
            for path in paths:
                if path.startswith('^'):
                    parts.append('--- PATH beginning with words:'.ljust(width)
                                 + '"' + path[1:] + '"')
                else:
                    parts.append('--- PATH containing words:'.ljust(width)
                                 + '"' + path + '"')
            for text in texts:
                parts.append('--- TEXT containing:'.ljust(width)
                             + '"' + text + '"')
            for tag in tags:
                parts.append('--- TAG word:'.ljust(width)
                             + '"' + tag + '"')
            for field in fields:
                parts.append('--- FIELD:'.ljust(width)
                             + '"' + field + '"')
            if parts:
                parts.insert(0, 'SEARCHING FOR NOTES WITH:')
            return '\n'.join(parts)


