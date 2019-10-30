# Notepath: User's manual

## Introduction

Notepath is a system for keeping text notes. The notes are stored in a SQLite database file, but to work on a subset of those notes, you export notes to a text file, edit them with your favorite text editor, and re-import the notes into the database. (See the RATIONALE document for an explanation for why I set things up in this way.)

Notepath is not version-control software; it does not keep multiple versions of notes. However, the process of using Notepath is analogous to using a verson-control system: You run a query to check notes out of the database, then you add or edit the notes, then you check the notes back into the database.

You run Notepath by running the Python script `notepath.py` within a terminal, with options on what notes to pull from the database, or an option to "save" (check in) a text file of notes back into the database. Some examples (assuming you're using Linux, or some other POSIX system such as Mac OS X):

-   `./notepath.py -t agitated`

    This searches the database for all notes whose text contains the word
    "agitated" and sends the content of those notes to standard output.

-   `./notepath.py -g work -f "cost>500"`

    This searches the database for all notes with the tag "work" and a field
    "cost" with a value greater than 500.

-   `./notepath.py -s *.nptext`

    This loads the notes from all text files matching the `*.nptext` pattern
    and saves them into the database.



## Some basic information

Notepath can be copied onto your hard drive or onto a thumb drive. There is currently no installer.

### Requirements

You need to have Python 3.5 or higher installed on your system in order to run Notepath. Currently, Notepath does not use any Python libraries that do not come with Python itself.

### Folder structure

The folders within the Notepath package are as follows:

-   `data` is where the `notes.sqlite3` database file and the `archive.nparch`
    file will go once they are created.
-   `notepath` contains the module files that contain almost all of the Python
    code for Notepath.
-   `tests` contains the testing script and a couple of data files for testing.


### Text files in notepath format

Notepath takes notes from plain-text files in **Notepath format** and saves them into a SQLite database. Once the notes are in the database, you can query for them, and Notepath will find the notes matching the query and print them to standard output in Notepath format.

This is a sample of what text in notepath format looks like:

    SEARCHING FOR NOTES WITH:
    --- PATH containing: "this/is"

    \===========================================================
    \ this/is/a note path
    \
    \ one tag, another one, and another, separated by commas
    \ a line with an equal sign = a field with a value

    # This is a Markdown "h1" heading.

    This is the text of the note "this/is/a note path".

    If you want formatting, you'll want to use a markup scheme,
    such as **Markdown**.
	
	## Another Markdown heading

    \\If you really need a content line that begins with a
    backslash, begin the line with an extra backslash so that
    Notepath can tell that the line is supposed to be content
    and not a header line.

    \===========================================================
    \ this/is/another note path

    This is another note, one with no tags or fields.

So the whole note file is divided up into **temporary text** at the top, followed by one or more **notes**. Each note consists of a **header** followed by the note's **text**.

#### The note file's temporary text

The note file can include text above the first note, but this text is temporary --- it will not be added to any note or saved to the database.

The purpose of this text is to provide a place where Notepath can save some	statistics about the query that produced the file, such as the terms searched for, when the query was run, the number of notes found, and the number of words in the text of the notes found.

#### The note header

-   The header consists of one or more **header lines**. A header line begins
    with a single backslash character.

-   By convention, the first header line in a note is the **divider line** ---
    a line of equal-sign characters across the top of each note. Notepath does
    not need this; the divider line exists solely to make it easier to see where
    each note begins when you're reading the file in a plain-text editor.

-   The first header line (after the divider line, if the note has one) is the
    note's **path**. The path serves as the note's ID; every note must have a
	different path. The path also indicates the note's location within the
	hierarchy of all notes: Like the path to a file, the path of a note is
	usually a list of categories and subcategories separated by slashes, e.g.,
	`projects/work/website`. If you're in a hurry or can't come up with a good
	path for a note, you could just use the date and time: `2019/11/22/14:23`.
	(Yes, you can use colons in a path.)

-   A note may have header lines other than the divider line and the path line.

	-   If the line has just the backslash, then Notepath ignores the line, since
	    the line is probably there just to make the note header look better.
	
	-   If an at-sign, `@`, follows the backslash, then the line is a
	    **directive**.
	
	-   If no at-sign follows the backslash, but the line does contain an equal
	    sign, then the line is a **field line**.
	
	-   If no at-sign follows the backslash, and the line does not contain an
	    equal sign, then the line is a **tag line**.

-   A note will often have a directive, which tells Notepath what to do with
    the note when you save the note file to the database. The directive is one of
	the following: `@add`, `@merge`, `@replace`, `@rename some/new/path`, or
	`@delete`.

-   A note may have zero, one, or more tag lines. Each tag line has one or more
    tags (keywords), separated by commas. Each tag is an arbitrary word or phrase,
	and you can search for notes that have specific tags.

-   A note may have zero, one, or more field lines. Each field line consists of a
    field name, an equal sign, and a field value. If you have a group of people or
	things you want to keep track of, and you keep a note for each person or item
	in the group, then fields are useful if you want to extract a subset of these
	notes later, based on when a person joined an organization, or how expensive
	an item is, or what year an event happened.

#### The note text

The first non-header line ends the note's header. This line does not begin the note's text unless the line has text on it. In other words, a blank line can be used to separate a note's header from the note's text. (Again, Notepath does not need this; the blank line just makes the note look better in a text editor.)

The note's text consists of all lines from the first nonblank line after the header until the last line (blank or not) before the next note's header or the end of the file (whichever comes first).

The note's text is plain text, of course. If you want to add formatting, such as **bold** or *italic*, you'd use a markup scheme such as Markdown.

A line within the note's text *can* begin with a backslash --- as long as it begins with at least two. (A script that exports notes to HTML or EPUB would need to watch for such lines, and to trim off the first backslash.)

    \\ this is/a line/of note text
	\ this is/an actual/note path



## How to do things

### How to create and edit notes

As stated, Notepath expects your notes to be in a specially formatted text file, so you'd create and edit your notes in a text editor. You can open up your text editor, enter a note-path line, then type in your note's content. The simplest note you're likely to create consists of two lines:

    \ a sample note
	This line is what I wanted to type in and remember.

The path can be a simple phrase, just as long as no other note has the same path. If you can't think of an appropriate path to use, you can always add the current date and time to the path, like this:

    \ random stuff/2020/03/31/2:00 pm

If you add slashes to the date and time, you can then search for notes by year and month, by running Notepath with a line like this:

	./notepath.py -r "random stuff/2020/03"

#### How to make the note file easier to read

The text file can have many notes:

    \note 1
	Text here.
    \note 2
	More text.
	\note 3
	Still more text.

But there are some conventions I use to make the file a little easier to navigate visually, and a little nicer to read. You will find that Notepath uses these conventions when getting notes back out of the database. (These are just suggestions. If you don't follow these conventions, Notepath will still import these notes into the database correctly and without complaint.)

1.  Begin each note with a divider line, to make the location of the start of each note more obvious.
2.  For each header line that is not a divider line, put a space between the backslash and the line's content.
3.  Add a blank line between the end of the note header and the start of the note text.
4.  Add one or more blank lines between the end of one note's text and the start of the next note.

Thus:

    \===========================================================
    \ note 1

    Text here.
	
    \===========================================================
    \ note 2

    More text.
    
	\===========================================================
	\ note 3
	
	Still more text.

Sometimes you want to add tags or fields to a note. I tend to put an empty header line between the note path and the first tag or field line:

    \===========================================================
	\ tasks/clean the garage
	\
	\ todo, home, project, remind me
	\ due by = 2020-02-02
	
	Make sure to clean the toolshed too.


### How to save notes into the database

You can pass the name of one of these Notepath-format files to `notepath.py` to import the files into the database. If the database already has a note with the same path as a note in the file, then the note in the file will (by default) be merged into the note in the database.

If you're careful to give all of your note-text files (and only your note-text files) the file extension `.nptext`, then you can save all of your notes to the database with one command:

    ./notepath.py -s *.nptext

#### Directives

A note will often have a directive, which tells Notepath what to do with the note when you save the note file to the database.

If you are creating a new note, you don't have to add a directive. If a note does not have a directive, then Notepath will treat the note as if it has the `@merge` directive.

	\ 2020/02/03/1400
	Mr. Mattis wants meeting Thursday at 9 AM in his office.

Whenever you run a query, Notepath exports notes with the `@replace` directive, so that whatever changes you make to the note will replace the old note in the database, as long as you leave the note-path line intact.

    \===========================================================
	\ writing/novels/TWITW/p1/ch2/scene3
	\
	\ @replace
	\ plot point, inciting incident
	\ viewpoint = Bakersfield
	\ setting   = Area 27
	
	Bakersfield didn't like the look of that corridor. Too many
	moving shadows. And his infrared camera was beginning to act
	up again.

The directive can be one of the following:
	
-   If the directive is `@merge`, Notepath will first check the database
    to see if a note exists with the same path as your note. If so, then
	your note is merged into this other note, so that the note has both the
	old and the new data. (The old version of the note is appended to the
	archive file.)

	If no such note exists, Notepath simply adds your note to the database.

-   If the directive is `@replace`, Notepath will first check the
    database for a note with the same path. If such a note is found, it is
	appended to the archive file and then deleted from the database. Then
	Notepath simply adds your note to the database.

-   If the directive begins with `@rename`, then a new path should
    follow, like this: `@rename this/is/the/new/path`.

	Notepath will check the database for a note with the note's original
	path and will append it to the archive file and delete it from the
	database if it is found. If a note with the *new* path is found, then
	Notepath performs a merge (see above); if not, Notepath simply adds
	your note to the database.

	***Note:*** If you want to rename a note, the note must include both
	the original path in its usual place *and* the new path immediately
	after the word `@rename`. (If you try to rename a note by editing
	the note-path line, Notepath will of course *not* look for a note with
	the old path; it will look only for whatever is on the note-path line.)

-   The directive `@newpath` is a synonym for `@rename`. You may prefer one
	over the other; they both do exactly the same thing.

-   If the directive is `@delete`, then Notepath appends the note in
    the database to the archive file, deletes the note from the database,
	and does not save the note from the note file to the database.

There is one other directive that you might never use:

-   If the directive is `@add`, then if Notepath finds that another note
    exists with the same path, Notepath halts with a `DatabaseError`. If the
	note to be "added" is in the middle of a note file, then this error does
	not undo the saving of any notes before the note, and it does not ensure
	that the note is saved in any way, but it does prevent the saving of any
	notes after. It also aborts the query, if one was specified, because if
	a call to `notepath.py` both saves notes and runs a query, the saves are
	done before the query, so that new changes may be included in the query
	results.
	
	(If there is no note-path conflict, then of course the note is added.)
	
	You'd normally use either `@merge` (the default for new notes) or
	`@replace` (the default for notes produced by a query) instead. You'd use
	`@add` only if you want Notepath to abort if a note already exists.


#### The archive

Whenever a note in the database is to be altered --- merged with another note, replaced outright, renamed (meaning that its path is changed), or deleted --- it is "archived," meaning that it is exported to the "archive file," which is just another text file in notepath format, named `archive.nparch` and stored in the `data` folder. Thus, old data does not clutter the database file, but if you replace or delete a note by mistake, you can recover the old note, copy it back into a note file, and save it back into the database.


### Getting notes out of the database

To get notes out of the database, you use `notepath.py` to run a query. Any notes that match the query are printed (sent to standard output in Notepath format). You can save these notes to a file using redirection, like this:

    `./notepath.py -g project work > work_projects.txt`

Each note has up to four parts that you can query on --- the main **text** of the note, the note's **path**, the note's **tags**, and the note's **fields**.

-   The `-t` or `--text` option lets you specify words, or "phrases in quotes",
    that must be in each note printed.

-   The `-p` or `--path` option lets you specify words or "phrases" that must
    appear within each note's path. The `-r` or `--root` option lets you
	specify the word or phrase that must *begin* each note's path; this lets
	you take advantage of your outline's structure and restrict the query to
	just a specific section of the outline.

-   The `-g` or `--tag` option lets you specify one or more tags or keywords
    that each note must have.

-   The `-f` or `--fields` option lets you match notes by field. You can
    specify a precise value each note must have, e.g., `-f "color=red"`, or
	you can specify a range of values, where each note must assign a value
	within that range to the given field, e.g., `-f "year>1980" "year<2000"`.

See the section "To run a query for notes" below for more information.



## List of command-line options

### To get information about the program

-   `-h` or `--help`

    Show the options Notepath understands, then exit.

-   `-v` or `--version`

    Show Notepath's version number, then exit.

-   `-L` or `--license`

    Print the software license under which Notepath is released, then exit.

-   `-d` or `--database`

    Print the settings used by Python's version of SQLite.

### To run a query for notes

Note that all of these search for whole words and ignore case, so that "CAT" will match "cat" but not "CATCH" or "cater". In addition, all of these options act together to run a single query, so that `notepath.py -t hiring "business casual" -g dogs -f "year>=2015"` searches for all notes with the word "hiring" in the text, *and* the phrase "business casual" in the text, *and* the tag "dogs", *and* a field "year" where the value is greater than or equal to 2015.

-   `-t` or `--text` (followed by one or more words or phrases)

    Send to standard output each note whose text contains each of the words or quoted phrases given.

-   `-r` or `--root` (followed by one word or phrase)

	Send to standard output each note whose path begins with the word or quoted phrase given. So `-r "one/two red"` will match "one/two red/car" and "one/two red boots" but not "one/two redeemed".
	
	Use this to restrict the search to a specific topic.

-   `-p` or `--path` (followed by one or more words or phrases)

    Send to standard output each note whose path contains each of the words or quoted phrases given.

-   `-g` or `--tag` (followed by one or more words or phrases)

    Send to standard output each note that has each of the given words or quoted phrases as a tag. This always matches whole tags, so that `-g plot` matches the tag "plot", not the tag "plot point" or "plot outline".

-   `-f` or `--field` (followed by one or more field specifications)

    Send to standard output each note that matches each of the field specifications given.
	
	A "field specification" consists of a field name, a comparison operator, and a field value --- for example, `year >= 1980` or `lastname = asimov`. Ten comparison operators are supported:
	
	-   `=` tests if the note's value matches the looked-for value exactly.
	    ***Note:*** This means that case is *not* ignored, so if we're
		seeking `lastname = asimov` and a note has `lastname = Asimov`,
		the note won't match. In this case, you should use
		`lastname re asimov` in the query instead.

        This will also match numeric values as numbers, not as strings,
		so that `count < 20` will match a note were `count = 6`, as it
		should.

	-   `==` does the same thing as `=`.
	
	-   `!=` tests if the note's value does NOT match the looked-for
	    value exactly. In other words, it matches whatever `=` would
		not match.
	
	-   `<>` does the same thing as `!=`.
	
	-   `<=` tests if the note's value is less than or equal to the
	    looked-for value.
		
	-   `<` tests if the note's value is less than the looked-for value.

	-   `>=` tests if the note's value is greater than or equal to the
	    looked-for value.
		
	-   `>` tests if the note's value is greater than the looked-for value.
	
	-   `has` treats the note's value as text, so it matches whole words
	    and ignores case. It tests if the note's value contains the
		looked-for word or phrase.
	
	-   `re` tests if the note's value matches the looked-for value,
	    which is a regular expression. This can be used to match a
		string of characters within a word.

-   `-P` or `--paths-only`

    Normally a query sends whole notes to standard output. If the "paths only"
	option is specified, however, then only notes' paths are sent to standard
	output.

### To save and reuse queries

You can not only run queries; you can have the terms of the query saved to the database under a given name, and then later rerun a query by specifying its name.

-   `-n` or `--name` (followed by one word or phrase)

    Save the terms of this query under the given name. (Use this only when
	the same command includes `--text`, `--path`, `--root`, `--tag`, and/or
	`--field` items to search for.)

-   `-q` or `--query` (followed by one word or phrase)

    Retrieve the query saved under the given name, and send to standard
	output whatever notes match the query.

-   `-l` or `--list-queries`

    Send to standard output the names of all saved queries in alphabetical
	order.

-   `-x` or `--remove-query` (followed by one word or phrase)

    Remove from the database the query saved under the given name.
	(Note that there is no "undelete" option for this, so be careful.)


### To save notes back into the database

-   `-s` or `--save-notes` (followed by one or more file paths)

    Read the notes from the given files and save them into the database.
	Each note will be handled per the directive found in the note (see
	"Directives" above).


## Questions

### What happens if two notes have the same path?

If you save a note to the database that has the same path as a note already there, the default action (if the note doesn't have a directive) is for the new note to be merged to the existing note.

So if you add a note to your text file ---

    \ my note
	\
	\ home, project
	
	This line is new.

--- and the database already has a note like this ---

    \ my note
	\
	\ work, project
	
	This is already in the database.

--- then the note that ends up in the database looks like this ---

    \my note
	\
	\ home, project, work
	
	This is already in the database.
	This line is new.

--- but before this happens, the note that was in the database is appended to the archive file, but with an additional field that has the current date and time as the value ---

    \===============================================
	\ my note
	\ work, project
	\ {archive_date} = 2019-10-28 Mon 8:42:10.924153
	
	This is already in the database.

If the note *does* have a directive, then how the note is handled depends on the directive (see "Directives" above).



