# Roadmap

It's been said that software is never finished; either you publish what you have because you reached a decent stopping point, or you abandon it.

As of the end of October 2019, I am releasing what I have as Notepath v0.1 and releasing it to the world. It is usable right now, but it probably has bugs, and it definitely is missing some features it should have, so I'm not done with Notepath just yet.




## Planned for Notepath

Here are some features I plan to add, and issues I plan to address.


### More tests

At the very least, the test script needs more tests to verify (1) that a field's tags and fields are accurately saved to the database, (2) that queries for specific tags work correctly, and (3) that, for each of ten comparison operators, and each of three value types (string, integer, float), a query for a field works correctly.

I also need to write tests to better verify that named queries are saved and run correctly, and that a query specified directly gets the same results as the same query saved and then run by name.

I also need to write tests for classes other than the Database class.


### Option: --write-to <file_path>

I want to add a `-w` (`--write-to`) option to write exported notes to a file. Of course, since Notepath sends notes to standard output, you can already run something like this ---

    ./notepath.py -g work -f "due by=2020-03-01" > ../tasks.txt

--- to save the notes to a file, but the -w option would be a nice addition.


### Option: --list-tags

This would print a list of all tags in the database, sorted alphabetically.


### Option: --list-fields

This would print a list of all field names in the database, sorted alphabetically.


### Option: --list-values-for <field_name>

This would find all values for a specific field name and print them sorted (with numeric values sorted before other values).


### Option: --list-paths

This would list all note paths in the database, sorted. This would not run a query. To list the paths of notes that match a query, you'd specify a query, but you'd specify `--paths-only`.


### Option: --outline

This would also list all note paths in the database, sorted, but each element in each path goes onto its own line. So instead of printing a path like "writing/novels/TWITW/p1/ch2/scene3/notes", Notepath would print this (with dots and vertical bars to indicate the level of each element):

    writing
    . novels
    . . TWITW
    . . . p1
    . . . . ch2
    . . . . | scene3
    . . . . | . notes


### Option: --sort-by <field_name>

This would sort the matching notes on the field name(s) given before sending the notes to standard output. This would not disqualify any notes matched by the query, so it would have to handle notes that did not have the fields being sorted on.


### Autoquery option

This would be an option for Notepath to search the temporary text at the top of each note file for a "magical" line, something like this ---

    QUERY: -p "word" "^root" -t "phrase" -g "tag" -f "year>1980"

--- that would tell Notepath not only to save the notes to the database, but to overwrite the note file with the results of the query specified in the QUERY line. In other words, the file would be automatically refreshed after each save.


### Option: --vacuum

If you suspect that the database file is getting a little bloated, this option would run SQLite's [VACUUM command](https://www.sqlite.org/lang_vacuum.html) on the file, to remove any unused space within the file.






## Scripts in addition to Notepath

Not every feature I want to have would make a suitable addition to Notepath itself. Rather, I'd create another script or program to perform this work.


### Export notes to HTML, DOCX, EPUB, etc.

I doubt I will add these to Notepath directly. More likely I'll be writing various additional scripts, either to act on note-text files or to use Notepath to query for notes.

One such script would be one that calls on Pandoc or some other program to convert a set of notes into a document in one format or another (a single HTML file, a folder of HTML files, an EPUB or DOCX file, etc.)


### GUI application to simplify using Notepath

Sometimes a GUI application is written to simplify the use of a complex command-line program. If you want to use `grep` or `wget` or some other program, but you're not comfortable using the command line, you can often find and install a program that lets you specify options and parameters by using menus, buttons, and text boxes rather than by typing in the arguments.

I may one of these days produce a simple GUI app to simplify the use of Notepath. The main window would likely show a list of notes on the left (notes matched by the most recent query) and the content of the currently selected note on the right. Notepath would serve as the back end for the app.

The app would have a few goodies for editing, e.g., the ability to hit a key to insert the current date and time as a note-path line (with a divider line above).

At the very least, it should be possible to send the selected text to an external script, have it do something with the text, and send back the result, which would replace the selection in the editor.





