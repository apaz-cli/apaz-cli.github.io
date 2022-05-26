
# Errors and Configuration

If there's one thing that programmers hate, it's edge cases. They're annoying and time consuming.

![Snake](images/Snake_moriya_suwako.jpg)

The more sources of error you have, the more edge cases you have. Unfortunately, often the growth is not linear. You have to think about them, and write extra code to handle them.

This sort of thing comes up a lot. An example would be opening a file in C. You have to:
```md
* Get the size of the file on disk (either through `stat()` or the `fseek()` dance)
* Allocate a buffer large enough memory to store the file's contents
* Open the file for reading
* Read from the file into the buffer
* Close the file
* Null terminate the buffer
```

All but the last of these operations can go wrong. However, the buffer and the file pointer are resources that need to be cleaned up on failure. This complicates error handling. My first few tries had memory/resource leaks in them.


```md
* Time zones
* That code is often difficult to test, especially in firmware.
```
