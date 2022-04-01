## Kinds of Errors, Features, and Builds:

When you're writing a compiler, there's a lot to keep track of. Here's a framework for doing so.

### Errors

I assert that there are a many categories of runtime errors.
```md
1. Is the error recoverable?
2. Did the error come from violating a precondition?
3. Did you plan for this error?
4. Is the cause of the error beyond your control?
5. Is the behavior undefined?
6. Is the error a result of the program being incorrect?
```

As you can see, there are at least 2^6 kinds of errors. For any given combination of yes/no answers to
these questions, you could probably come up with your own example. Here are some of mine.

```md
101000 - `malloc()` fails, and an error is returned to the caller.
000110 - The CPU is hit with a big hammer.
101100 - One of the CPUs in your airplane's engine controller disintegrates.
010011 - Accidentally passed a null pointer to `strlen()`.
010001 - While debugging, you instrumented the build of your code to trap on integer overflow.
```

Although there are lots of types of errors, once one error has been detected, there are really only two things
things you want to do with any error. You either pass the error to the caller, or crash as gracefully
as possible, perhaps after logging the error.

The way that errors are reported should be ergonomic and standardized across all different kinds of functions,
and the way that crashes happen should be standardized, configurable, and overrideable.


### Features

I assert also that there are a few categories of features.
```md
1. Is the feature supported on the platform>
2. Does the feature require optional dependencies?
```

If a feature is supported on the platform and has all of its dependencies, it is available. Otherwise, it is not.
This should not be pushed to runtime.


### Builds

```md
1. Is optimization turned on?
2. Is the build instrumented to catch errors?
3. What features are required?
```

Optimized and uninstrumented is a normal production build, and unoptimized and instrumented is a normal debugging
build. It's less common, but for various other reasons you may want to create optimized and instrumented, or
unoptimized and uninstrumented builds.

If a feature is required but not available, the build should fail. This should not be pushed to runtime.

<br>

