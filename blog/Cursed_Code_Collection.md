
# Cursed Code Collection


<hr>

The shebang for C is just a little bit longer than one line.
```c
#if 0
TMP="$(mktemp -d)"
cc -o "$TMP/a.out" -x c "$0" && "$TMP/a.out" $@
RVAL=$?
rm -rf "$TMP"
exit $RVAL
#endif

#include <stdio.h>
int main() {
  puts("This is such a cool bash script!");
}
```

<hr>


Open a file, swap the nibbles of every byte, and write it back.
I'm not sure if this error handling macro is big brain or small brain.
For sure it wouldn't pass code review.
```c
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <stdio.h>
#include <errno.h>

char* b;
size_t i;
int fd;
struct stat st;

#define EH(fn,...) fn(__VA_ARGS__); if (errno) return perror(#fn), 1;
#define sz st.st_size

int main(int argc, char** argv) {
  if (argc != 3) return 1;
  EH(stat, argv[1], &st);
  b = EH(malloc, sz);
  fd = EH(open, argv[1], O_RDONLY);
  EH(read, fd, b, sz);
  for (i = 0; i < sz; ++i)
    b[i] = ((b[i] & 0x0F) << 4) | ((b[i] & 0xF0) >> 4);
  fd = EH(creat, argv[2], S_IRWXU);
  EH(write, fd, b, sz);
}
```

<hr>


Annihilate your python runtime.
```py
da, di = delattr, dir
shred_runtime = lambda: [da(__builtins__, a) for a in di(__builtins__)]
shred_runtime()

# print() is no longer defined
print("Hello World!")
```

<hr>


Use generics to figure out what version of `strerror_r` you have. This 
is less cursed code, and more just the most sane way of doing things. 
But the fact that `_Generic` is actually the best solution to any 
problem is baffling, and cursed in its own right.

```c
#include <string.h>
#include <stdio.h>

#define STRERR_R _Generic(strerror_r,                          \
                          int(*)(int, char*, size_t): "XSI",   \
                          char*(*)(int, char*, size_t): "GNU", \
                          default: "UNK")
int main(void) {
  puts(STRERR_R);
}
```

<hr>


`eval()` exists in javascript and python. It takes code as a string and 
runs it. What if I told you it existed in C as well?
```c
#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <unistd.h>

void eval(char* program, char* symbol) {
  FILE* tmpf = fopen("/tmp/libtmp.c", "w");
  fprintf(tmpf, program);
  fclose(tmpf);
  system("cc /tmp/libtmp.c -shared -o /tmp/libtmp.so");
  ((void(*)(void))dlsym(dlopen("/tmp/libtmp.so", RTLD_LAZY), symbol))();
}

int main() {
  char* hello_world = (char*)"#include <stdio.h>\n"
                             "void hello(void) {\n"
                             "  puts(\"Hello World!\");\n"
                             "}";
  eval(hello_world, "hello");
}
```


<hr>


My favorite hello world program. The compiler replaces the while loop 
with a call to `memset()`, and it calls our memset rather than the one 
from the stdlib, because that one hasn't been included. To disable this 
behavior, you can use the compiler flag `-fno-builtin`.

```c
#include <stdio.h>

void* memset(void* s, int c, size_t n) {
  puts("Hello world");
}

int main(int argc, char** argv) {
  while (argc--) argv[argc] = 0;
}
```

<hr>


Melt your compiler. GCC does the right thing and tries to read 
/dev/urandom forever. For some reason Clang does not, doesn't even 
error, and compiles a functional hello world program. Absolutely wild.

```c
#include </dev/urandom>
#include <stdio.h>

int main() {
  puts("Hello world!");
}
```
