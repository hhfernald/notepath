# Notepad: Rationale

This document explains how I came to write Notepath.

Over the years, I have accumulated an ungodly number of text notes on various topics --- over 25,000 of them, taking up over 25 megabytes of text. Searching and organizing these notes has become a problem, and I have tried various solutions over the years. I have been unhappy with most of them for one reason or another.

## Initial principles

In the past, I had tried out a number of applications (Microsoft Word, [Atlantis Word Processor](https://www.atlantiswordprocessor.com/en/), [Writer's Café](http://www.writerscafe.co.uk/), and [Scrivener](https://www.literatureandlatte.com/scrivener/overview) among them) that either were proprietary, stored information in proprietary formats, or ran on only one operating system (usually just Windows or just Mac OS X). Even if the application stored text in text files (or at least files readable by a plain-text editor), it often stored text in some encoding other than UTF-8, or (like [WikidPad](http://wikidpad.sourceforge.net/) and [Zim](https://zim-wiki.org/)) it allowed for the use of markup to indicate formatting, but it didn't work well with Markdown. When I eventually became unhappy with those applications for one reason or another, the process of migrating --- moving my notes out of one application and into another --- was a pain in the butt. So over time I decided on some rules I wanted to follow for my notes:

-   I wanted to store them as plain text. No matter what operating system you
    are using, you have access to a text editor, and you probably get to choose
    from dozens of text editors.
-   I wanted them encoded with UTF-8 --- not plain ASCII, not UTF-16,
    not [Mac OS Roman](https://en.wikipedia.org/wiki/Mac_OS_Roman),
    and not Windows "ANSI"
    ([ISO-8859-1](https://en.wikipedia.org/wiki/ISO/IEC_8859-1) or
    [CP-1252](https://en.wikipedia.org/wiki/Windows-1252)).
-   I wanted to use Markdown to denote headings, *emphasis*, lists, blockquotes,
    and `code samples`.

I had resolved early on that the notes should be stored as text --- not word-processor documents or proprietary files.

So why have I now changed my mind and decide to store my notes in a SQLite database file?



## Why SQLite?

Imagine that you have thousands of notes on various topics. How do you store them?

Imagine that you're still committed to storing them all in text files. You can store one note per file, as programs like [QOwnNotes](https://www.qownnotes.org/) and [IPyNotes](https://github.com/hhfernald/ipynotes) require. When you do this, though, being able to manipulate the notes using a file manager becomes tempting, especially when you have a huge number of notes and you want to organize them in some way. But file managers often become sluggish when they are used to browse directories with thousands of small files. Not only that, but searching thousands of files for a phrase can also be very slow.

Storing *all* of your notes in a single text file seems like a great idea, since searching a large file is much faster than searching many small files with the same amount of text. It's fine as long as the text file is under a megabyte or two in size. Unfortunately, many text editors become sluggish or even crash-prone when used to edit a file ten or more megabytes in size.

Storing many notes in each of many files --- that is, segregating notes by general topic --- seems like the compromise to make. Each file would represent a top-level topic, such as "work" or "projects" or "writing" or "todo".

But at some point, I decided that I wanted to be able to attach tags (keywords) and fields (name-value pairs) to notes. I should be able to have notes with no tags or fields, but the other notes should have whatever number of tags or fields seem appropriate. I wanted tags or fields because there is always more than one plausible way to find a note, and if I put a note in "work" or "writing", it could just as easily go into "todo" because it dealt with something I wanted or needed to do.

So at the very least, I wanted to be able to mark a note as a to-do item.

Over time, I also wanted to be able to sort notes on fields. If I store a number of quotations by topic, I might want to be able to output them sorted by the name of the person being quoted. If I have multiple files listing historical events, I'll want to be able to sort them by year. And so on.

But if I keep tags and fields in notes in text files, then I'd need some kind of software to (1) retrieve those notes, and only those notes, that match what I'm looking for, and (2) sort those notes on the fields they have, if they have them.

Most text editors will sort lines in a file. I have yet to find a text editor that will treat groups of lines in a file as a unit and to sort those units by information within them. If I wanted that, I'd have to write code to handle that myself.

But then I remembered [SQLite](https://sqlite.org/about.html).

SQLite files are binary files, not text files, of course, but the SQLite file format is in the public domain, and it's not going away. It's a binary format that lets an application save changes without rewriting the whole file (which is what has to happen whenever you save changes to a text file, no matter how large the file or how small the change).

I won't go on any further about the various approaches I experimented with. I'll just say that Notepath stores notes in a SQLite file, because SQLite offers some advantages over text files:

-   ***Saves are safe.*** If the system crashes or the power goes out in the
    middle of a save, SQLite can roll back the changes it made to the file, and
    the file is left undamaged. Try that with a large text file.

-   ***Huge files are not a problem.***
    Loading a SQLite database requires that only a small portion of the file be
    read into memory at a time. You can store hundreds of thousands of notes in
    a single file without issue. The database file can grow to tens or hundreds
    of megabytes in size, and your application will not slow down or crash when
    you open the database. Many text editors cannot handle text files larger
    than a dozen megabytes or so.

-   ***Saves are fast.***
    Saving a single note to a large text file requires that the entire text file
    be rewritten. Saving a single note to a large SQLite file requires that only
    a small portion of the file be rewritten.

-   ***Loads are fast.***
    You usually want to see only those notes that match a pattern, or notes that
    have certain tags or fields. Most text editors require you

-   **Queries are possible. You can retrieve just the data you want.**
    The SQLite library makes it possible to query your data. Specifically, notes
    can have tags (keywords) and fields (name/value pairs) assigned to them, and
    Notepath can output all notes with not only specific words and phrases but
    also specific tags and fields. The note file has indexes to make searches
    for tags and fields fast.

-   **The SQLite file format is nearly universal.**
    Text files might be thought of as *the* universal file format for personal
    data, but the SQLite file is probably the closest thing there is to a
    universal *binary* file format for personal data. SQLite files can be opened
    and read and queried and written as-is on Windows, Linux, Mac OS X, Android,
    and other operating systems.

    Even if you lose the script you use to query and modify the database,
    applications like "DB Browser for SQLite" can be used to read the database
    and export its records.

***Why not build an application to edit the database directly?***

Notepath is a compromise.

I've started working on a note-keeping application many times, only to start over because I wasn't happy with the result. Most notably, I got [IPyNotes](http://www.github.com/hhfernald/ipynotes/) working, but I wasn't satisfied with having one note per file when I had over 20,000 notes.

I finally got tired of spending a few months working on a new GUI application, only to end up unhappy with it. I decided to work on a command-line application, reasoning that I could write a GUI that called the application in the background later.

The project also turned out to be fast to write. Without having to worry about menus and toolbars and preferences and all the things that a modern GUI application is supposed to have, I managed to get Notepath v0.1 written in less than two-and-a-half weeks.

I can always write that GUI app later. It would call Notepath in the background, and pull the notes from Notepath's standard output stream. In the meantime, I already have something I can use, and if it's slightly clumsy, that's OK for now.



