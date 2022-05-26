
# Errors and Configuration

If there's one thing that programmers hate, it's edge cases. They're annoying and time consuming.

![Snake](images/Snake_moriya_suwako.jpg)

The more sources for error you have, the more edge cases you're likely to have. Unfortunately, often the growth is not linear.
You have to think about these edge cases, and write extra code to handle them.

This sort of thing comes up a lot. An example would be opening a file in C. You have to:
```md
* Get the size of the file on disk (either through `stat()` or the `fseek()` dance)
* Allocate a buffer large enough to store the file's contents
* Open the file for reading
* Read from the file into the buffer
* Close the file
* Null terminate the buffer
```

Basically all of these operations can go wrong. The buffer and the file pointer are resources that need to be cleaned up on failure.
This complicates error handling. Opening a file isn't hard (although the language makes it much harder than it should be), but it's
easy to accidentally leak the buffer or forget to close the file on one of the many errors if you're not careful. There's no other
way to get it right than to squint at your monitor and trace through all the edge cases.

Now suppose your code is firmware supposed to handle something truly unlikely. For example, the internal flash inside your microcontroller
fails mid-write. Or, the wires attaching some sensors to your airplane's engine controller get struck by a bolt of lightning, causing the
readings to spike to physically impossible levels and then go dead as the wires melt. These situations aren't very testable. How can we be
confident that they're handled correctly so the plane doesn't crash?

<br>


## The Solution to the Problem

What we need is some way to make sure the number edge cases stays manageable. Here are a few ways.

```md
* Reduce the number of sources of error in project planning.
 * Limit the scope of the project.
 * Split the project up into manageable parts.
 * Use a library instead of rolling your own. (Ex: std::chrono/DateTime and leap seconds)

* Group errors together with a uniform interface.
 * In POSIX C, `errno` is 0 if no error, otherwise it's the error code.
 * In Java, the exception type is the error code, and it usually comes with a string explanation.

* Treat different kinds of errors the same.
 * In the Daisho `openFile()` implementation, there are only two kinds of errors. There's "out of memory", and there's "couldn't open the file."
   The average programmer doesn't have to care if that's due to a failed integrity check or a sledgehammer. There's an argument that splitting out
   the OOM case is unnecessary also.
```


## A Bigger Problem

A programming language is massive.
