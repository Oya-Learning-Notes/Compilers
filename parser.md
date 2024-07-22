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
  - [Generate LL(1) Table](#generate-ll1-table)
    - [First Sets \& Follow Sets](#first-sets--follow-sets)
    - [First Set](#first-set)
    - [Follow Set](#follow-set)
  - [Build Table](#build-table)
- [Bottom-Up Parsing](#bottom-up-parsing)
- [Shift-Reduce Parsing](#shift-reduce-parsing)
  - [Concept](#concept)
    - [Sub Strings](#sub-strings)
    - [Shift \& Reduction](#shift--reduction)
    - [Items](#items)
    - [Prefixes](#prefixes)
    - [Prefix Chain](#prefix-chain)
    - [Viable Prefixes](#viable-prefixes)
  - [Recognize Prefixes](#recognize-prefixes)
    - [Valid Item](#valid-item)
- [SLR Parsing](#slr-parsing)
- [CLR Parsing](#clr-parsing)
  - [LR(1) Items](#lr1-items)
  - [LR(1) Parse Table](#lr1-parse-table)
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

## Generate LL(1) Table

### First Sets & Follow Sets

To generate Parse Table for LL(1), we actually need to calculate the `x` that satisfy `table[A][t] = x` (if it exists), that is:

Consider:

- $A$ A *Non-Terminal*
- $\alpha$ A RHS pattern in *Production* $A$
- $t$ Next *Terminal*
- $B, P, Q, \cdots$ Some other *Terminal* or *Non-Terminal*

Then $table[A][t] = \alpha$, if exists:

$$
\begin{aligned}
  A& \to \{\cdots, \alpha, \cdots\} \\
  a& \to^* tB \\
  & or \\
  A& \to \{\cdots, \alpha, \cdots\} \\
  a& \to^* \varepsilon \\
  B& \to^* PAtQ
\end{aligned}
$$

Above contains two situations.

The first one is simple: if we can get something like $tB$, then we definitely could match next token $t$ successfully. In this situation, we say $t \in First(\alpha)$

The second one means, if we failed to find a way to get something start with $t$ from $A$, it's still possible to match it if $A$ could be derived into $\varepsilon$, and there exists some production could derived into $PAtQ$, so that once $A$ become $\varepsilon$, the next element could be $t$. In this situation, we say $t \in Follow(\alpha)$.

### First Set

For Terminal $t$, we have: 

$$
Start(t) = \{ t \}
$$

-----

For a Non-Terminal $S$:

$\varepsilon \in Start(S)$ if:

$$
\begin{aligned}
  S &\to \varepsilon \\
  & or \\
  S &\to A_1 A_2 \dots A_n \\
  \varepsilon &\in Start(A_i)
\end{aligned}
$$

$Start(S') \in Start(S)$ if:

$$
\begin{aligned}
  S &\to A_1 A_2 \dots A_n S' \dots \\
  \varepsilon &\in Start(A_i)
\end{aligned}
$$

### Follow Set

The definition of Follow Set is: $t \in Follow(A)$ if exists:

$$
S \to^* PAtQ
$$

In which:

- $S$ Some Non-Terminal
- $P,Q$ Some Terminal or Non-Terminal
- $t$ Terminal

In a more succinct way, we could say:

$$
Follow(A) = \{ t | S \to^* PAtQ \}
$$

To **calculate Follow Set of $B$**, We just need to look the *Production* where $B$ was contained in it's *RHS*.

$$
\begin{aligned}
  A \to PBQ &\Rightarrow First(Q) - \{ \varepsilon \} \subseteq Follow(B) \\
  (A \to PBQ) \wedge (Q \to^* \varepsilon) &\Rightarrow Follow(A) \subseteq Follow(B)\\
  \$ &\in Follow(S)
\end{aligned}
$$

> In above, $S$ represents the entry, $\$$ represents *End Of Input*.

## Build Table

Once we have First Sets and Follow Sets, we can start building the Parse Table.

For each $A \to \alpha$, we have:

$$
\begin{aligned}
A \to \alpha, t \in First(\alpha) &\Rightarrow table[A][t] = \alpha \\
  A \to \alpha, \varepsilon \in First(\alpha), t \in Follow(\alpha) &\Rightarrow table[A][t] = \alpha \\
  A \to \alpha, \varepsilon \in First(\alpha), \$ \in Follow(\alpha) &\Rightarrow table[A][\$] = \alpha \\
\end{aligned}
$$

If there are more than one item in the entry of the Parse Table, then this CFG(Context-Free Grammer) system is NOT LL(1) compatiable.

# Bottom-Up Parsing

Bottom-Up parsing is actually **do the opposite of *Production*, which we called *Reduction*.**

![image](https://github.com/user-attachments/assets/0b3fb720-ffe0-4bd7-a469-13e637fb4966)

And we can see that, if we see the process **from bottom to top, we will see that it's right-most derivation**. In another word, **Bottom-up Parsing traces right-most derivation in reverse.**

One advantage of Bottom-up Parsing is that **it do NOT need Left Factoring**.

# Shift-Reduce Parsing

*Shift-Reduce Parsing* is a *Bottom-up Parsing* Algorithm that has been used by lots of popular parser generator.

There are only two types of operation in this Algorithm: **Shift** and **Reduce**.

## Concept
### Sub Strings

Consider a single step in Bottom-up Algorithm: $pABCq \to^{reduce} pXq$ (which based on $X \to ABC$), **then $q$ must be a string of Terminal**. This is because Bottom-up Parsing is always right-most derivation in reverse, so if $q$ is Non-Terminal, then $q$ should be reduced first before $ABC$ has been reduced.

Based on this, we divided input into two substrings: the left part and the right part, use symbol $|$ to seperate them. Specially, call the **right part as Unexamined String** since they were not go through any Reduction.

### Shift & Reduction

- **Shift** means to **shift one Terminal from Unexamined String to left part.**
- **Reduce** means to **perform Reduction with the elements at the end of left part.**

![image](https://github.com/user-attachments/assets/fd71ea87-4202-414e-bfdb-5896a3085510)

### Items

An item *(or in this case you can call it LR(0) items)* is a production with a symbol `.` in the righthand side. For example if we have a part of Production: $A \to (E)$, the items are:

$$
\begin{aligned}
  A \to .(E) \\
  A \to (.E) \\
  A \to (E.) \\
  A \to (E). \\
\end{aligned}
$$

> Specifically, For production $A \to \varepsilon$, the only Item is $A \to .$

We could use Item to **represent the state of our leftside stack** in Bottom-Up parsing. Which we will discuss later.

### Prefixes

If we look into the Stack in Bottom-Up Parsing, we may find that the stack is consists of a series of Prefixes of RHS.

For example, consider a state during Bottom-Up Parsing, with a Production `T -> (E)`

```
(E|)
This state of affairs could be described using Items!
T -> (E.)
```

The mark `T -> (E.)` actually express such states of affairs:

- **Prefix In Stack:** We have already see the prefix `(E` in Stack.
- **Expected:** We expect to see `)` later in the Unexamined String.

Also there is one property about *Prefixes* in Bottom-Up Parsing, that is: All **prefixes in *Bottom-Up Parsing* could be represented using *Regular Expression*.**

### Prefix Chain

Then generally, a valid Stack could actually be considered a valid Chain of Prefixes:

![image](https://github.com/user-attachments/assets/4cafc15f-d79d-4713-bc5f-127b6a4d26f4)

When `int*` got `T` and reduced to `T`, it becomes the needed part of previous prefix. When the `e` got `T`, then it will be reduced to `E` which is needed by it's previous prefix `T -> (.E)`, then it will become `T -> (E.)`

Notice that in a input, the prefixes not always be viable, in another word, one of the key thing in Bottom-Up Parsing is to recognize *Viable Prefixes*.

### Viable Prefixes

This concept refers to ALL things in a stack. If the thing in this stack is possible to finally derived into entry point, then we say this is a *Viable Prefixes*.

Notice that the "Prefix" in Viable Prefix are not the same thing with the prefix we talked above. The prefixes above is the prefix of RHS, but prefix in Viable Prefixes actually refers to some kind of state of the whole Stack.

## Recognize Prefixes

Here comes to the key part: How we recognize Viable Prefixes? How we know if the next input in Unexamined Strings is acceptable?

The answer is **using NFA(Non-Finite Automata) to check the Prefixes in the Stack**.

As we said above, Prefixes could be represented using Regular Expressions, thus can be checked using NFA, and actually the Item refers to a state of the NFA. Every state in this NFA is an accept state.

There are only two rules when we convert CFG to NFA. For every Item: $Item_1 = A \to X.YZ$

$$
\begin{aligned}
  (A \to X.YZ) &\to^Y (A \to XY.Z), &Y = Terminal \vee Y = NonTerminal \\
  (A \to X.YZ) &\to^{\varepsilon} (X \to .Q), & \exists (X \to Q) \\
\end{aligned}
$$

For example we may finally got the NFA below with CFG:

$$
\begin{aligned}
  S' &\to E \\
  E &\to T \\
  E &\to T + E \\
  T &\to (E) \\
  T &\to int * T \\
  T &\to int
\end{aligned}
$$

![image](https://github.com/user-attachments/assets/ed2f633a-92ef-42a0-9d9e-b251e7076e00)

For convenient, we could also convert this NFA to DFA *(a technique we used in Lexical Analyzer algorithm)*, then we could get something like the image shows below:

![image](https://github.com/user-attachments/assets/44b13deb-c227-43b5-87c8-74fdb129c300)

### Valid Item

First we talk about the formal definition of Valid Item.

$I \to X.Y$ is valid item for viable prefix $PX$ if exists Production $S \to^* PIQ \to PXYQ$

**More Simple Way To Explain**

Take it easy, actually a Valid Item is actually means if some Items are possible to be one the of the top of Stack. For example at some point we have Stak:

$$
ABCDE
$$

Then what could be considered as the Item in top stack? $I_1 \to DE.FGH$, $I_2 \to E.MN$, $I_3 \to CDE.P$ and so on. However only some of them are valid. For example if choosing $I_1$ will make it impossible to finally reduced to Entry, then $I_1$ is not a Valid Item for Viable Prefix $ABCDE$.

You may already found, that's what the NFA / DFA above helps us do. **So simply, if we give a Viable Prefix in Stack to DFA, then all Items included in the ending state is a valid state of this Viable Prefix.**

# SLR Parsing

Finally! We are going to talking about how the Parsing Algorithm looks like! Fisrt of all, SLR stands for Simple LR(0) Parsing. We will talk about the "Simple" in the name later.

We the knowledge about Recognize Valid Items above, consider we are in a certain states:

- Next **input in Unexamined Strings is $t$**. *(You could also say the first thing in that Strings is $t$)*
- The Valid Item **DFA halt in an Accept State $s$** when given Stack as input. *(Notice that $s$ should be a set of Items)*

Then the rule of SLR is:

- Reduce by $A \to B$ if satisfy both:
  - $(A \to B.) \in s$
  - $t \in Follow(A)$ *(Notice this is what SLR different from LR(0))*
- Shift $(A \to X.tY) \to^t (A \to Xt.Y)$ if satisfy:
  -  $(A \to X.tY) \in s$

By using SLR, there will be less Shift-Reduce and Reduce-Reduce conflict. *(However SLR could not always completely annihilate such conflict)* It's more about a heuristic method of finding correct handle.

> If a DFA generated from CFG could always find the correct token with SLR, than it's SLR Language, otherwise it's not.

Now let's try some example:

# CLR Parsing

CLR stands for Canonical LR(1) Parsing. But we already have SLR, why we need CLR?

Checkout the example below:

```
S -> L = R
S -> R
L -> *R
L -> id
R -> L
```

![image](https://github.com/user-attachments/assets/13527aae-4250-4589-88a1-5d20f6a84aa4)

The follow set is:

$$
\begin{aligned}
  Follow(S) =& \$ \\
  Follow(L) =& \{=,\$\} \\
  Follow(R) =& \{=,\$\} \\
\end{aligned}
$$

THis grammar is unambiguous, and could parse something like:

```
****id = *****id
**id
id
...
```

Now let's try using SLR to parse the string below with this grammar.

```
id = id
```

Steps:

```
Stack: | id = id
Shift

Stack: id | = id
Reduce: L -> id

Stack: L | = id
  Current state set is I2, which contains R -> L.
  Program: Should we reduce, my SLR Parser?
  SLR Parser: Wait a sec, let me check...
  SLR Parser: Lookahead is "=", and "=" in Follow(R), reduce it!
Reduce: R -> L

Stack: R | = id
Reduce: S -> R (since this is only possible move in I3)

Stack: S | = id
OMG!!! Parse Error!!!
```

The example above shows a situation that SLR Parser will failed. But why?

When current non-terminal is `L` and lookahead is `=`, SLR allow us to do reduce with Production `R -> L` because that $'=' \in Follow(R)$, and this finally cause the problem.

If we look into that how $=$ has been added to $Follow(R)$, we will found it's added based on following Production:

$$
S \to L = R \\
L \to *R
$$

- The first production add $=$ into $Follow(L)$
- The second production add $Follow(L)$ to $Follow(R)$

This means the `=` symbol is in $Follow(R)$ because there is a posibility that $*R$ be reduced to $L$ and $L$ can follow something.

However in case $id = id$, the $R$ inside stack $R = id$ is not structure like $*R$, so it could not be reduced to $L$, since could not deal with the following $=$. So the correct process is to leave this $L$ in stack, but not reducing it.

## LR(1) Items

To solve some issues in SLR and LR(0), one way is to use CLR Parser, which will use LR(1) Items when parsing.

LR(1) Items is similar to LR(0) Items, but with *Lookahead Temrinal* built into the Items. So it will look like something below:

$$
L \to L .+ R,i \\
L \to L .+ R,j \\
L \to .L + R,k \\
$$

Notice in this case the first and second Item should be considered to different Items, since they have different lookahead. The lookahead in LR(1) Item actually refers to that what token should appear after the Reduction.

For example: The lookahead of start symbol $S$ should be $\$$, since the token should appear after Reduction $S \to \cdots$ should only be $\$$ (end of input)

## LR(1) Parse Table

# AST (Abstract Syntax Tree)

Parse above is tracing the derivation sequence of the symbol, but compiler actually want a structural representation of the program, that is: Abstract Syntax Tree, which is similar to Parse Tree but ignored some info.

![image](https://github.com/Oya-Learning-Notes/Compilers/assets/61616918/2c1f1cac-7440-4cef-a846-db17eee2a6cb)

As we can see, something may not be necessary for compiler like:

- Parenthesis
- Single-successor node
- ...

If we convert the Parse Tree above into an AST, we will get:

![image](https://github.com/Oya-Learning-Notes/Compilers/assets/61616918/9e48a59b-e1da-499a-992a-94b20c893f6c)

