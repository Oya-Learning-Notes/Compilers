This part takes in charge to convert *source code string* into `token` pairs.

- [Token](#token)
- [Regular Language](#regular-language)
  - [Regular Expressions](#regular-expressions)
  - [Meaning Function](#meaning-function)
  - [Some Regular Expression Example](#some-regular-expression-example)
- [Lexical Specification](#lexical-specification)
  - [LA Matching Process](#la-matching-process)
  - [Resolve Ambiguity](#resolve-ambiguity)
    - [Both $R\_x$ and $R\_y$ matched, Different Matched Length](#both-r_x-and-r_y-matched-different-matched-length)
    - [Both $R\_x$ and $R\_y$ matched, Identical Matched Length](#both-r_x-and-r_y-matched-identical-matched-length)
    - [No Matches](#no-matches)
- [Finite Automata](#finite-automata)
  - [Structure](#structure)
  - [Transition](#transition)
  - [Automaton Diagram](#automaton-diagram)
    - [Practice](#practice)
  - [DFA and NFA](#dfa-and-nfa)
- [Resources](#resources)


# Token

Token consists of 2 parts:

- `class` Indicate type of this token. E.g.: `Op`(Operator), `Id`(Identifier).
  - Some symbol itself could be a `class`, e.g.: `(`, `)` and `;`.
- `lexeme` Content of this token.

And we call `<class, lexeme>` as a token. E.g.: `<Op, "==">`.

# Regular Language

Based on Google Search Result, *Regular Language* represents to **language that could be expressed by *Regular Expressions*.**

## Regular Expressions

There are several actions in Regular Expression:

- $\Sigma$ Chracter set.
- $c$ Single Character.
- $\varepsilon$ Epsilon (Set with an empty string).
- $+$ Union
- $\cdot$ Concatenation
- $*$ Iteration

$$
\begin{aligned}
\varepsilon &= \left \{ '''' \right \} \\
'c' &= \left \{ ''c'' \right \} \\
A + B &= A \cup B \\
AB &= \left \{ ab | a \in A \wedge b \in B \right \} \\
A^{*} &= \bigcup_{i \ge 0} A^i
\end{aligned}
$$

For example:

- $\{a,b\}\{p,q\} = \{ap,aq,bp,bq\}$
- $\{0,1\}^*$ contains empty string and all possible binary string, e.g.: `00101110100101`.

## Meaning Function

In order to distinguish *Sematics* and *Syntax*, here we need to introduce a new function. Consider a function $L(x): RegExp \to StringSet$. Then we amend our previous definition of RegExp.

$$
\begin{aligned}
\varepsilon &= \left \{ '''' \right \} \\
'c' &= \left \{ ''c'' \right \} \\
L(A + B) &= L(A) \cup L(B) \\
L(AB) &= \left \{ ab | a \in L(A) \wedge b \in L(B) \right \} \\
L(A^{*}) &= \bigcup_{i \ge 0} L(A^i)
\end{aligned}
$$

## Some Regular Expression Example

Variable (Start with letter, contains letters and digits):

```
digit = [0-9]
letter = [a-zA-Z]
variable_regexp = letter (letter + digit)*
```

Whitespace (Non-empty sequence of all blank symbol ` `, `\n`, `\t` etc.):

```
whitespace = ` ` + `\n` + `\t`
ws_regexp = whitespace+
```

> Notice: For a set $A$, $A^+ = AA^*$. Which can considered non-empty sequence of $A$.

Number (E.g.:`-3`, `5.4`, `+10.5`):

```
e = ``
sign = (`+` + `-`)
sign_part = sign + e
int_part = digit+
frac_part = (`.`digit+) + e
number_regexp = sign_part int_part frac_part
```

> Notice: `e` above is actually $\varepsilon$.
>
> `some_regexp + e` actually make this part of regexp become *Optional*. In morden RegExp system, we usually use $A?$ to represent $A + \varepsilon$.

Match string that do NOT contain digits.

```
[^0-9]+
```

> Where `[^some_range]` means any characters exclude the ones in this range.

# Lexical Specification

Now we already know the basic about *Regular Expressions*. How can we use this tools to make an *Lexical Analyzer* ?

## LA Matching Process

First of all, we need to write down RegExps for all possible tokens, for example:

$$
\begin{aligned}
  R_{Op} =& ... \\
  R_{Id} =& ...\\
  R_{Vari} =& ... \\
  R_{...} =&...\\
\end{aligned}
$$

Then construct GlobalExp:

$$R = \sum R_{x}$$

Now consider we got an input string $str$.

1. Try matching $str$ using $R$ if $str$ not empty.
   - If $str_{i,j} \in L(R)$: Further find out which $R_x$ it matchs, add it to token pairs, remove $str_{i,j}$ from $str$.
   - If $str_{i,j} \notin L(R)$: Fall into Error Handling process.

## Resolve Ambiguity

### Both $R_x$ and $R_y$ matched, Different Matched Length

Two RegExp both triggered, **with different matched string length**.

For example, consider string contains `==`. It could match `SingleEqSymbol` RegExp: `=`, but could also match `CheckEqSymbol` RegExp: `==`. Which one should we take?

The answer is: most of time we will be glad to directly choosing the one with longer length.

### Both $R_x$ and $R_y$ matched, Identical Matched Length

For example: `test` could match `Variable` RegExp, but in some language it could be a keyword, matching `Identifier` RegExp, and both of them have same matched string length.

In this case, it requires us to specify the priority of different RegExps. The RegExp with higher priority take precedence.

### No Matches

This case indicates some Lexical Errors exists in original $str$. How to deal with this situation will highly affect the error linting ability of a compiler. Modern compiler will **actually NOT let this thing happen** by **adding a bunch of comprehensive matcher used for Error Handling and put them at the end of RegExp list** (which means have lowest priority).

# Finite Automata

If we consider *Regular Expression* the Specification of the Lexical Difinition of LA, then the **Finite Automaton**, which we are going to talking about, **is the implementation**.

## Structure

Structure of a *Finite Automaton* consists of:

- $\Sigma$: Input alphabet.
- $S$: A set of states.
- $F$: A set of accepting states. Should satisfy $F \subseteq S$.
- $n$: Start states.
- $State \to^{input} State'$: A set of transitions.

## Transition

There are 2 final result of a *Finite Automaton*: *Accept* and *Reject*.

- Accept if: *Inputs End* and $State_{now} \in F$.
- Reject if one of:
  - *Inputs End* and $State_{now} \notin F$.
  - Automaton stucked. Which means not exist a transition $State_{now} \to^{input} State'$.

## Automaton Diagram

![image](https://github.com/Oya-Learning-Notes/Compilers/assets/61616918/7a2acb5c-7101-415a-8232-8d3d46c90d18)

The image above indicates a more intuitive way representing a *Finite Automaton*, or you can call it *Transition Graph*.

### Practice

Any `1`'s followed by a single `0`.

![image](https://github.com/Oya-Learning-Notes/Compilers/assets/61616918/46714449-075b-40db-9259-48dc3070db8f)

## DFA and NFA

First we need to know what is $\varepsilon$ moves. That means **automata transfer from one state to another state WITHOUT consuming any input.**

And DFA refers to FA that:

- Do NOT have $\varepsilon$ moves.
- One transition per input per state. (No ambiguous transition: $s_1 \to^{1} s_2, s_1 \to^{1} s_3$ is NOT allowed)

The opposite of DFA is NFA *(Nondeterministic Finite Automata)*. It could have more than one possible path. And accept when some of the path ended in a *Accept State*.

Both `NFA` and `DFA` could be used to recognize Regular Language. However:

- `NFA`: Smaller *(Sometimes exponentially)*.
- `DFA`: Faster to execute *(Since there is no choice, and only one possible state at a time)*.

# Resources

- [Finite Automaton Diagram Whiteboard](https://madebyevan.com/fsm/)
- [Regex To TransitionGraph Simulator](https://ivanzuzak.info/noam/webapps/fsm_simulator/)