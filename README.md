# IO-Language

**The IO Language is a dynamically typed, horribly supported and badly written programming language that compiles to C++.**

# Syntax

The syntax of IO is fairly simple. This is an example function named "hello" that takes an argument "a", and an argument "b".

```
hello: a b
{
	print(a)
	print(b)
}
```

To store a variable, the arrow is used.

```
a <- 0
print(a)
a <- 'hello world!'
print(a)
```

While loops are "for" loops, and take either a function, a variable, or nothing as input.

```
for
{
	print('this will print forever!')
}

a <- 1
for a
{
	print('this will print while a is not 0!')
}

for =(a 1)
{
	print('this will print while a is 1!')
}
```

If statements have the same syntax.

```
a <- 1
if a
{
	print('a is one!')
}
```

The entry point has different syntax.

```
ook: a
{
	print(a)
}

main
{
	ook(9)
}
```

Functions can return one value each.

```
ook: a
{
	return <- add(a 1)
}

main
{
	a <- ook(9)
	print(a)
}
```
