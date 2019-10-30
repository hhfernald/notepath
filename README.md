# Notepath

*Current version: v0.1.*

**Notepath** is both a command-line program written in Python and a system for using a SQLite database for keeping and querying for text notes.

Currently it has no installer, so you'd download the archive file, extract its contents, navigate to the notepath folder, and run `notepath.py`. From the shell in Linux, you can do this:

    git clone https://github.com/hhfernald/notepath.git
    cd notepath
    chmod +x ./notepath.py

Since `notepath.py` is a terminal application, you can get a quick help screen by entering `./notepath.py --help`.

**2019-10-29:** Notepath should be considered unfinished (alpha) software. Some features need to be added; some issues need to be ironed out. If you download this and play around with it, expect the occasional bug, and make backups.


## Dependencies

-   Python 3.5+.

    (I use a lot of function annotations and
    [type hints](https://docs.python.org/3/library/typing.html)
    in my code.)


## Free Open-Source Software

I wrote this application for no one but myself, but maybe its source code will be useful to someone else. I'm releasing IPyNotes under the MIT License. If you find anything useful in the code I've written, feel free to fork this project and build your own application.


## Anticipated questions

**Q. What is this for?**

Notepath is a system for storing notes in a database file, exporting notes to text files so you can edit them with your favorite text editor, and re-importing your edited notes back into the database.

**Q. Is this for storing plain text or formatted text?**

Notepath stores plain-text notes in the database and re-exports notes as plain text. To indicate formatting, you'd use a markup scheme like Markdown.

**Q. Why store notes in a database if you have to export them to text files just to edit them?**

Basically I used SQLite to save myself from writing my own search code. I wanted to be able to add tags and fields to notes and then search for notes that have specific tags, or notes with a range of values for a specific field. I can query for a specific subset of my notes, save just those notes to a temporary text file, work on those notes, save the notes back into the database, and delete the text file.

I also wanted to be flexible about what text editor you could use to edit the notes. Everyone who works with text has a favorite editor, be it Vim, Emacs, SublimeText, medit, jEdit, or something else. People who use text editors are used to having things like syntax highlighting (e.g., for Markdown), spellcheck, search and replace, and so on. Writing Notepath like this saves me from having to recreate all of that for my program.

**Q. What does it mean for every note to have a "path"?**

Just as your hard drive arranges your files and directories into one big hierarchy, so Notepath arranges your notes into one big outline. You can be as formal or as casual about the topics in this outline as you like, although you'd probably use broad top-level categories like "projects", "work", "contacts", "writing", etc.

**Q. What if I just want to write something down before I forget it?**

If you want a place for arbitrary jottings, you can use a top-level category like "jottings" or even just "j" if you want, then use the date as a subcategory, like this:

    \ j/2020/02/04
    This is the thing I wanted to remember for later.

You could even just use an arbitrary keyword or phrase, so you don't have to spend more than a second or two thinking of a location for your note and can get your fleeting thought down as quickly as possible:

    \ j/phone
    Ronald's phone number: 222-555-6789

You can then save your notes to the database. If the note's path is already used, then the default action is for your new note to be merged to the existing note. This is especially useful if you just want to save jottings by date or keyword.

**Q. Isn't there a risk that you could run a query and end up with more than one copy of a note in multiple files?**

Yes. This is the main drawback of how Notepath is set up. Notepath is meant to be a system for keeping personal notes; it's not meant to handle the needs of a large company, for example. For my own needs, I think that the risk is small and the benefits are worth the risk. You'd have to decide for yourself if the risk is worth taking. But if you adopt the habit of deleting files once you're through with editing them, you alleviate the risk.

Once your notes are saved, you can work on the notes some more and save them again later. Once you are finished working on the notes, though, you should delete the file after saving the notes. This is because it's possible to run two or more queries that export the same notes, in which case you could end up with conflicting versions of the same notes because the same notes are in different files. (You can always query for those notes again.)

**Q. What is the status of Notepath?**

Notepath works just well enough to justify its release to the public.

Notepath comes with a test suite (`test.py` in the `tests` folder). Currently it tests the most critical bits --- saving notes to the database and archiving notes that are overwritten or deleted --- but a number of tests remain to be added.

Generally speaking, Notepath should be considered alpha software. I plan on adding features and testing for more bugs in the near future, so expect changes. If you do try this out, make backups of everything you save into the database; do not trust Notepath until you've used it for a while without incident.

**Q. Where should I save my text notes?**

To alleviate the risk of harming any files in the Notepath installation, you might want to keep Notepath in one directory and your text notes in another. You could create a "notes" directory where your text files will go, then put `notepath.py` and all the files and folders that go with it into a subfolder "n". Then, to use Notepath, you navigate to your "notes" directory and run lines like this to create work files:

    n/notepath.py -r writing/novels/TGAN/chapter1 > chapter1.txt

**Q. Why does Notepath not have an install option?**

I opted to keep things simple. I wanted the option of simply copying Notepath and its accompanying files onto a thumb drive and taking the whole system with me, if the need arose. I didn't see the need to "install" Notepath onto the hard drive if I could put the Notepath directory somewhere and just run Notepath from where it was.



[changelog]: https://github.com/hhfernald/notepath/blob/master/CHANGELOG.md
[wiki]: https://github.com/hhfernald/notepath/wiki
