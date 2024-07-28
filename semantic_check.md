- [Semantic Analyzer Basic](#semantic-analyzer-basic)
  - [What We Do In SA](#what-we-do-in-sa)
- [Symbol Table](#symbol-table)
  - [Data In Symbol Table](#data-in-symbol-table)
  - [Scope](#scope)
  - [Construct And Maintain Symbol Table](#construct-and-maintain-symbol-table)
- [Attributed Grammar](#attributed-grammar)
- [Type System](#type-system)
  - [Why We Need Type System?](#why-we-need-type-system)
  - [Type System In Compiler](#type-system-in-compiler)
- [Abstract Syntax Tree](#abstract-syntax-tree)
  - [Structure Optimization](#structure-optimization)
    - [List Converting](#list-converting)
    - [Redundant Layer Removal](#redundant-layer-removal)
- [TAC (Triple Address Code)](#tac-triple-address-code)



# Semantic Analyzer Basic

Semantic Check is the last front-end step for a compiler.

## What We Do In SA

Lots of things based on the feature and characteristics of this language.

Generally, we will do things like:

- Symbol Scoping
- Type Checking
- Class Definition Checking
- etc.

# Symbol Table

## Data In Symbol Table

Symbol table is used to store the info of appeared symbols in the program. There could be a lot of different infos in the Symbol Table, for example:

- Name of the symbol.
- Type of the symbol. *(function, variable, classname, ...)*
- DataType of the symbol. *(Int, String, Array, ...)*
- Storage Info of the symbol. *(Address of the symbol, ...)*
- *Other info needed for the compiler.*

## Scope

We use **scope to organize the definition and visibility of the symbols**. Most of the languages are statically scoped. Also, **scope could be nested**.

```cpp
// global scope
int a = 0;

int main(){
    // local scope <func: main>
    int a = 0;
    if(int a=0; x<10; ++x){
        // local scope <func: main, stmt: if_stmt>
        ...
    }
}
```

At a certain point of the program, if the content of the scope has finished, then we say it's a Closed Scope. Else, it's an Open Scope. We still use the code above as example:

```cpp
// global scope
int a = 0;

int main(){
    // local scope <func: main>
    int a = 0;
    if(int a=0; x<10; ++x){
        // local scope <func: main, stmt: if_stmt>
        ...
    }

    // At this point:
    // - global scope: Open
    // - <func: main>: Open
    // - <if_stmt>:    Closed
}
```

At any point of the program, **we should only access the Symbol in the Open Scope at that point**.

## Construct And Maintain Symbol Table

Based on the point we mentioned above, we may know that the **Symbol Table should be maintained dynamically while compiler dealing the sourse code**.

Notice that all source code traverse is based on a tree strcuture like AST, not directly go through the string or the token list.

-----

**Stack-Based Symbol Table**

Extremely simple Symbol Table implementation. We just push new symbol when it declared, pop it when out of scope.

For such Symbol Table, it's able to perform following operations:

- Add Symbol
- Access Symbol
- Remove Symbol

-----

**Multiple Symbol Tables**

This is a more general and powerful approach to manage the symbol in program.

# Attributed Grammar

Attributed Grammar, for me, could actually be considered an enhanced version of CFG. It allows more info to be carried on the node of the tree, thus allow us to achieve more amazing things.

Type Checking and Intermediate Code Generating could both depend on helps from Attributed Grammar.

Also, there are major types of the Attributed Grammar:

- S-Attributed Grammar (**Synthesized attribute only**. Gather info **from bottom to top of the tree**)
- L-Attributed Grammar (Use **both Synthesized and Inherited attribute with some limitation**. Info **could be passed up and down**)

For more info about Attribute Grammar, checkout [Wikipedia Page.](https://en.wikipedia.org/wiki/Attribute_grammar)

# Type System

Formally, a Type System in language is **some valid operations on some different types.**

## Why We Need Type System?

First of all why we need a Type System? Quick answer is: we **only want to allow some certain operation be performed on different types**.

For example, if both $a$ and $b$ is $Integer$, then it's make sense to add them together.

But if $a \in String$, $b \in FunctionPointer$, then that doesn't make sense if you say you want to add them together.

## Type System In Compiler

There are differnt kinds of Type System:

- Static Typing. _C++, Java, etc._
- Dynamic Typing. _Python_
- Untyped. _ASM_

# Abstract Syntax Tree

Actually it's quite intuitive when we want to convert a Parse Tree into an AST. 

The major thing that we need to do is to define the rules of **how to convert a node in parse tree into a node in AST**. And we already know a node in Parse Tree actually represent a NonTerminal or Terminal, so the task becomes defining converting rules for all possible non-terminal and temrinals.

## Structure Optimization

Parse Tree is the very very original result from the Parser, however some info is unnessary or to verbose. We need to do the optimization when generating AST.

### List Converting

For example, the rule `S -> E;S | E;` actually produce language with pattern like `E;E;E;...E;`, and here is the possible shape for Parse Tree:

![image](https://github.com/user-attachments/assets/a6e78ad7-eb92-4715-872b-50c979d1eee3)

So to make such convertion, we could use the rules with schema below:

```
S -> E;S1  // S.make() = return S1.make().insert(index: 0, content: E.make())
S -> E;    // S.make() = return make_list(content: E.make())
```

### Redundant Layer Removal

For rules like:

```
T -> (E)
```

Such node layer does not contains any info, the structure of the Parse Tree already contains the info like calculation order, so the layer could be removed. Please see the image below:

![image](https://github.com/user-attachments/assets/0934a9d4-3eb0-438d-a5b8-e2079bba5ed7)

To do such things, we could use the schema below:

```
E -> T + E  // E.make() = return make_node(type: 'add', left: T.make(), right: E.make())
T -> (E)    // T.make() = return E.make()  <--- Notice we do not use make_node() to generate new node here.
E -> T      // E.make() = return T.make()
T -> int    // T.make() = return int.make()
...
```

# TAC (Triple Address Code)

This is another structure different from AST to represent the parsing info. As its name implies, this code usually store 3 address (sometimes less).