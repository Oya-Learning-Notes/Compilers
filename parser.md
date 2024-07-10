# TOC

- [TOC](#toc)
- [About](#about)
- [CFGs (Context Free Grammers)](#cfgs-context-free-grammers)
  - [Non-Terminal and Ternimal](#non-terminal-and-ternimal)
  - [Productions](#productions)
  - [Derivations](#derivations)
  - [Resolve Ambiguities](#resolve-ambiguities)

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

If we **always first replace leftmost $N$ (Non-terminal)**, then it called **Left-most Derivation**. Similarly, we will have **Right-most Derivation**.

## Resolve Ambiguities