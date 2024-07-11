# TOC

- [TOC](#toc)
- [About](#about)
- [CFGs (Context Free Grammers)](#cfgs-context-free-grammers)
  - [Non-Terminal and Ternimal](#non-terminal-and-ternimal)
  - [Productions](#productions)
  - [Derivations](#derivations)
  - [Resolve Ambiguities](#resolve-ambiguities)
- [RD Algorithm (Recursive Descent)](#rd-algorithm-recursive-descent)
  - [Limitation of RD Algorithm](#limitation-of-rd-algorithm)
    - [Short Circulating](#short-circulating)
    - [Left Recursive](#left-recursive)
- [LL(k) Algorithm](#llk-algorithm)
  - [Left Factoring](#left-factoring)
  - [Parsing Table of LL(1)](#parsing-table-of-ll1)
  - [Code Implementation](#code-implementation)
- [AST (Abstract Syntax Tree)](#ast-abstract-syntax-tree)

# About

The task of parser is to:

- Convert *Token Pairs* into *Parse Tree*
- Provide graceful error info when parse failed

To do this, we need:

- A way to describe the rules of how to parsing the tokens
- Implementation the rules into parser

# CFGs (Context Free Grammers)

Context Free Grammer is a way to describe parsing rules. We notice that grammers of a Programming Language is usually recursive, for example let consider the $EXPR$ structure of a language:

```
EXPR = if EXPR then EXPR else EXPR
EXPR = while EXPR do EXPR
EXPR = ...
```

In above, parts like `if`, `else` etc are now dividable anymore, however `EXPR` can be divided using those rules recursively. Now let's talk about how CFG describe this rules:

$CFG$ consists of the following parts:

- $N$ Set of Non-Terminal
- $T$ Set of Ternimal
- $S$ Start symbol
- $P$ Set of productions

## Non-Terminal and Ternimal

Non-Terminal refers to some final state of that part of string. **Once Ternimal is produced, it's permanent and will not be changed or dirived anymore**, however a Non-Ternimal could produce other Non-Ternimal or Ternimal, and that could be done by *Productions*.

## Productions

Formally, $P$ satisfys the following structure:

$$
P_i = X \to \{Y_1, Y_2, \cdots, Y_n\}, X \in N,Y_i \in N \cup T 
$$

The productions in CFG is actually a *Transition* (or you can consider it rules) that defined how can a Non-Terminal produce some another Non-Ternimal or Terminal.

For example:

$$
\begin{aligned}
    P_e =& E \\
    |& E + E \\
    |& E * E \\
\end{aligned}
$$

## Derivations

The rules above could be used recursively to generate something like:

$$
\begin{aligned}
    E &= E * E \\
    &= E * E + E
\end{aligned}
$$

The sequence of the replacing above is called *Derivation*. A derivation could represents a *Parse Tree*.

If we **always first replace leftmost $N$ (Non-terminal)**, then it called **Left-most Derivation**. Similarly, we will have **Right-most Derivation**. And a single *Start Symbol* $S$ could have more than one *Derivations*.

## Resolve Ambiguities

Still using $id * id + id$ as example, we have 2 way to parse this Symbol:

$$
\begin{aligned}
    E &= E * E \\
    &= (E * E) + E
\end{aligned}
$$

Or

$$
\begin{aligned}
    E &= E + E \\
    &= E * (E + E)
\end{aligned}
$$

How to solve this kind of ambiguity? One way is to rewrite the Productions:

$$
\begin{aligned}
  E \to& E' + E \\
  |& E' \\
  E' \TextOrMath& E' * (E) \\
  |& (E) \\
  |& E' * id \\
  |& id
\end{aligned}
$$

The two new Production above will ensure that operator `*` takes precedence of `+`. This is because the rules above ensures that any derivation that could generate pattern `A * B` must under the node of `+` symbol, and if you want to generate `+` symbol in subtree under `*`, then you will need parenthesis `()`.

Here is another example:

```
E -> if E then E else E
   | if E then E
   | ...
```

Then if we have a Symbol: `if E then if E then E else E`, there are two ways to parse this:

```
(1) if E then (if E then E else E)
(2) if E then (if E then E) else E
```

However we want the `else` clause to match nearest `if`, how to achieve this?

```
E -> if E then E
   | E'

E' -> if E then E' else E
    | (E)
```

# RD Algorithm (Recursive Descent)

This is an algorithm to implement parsing with CFG rules.

Consider the following definition:

- `INT, DOUBLE, LEFT_PAIR, RIGHT_PAIR, PLUS, ...` A set of aviliable token types.
- `next` A global process pointer, pointing to the position of currently proceeding char.

- `term(TERM: TOKEN): bool` Try to match a specific term at current cursor position. Return `true` if success.
- `E_x()` Function that test $x$th pattern in Production $E$. Return `true` if matched.
- `E` Function to try all possible patterns in Production $E$

Let's checkout how to write this function.

```cpp
bool term(Term term){
  return *next++ == term;
}
```

```cpp
// Consider E = T | T + E
bool E_1(){
  return T();
}

bool E_2(){
  return T() && term(PLUS) && E();
}

bool E(){
  /**
  * Here we create a "backup" of the next pointer.
  * If the previous test failed, we should first recover 
  * the previous place of the pointer before moving on to 
  * try the next one.
  */
  auto save = next;
  return ((next = save, E_1()) || (next = save, E_(2)));
}

// T = int | int * T
// Code is not shown for brevity
```

## Limitation of RD Algorithm

### Short Circulating

Consider we using the program above to match a token list `int + int`:

```
Invoke root: E()
  Try: E_1()
    Try: T() Succeed
  E_1() Succced
E() Succeed

Terminated.
```

We failed. The program only matching the part `int`.

After analyzing, we found the **problem is because of Short Circulating**: Once `E_1()` *(represent T)* succeed, it will directly return `true` and we have no chance to try other pattern like `E_2()` *(which represent T + E)*, which in this case could also match.

To solve this problem, we may need to rewrite our Productions to make there is at most one Derivation that matched in a single Production.

### Left Recursive

If in a CFGs, there are productions that satisfy:

$$
X \to^+ Xa
$$

In which:
- $X$ is a Non-Terminal
- $a$ is a Non-Terminal or Terminal
- $\to^+$ Means more than one time of production.

**Then we call this case a *Left Recursion***. Follwing is some CFGs production set that could lead to left recursion.

```
(1)
T = Ta | G
// Direct Left Recursion

(2)
T = R
R = Ma
M = T
// T -> R -> Ma -> Ta
// Indirect transmissive Left Recursion
```

Left recursion couuld break RD Algorithm **because it will sometimes lead to a *Dead Loop***. To solve this, we could **rewrite our Productions to eliminate *Left Recursion* cases**.

Example:

```
T = Ta | G  // Match G a+
```

Rewrite to:

```
T = GT'         // Match GT'
T' = aT' | e    // Match a+
```

Actually the **process of eliminating Left Recursion could be done automatically**, but in lots of cases the developer **still resolve this issue manually**, since **knowing how Parser work is helpful for the following step of making other part of the compiler** (*Semantic Checker*, for example).

# LL(k) Algorithm

This algorithm could solve the limitation of RD Algorithm. What it does is briefly *Lookahead*, that is use the info of next Token when deciding which pattern to use in current *Production*. We also call this *Predictive Parsing*.

In the name LL(k):

- First L refers to Left-to-right
- Second L refers to Left-most derivation
- `k` refers to $k$ tokens lookahead (Most cases this will be 1)

Notice that in Perdictive Parsing:

- Lookahead enabled
- No backtracking

The second point is the key, and we actually need to ensure **our CFG support *Predictive Parsing* and have no ambiguity** when using the next token to predict which pattern to use in a *Production*.

## Left Factoring

Checkout the Productions example:

```
E -> T | T + E
T -> int | int * T
```

Both rules could be issue when using Productive Parsing **since they have *Common Prefix* in their different patterns**.

For example we want to match `int * int`, and at sometime, we are now try dealing with node `T`, with next token look ahead `int`

```
E = T <-- Current Node: T, NextToken: `int`
// T -> int | int * T, if we only based on next token `int`, we could not determine which pattern to use.
```

This is why we need *Left Factoring*. In *Left Factoring*, we need to devide one *Production* into multiple to avoid *Common Prefix* of the patterns inside a single *Production*. Use the example above again, we could modified the *Production* into:

```
Original:
E -> T | T + E
Modified:
E -> TX
X -> e | + E    // e means epsilon here.

Original:
T -> int | int * T
Modified:
T -> int Y
Y -> e | * T    // e means epsilon here.
```

In this way there is no any *Common Prefix* in our *Productions* and the *Perdictive Parsing* could work well.

## Parsing Table of LL(1)

Once Left Factoring finished, we should be able to know what pattern inside a Production we should use with 1 Token lookahead. Then we could make a table that:

- Column Index: **Left-most Non-Terminal** waiting for Production.
- Row Index: **Left-most Token** waiting for Parsing.

![image](https://github.com/Oya-Learning-Notes/Compilers/assets/61616918/4d60b366-2ff2-405d-9e80-fc34482930da)

> RHS: Right hand side. In this article I used *Pattern* to represent the same thing.

## Code Implementation

How to write code to use the Parse Table?

```ts
type Terminal = Token;

// Token list and Parse Table.
const tokenList: Token[];
const parseTable[][]: RHS[NonTerminal][Token];

// Initial stack and next pointer.
let stack<Terminal | NonTerminal> = {E, $}; // $ Means end of Tokens.
let nextPtr = 0;

while(!stack.empty()){
  let stackTop = stack.pop();
  let tokenLookahead = tokenList[nextPtr];

  if(typeof stackTop === 'NonTerminal'){
    // find a valid rhs choose.
    let rhsChoosed: NonTerminal = parseTable[stackTop][tokenLookahead];
    if(rhsChoosed === undefined){
      console.log("Error: No available RHS pattern for this input on production");
    }
    // update stack.
    stack.push(rhsChoosed);
  }

  if(typeof stackTop === 'Terminal'){
    // try matching terminal with next token.
    let matched = stackTop === tokenLookahead;
    if(!matched){
      console.error("Error: Could not match tokens");
    }
    // update nextPtr.
    nextPtr++;
  }
}
```

![image](https://github.com/Oya-Learning-Notes/Compilers/assets/61616918/679734c8-e322-418a-90b9-bef2c84ea115)


# AST (Abstract Syntax Tree)

Parse above is tracing the derivation sequence of the symbol, but compiler actually want a structural representation of the program, that is: Abstract Syntax Tree, which is similar to Parse Tree but ignored some info.

![image](https://github.com/Oya-Learning-Notes/Compilers/assets/61616918/2c1f1cac-7440-4cef-a846-db17eee2a6cb)

As we can see, something may not be necessary for compiler like:

- Parenthesis
- Single-successor node
- ...

If we convert the Parse Tree above into an AST, we will get:

![image](https://github.com/Oya-Learning-Notes/Compilers/assets/61616918/9e48a59b-e1da-499a-992a-94b20c893f6c)

