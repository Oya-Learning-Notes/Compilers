Lots of LR Parser will use Stack Automaton and Items. So the `parser` module could extract the base functionality
of those two part to the root of this package.

# Items

Both SLR, CLR and LALR uses Items.

SLR use LR(0) Items, LALR and CLR use LR(1) Items. The only difference between these two are that if it has
a `lookahead`.

In this case we could actually simply implement LR(1) Items, and set `lookahead` to `None` when using it with SLR
algorithm. Or in another word, SLR only using the `core` of the LR(1) Items.

## Augmented Grammar And EOF in LR Parsers

In tradition LR Parser implementations, we treat the End Of Input as a special flag, which is usually represented by
using symbol `$`

In this package, we are going to consider EOF a general `Terminal`, and the only place that use this terminal is in
the augmented grammar:

```
S' -> S$
```

In addition, in CLR/LALR, the lookahead of the Items of this Production is empty (We use `None` to represent this
situation in the package).

When the set of lookahead terminal is `None`, it means the **relevant Reduction could be performed in any circumstance
without the limitation of what lookahead it is currently**.

This make sense. Let's consider what kind of Items will have `None` as lookahead.

-----

**Shift**

First of all, let's consider the Shift moves from Entry `S' -> S$` which will also have `None` as lookahead.

```
S' -> .S$, None
S' -> S.$, None
S' -> S$., None
```

It obvious that Item `S' -> S$` could perform Reduction Action `S$ -> S'` at anytime. This is because the only
possible action is Reduce when we already seen the EOF symbol `$`.

-----

**Closure**

Then if some of the Items derived from the Entry:

```
S' -> S$, None
S -> A...
A -> ...
```

It could be proved that all other items that discovered from Entry will NOT have `None` as lookahead.

Consider we have `S->ABC...`, the CLR Parser Algorithm tells us, the lookahead for this item should be:

```
First([$, None])
```

Since `$` is a terminal as we said before, it's impossible for `None` to be included in the set of lookahead for any
other Items discovered from Entry by finding closure Items.

# Stack NFA Optimization

There are two ways to generate the Stack Automaton for LR Parsers. One is to use `closure()` and `goto()` function
to directly generate the DFA (Determined Finite Automaton).

Another one is to first generate a NFA, then convert the NFA into DFA. Theoretically, we could also get a
well-functioning DFA with same effect as the one obtain from the first method.

However there are some points worth noticing when using the NFA-to-DFA method.

## Preserving Items When Merging State

When we perform actions below:

- NFA-to-DFA
- DFA Minimization

We may need to merge some states from the NFA. And when we doing this on a Stack Automaton NFA, **we should
preserve all relevant Items when merging state**.

For example, if two state `S1: {S->T.E, +}` and `S2: {E->.F, *}` is going to be merged, then the new state should
contain Items info of both merged nodes.

```
S12 = {
  S -> T.E, +
  E -> .F, *
}
```

It's free for you to decide how to store such set of Items in your new merged state as long as all of them are
preserved.

## Do Not Merge Reduction State

### What's Reduction State

First we need to define what states should be considered a Reduction State.

Consider a state S, it's representing Item is I. Then **if the `.` in I is at the last of the Derivation, then this
state S is a Reduction State**.

Below are some example of Reduction State.

```
A -> BCD.
F -> T.
E -> .
```

### Why Not Merge

To be simple, **merging Reduction State may cause Reduce / Reduce conflict.**

First there is a conclusion: **All Reduction State will be considered "Could be merged together"** when performing DFA
Minimization. This it because they all satisfy:

- Have identical Transition
- Are all Accepted States.

So things is obvious: Once there could be two Reduction Items that share same lookahead with different Core, there
will be a Reduce-Reduce Conflict.

Belowing is an example:

```
S' -> S$
S -> CC
C -> cC
C -> d

(c, d is Terminal, other is Non-Terminal)
```

If we do not merge the Reduction State, we will get Automaton with graph like below:

![image](https://github.com/user-attachments/assets/dc136c86-5150-4785-87bb-8f5697d576cf)

All good. No any Reduce-Reduce Conflict found, since all Reduction States are not disturbing each other. But what if
we enable Reduction State Merging? Checkout the graph below:

![image](https://github.com/user-attachments/assets/08029b17-f6a0-4b78-9524-df74814dbdfa)

All Items has been preserved, merged into a new states. Now if we are in that state, and the lookahead is `$`, we could
not determine which Reduction we should perfrom immediately.

Even worse, consider grammer that contains:

$$
\begin{aligned}
S &\to AA \\
A &\to AA \\
A &\to a \\
\end{aligned}
$$

Then it will have some Reduction States like:

$$
\begin{aligned}
S &\to AA, \$ \\
A &\to AA, \$ \\
\end{aligned}
$$

Now when we see $AA$ in Stack, and $\$$ in lookahead, which Reduction should we choose? It's totally ambiguous. Although
sometimes we could solve such ambiguous by rewrite CFG, but the better solution is to **prevent the merge of Reduction
States when minimizing the NFA**.

### How To Prevent

Quite simple and straight. **Check the Transition of states before merging. If there is no any Transition in the states,
skip merging**.

In this package, we use `skip_if_pointers_empty` as the flag to enable this feature.

```python
dfa.minimize(..., skip_if_pointers_empty=True)
```