This part takes in charge to convert *source code string* into `token` pairs.

# TOC

- [TOC](#toc)
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
- [RegExp Implementation](#regexp-implementation)
  - [RegExp to NFA](#regexp-to-nfa)
  - [NFA to DFA](#nfa-to-dfa)
    - [$\\varepsilon$ Closure](#varepsilon-closure)
    - [State Mapping](#state-mapping)
    - [Converting Rules](#converting-rules)
    - [Possible Algorithm Implementation (Not-Examined)](#possible-algorithm-implementation-not-examined)
  - [DFA to Table-Driven DFA](#dfa-to-table-driven-dfa)
  - [NFA to Table](#nfa-to-table)
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

Now we already know the basic about *Regular Expressions*. How can we use this ruleset to make an *Lexical Analyzer* ?

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

# RegExp Implementation

## RegExp to NFA

After knowing all info above, the next thing is to convert a RegExp into a NFA*(Nondeterministic Finite Automata)*.

![image](https://github.com/Oya-Learning-Notes/Compilers/assets/61616918/db53f66d-56b5-47ab-899c-3b397992e0ed)

![image](https://github.com/Oya-Learning-Notes/Compilers/assets/61616918/35d8aabf-294e-4606-bbc2-bb797d971889)

![image](https://github.com/Oya-Learning-Notes/Compilers/assets/61616918/0f291b05-4302-4b2a-813c-0eab6d76baf7)

![image](https://github.com/Oya-Learning-Notes/Compilers/assets/61616918/7f6ef93f-abd7-419d-a453-d67595030376)

Those image above shows how to convert *Regular Language* into NFA. Including $\varepsilon, 'c', A + B, AB, A^*$.

> Notice: The **node with schema $M_x$ in diagram actually refers to a sub-NFA**, whichs init state is actually the init state of the sub-NFA, and accept state is the accpet states of the sub-NFA.

Here is example of the NFA Graph of `(0+1)* 1`:

![image](https://github.com/Oya-Learning-Notes/Compilers/assets/61616918/781685c7-f25b-4f42-8325-ef85e2cd43a8)


## NFA to DFA

### $\varepsilon$ Closure

![image](https://github.com/Oya-Learning-Notes/Compilers/assets/61616918/f66a07c2-090b-4b88-a5bd-89027077c1e8)

As the image shows above, An $\varepsilon$ Closure of a node $A$ is all the nodes(including $A$ itself) could be reached through a finite steps of $\varepsilon$ moves.

### State Mapping

Denote that:

- $S$ is the set of states in NFA.
- $n = |S|$ is the number of the element inside $S$.

Then the DFA that represents this NFA could have at most $2^n - 1$ nodes. *(Because empty set of state has been exlucded)*. And the **state of the DFA could be presented as subsets of the NFA**. For example, $X = \{A, B\}$: where $X$ is a state in DFA and $A, B$ are states in NFA.

Moreover, denote:

- $eclos(s)$ Set of $\varepsilon$ Closure of state $s$
- $a(s)$ Set of all possible state next when current state is $s$ and input is $a$, or you could say:

$$
a(s_1) = \{s_2 | \exist s_1 \to^a s_2\}
$$

### Converting Rules

Now we could use the following rules to convert NFA to DFA:

- $S_{DFA}$ = Subset of $S_{NFA}$
- $Start_{DFA}$ = $eclos(Start_{NFA})$
- $F_{DFA}$ = $\{X | X \in S_{DFA} \wedge X \cup F_{NFA} \not= \emptyset \}$
- $X_1 \to^a X_2$ Exists if: $X_2 = eclos(a(X_1))$

### Possible Algorithm Implementation (Not-Examined)

Denotes that:

- $eclos(s)$ Set of $\varepsilon$ Closure of state $s$

That means: for any $x \in eclos(s)$, then we could use finite steps of $\varepsilon$ moves from $s$ to $x$

- $move(a,S)$ Set of all possible state next when current state is $S$ and input is $a$. 

Notice here $S$ is a set of states, This means: 

$$
x \in move(a,S) \Leftrightarrow \exists s (s \in S \wedge s\to^a x)
$$

Then the pseudo code could be:

```python
# DFA start state is e-closure of NFA start state
dfa_start_state = eclos(start_state(NFA))

# function used to detect new dfa state based on received previous state
def find_new_state(prev_state):
    if prev_state is already found:
        return
    # loop all possible input for current DFA state
    for input in all_possible_input(prev_state):
        # for each possible input, find DFA state after this input
        new_dfa_state = eclos(move(a, prev_state))
        # add to dfa state
        add_dfa_state_if_not_exists(new_dfa_state)
        # start from the newly found state, search more possible state
        find_new_state(new_dfa_state)

# start DFS search from DFA start state
find_new_state(dfa_start_state)
```

## DFA to Table-Driven DFA

Any DFA could be represented by a 2D table with following pattern.

- Row Index: States of DFA
- Column Index: Possible inputs
- Table`[i][j]` = $x$ that satisfy $S_i \to^j S_x$

Example:

![image](https://github.com/Oya-Learning-Notes/Compilers/assets/61616918/dfb6e882-d414-49ad-8f63-49107f62c748)

The corresponding table of the DFA above is:

|     | 0   | 1   |
| --- | --- | --- |
| S   | t   | u   |
| T   | t   | u   |
| U   | t   | u   |

Since **lots of rows are the same**, we could use a optimized pattern below to lower the size of table. However **this method could lower the algorithm** since there are indrect pointers, means we need to read twice time to get an item from table.

![image](https://github.com/Oya-Learning-Notes/Compilers/assets/61616918/267b34f6-097e-489c-9cb3-a002abe0920f)

## NFA to Table

We could skip the step of converting to DFA, and directly convert a NFA into Table, however this will be slower since the table block now handles set of states as image show below:

![image](https://github.com/Oya-Learning-Notes/Compilers/assets/61616918/e263d680-2bfa-4b45-aaa0-e5fad8e94787)

# Resources

- [Finite Automaton Diagram Whiteboard](https://www.cs.unc.edu/~otternes/comp455/fsm_designer/)
- [Regex To TransitionGraph Simulator](https://ivanzuzak.info/noam/webapps/fsm_simulator/)