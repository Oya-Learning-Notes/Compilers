- [Basic Block](#basic-block)
- [Control Flow Graph](#control-flow-graph)
  - [Calculate Dominators](#calculate-dominators)
  - [Natrual Loop](#natrual-loop)
  - [Refs](#refs)
- [Data Flow Analyzation](#data-flow-analyzation)
  - [Forward Analyze](#forward-analyze)
  - [UD Chaining](#ud-chaining)
  - [Backward Analyze](#backward-analyze)
  - [DU Chaining](#du-chaining)

# Basic Block

Here consider we already get the TAC(Triple Address Code). First step is to **conclude lines of TAC into several Basic Blocks.**

The definition of Basic Blocks is as below:

- Is several lines of code that should be executed sequently.
- Only have one start line, one end line.

# Control Flow Graph

In this graph, the node would be Basic Blocks.

We need to know:

- Calculate Dominators for nodes
- Find natural Loop in CFG

## Calculate Dominators

Here is one of the algorithm approach to calculate Dominators in CFG.

- Consider for node $N_i$, the dominators is $D(N_i)$, which is a set of nodes.
- Initialize all nodes, let $D(N_i) = \{ N_i \}$
- For each node $N_i$, for any $j$ that exists an edge $j \to i$
   -  $D(N_i)' = [\cap D(N_j)] \cup D(N_i)$
- Repeat previous step until no more Donimators has been changed.

## Natrual Loop

After this, we will be able to find out Back Edge and Natrual Loop.

## Refs

[Algorithms In Control Flow Graph](https://www.csd.uwo.ca/~mmorenom/CS447/Lectures/CodeOptimization.html/node6.html)

The link above contains explainations about lots of algorithms and implementation of those algorithms in CFG(Control Flow Graph).

# Data Flow Analyzation

We would analyze the data flow between blocks and inside a block.

We have several tools for the data flow analyze between blocks:

- Arrival-Def Flow **(Forward Analyze)**
  - UD Chaining
- Active-Variable Flow **(Backward Analyze)**
  - DU Chaining 

## Forward Analyze

$$
out[B] = gen[B] \cup (in[B] - kill[B])
$$

In the formula:

- $out[B]$ : The SP(set point) info that could **flow to the end of this Basic Block**.
- $in[B]$ : The SP info that **exists at start of BB**(Basic Block).
- $gen[B]$ : The SP info that could **survive at the end of the BB**.
- $kill[B]$ : The SP info that **being overrided(reset) in this BB**.

Based on the info, we could calculate $in[B]$ and $out[B]$ for any Basic Block $B_i$.

## UD Chaining

If we used ref of variable `x` in line `j` of BB `B`, then **all the set points that could reach** is in the UD chain of `x` at this point.

```
Schema: <BasicBlockIndex, LineNumber>

<BB3, 0>
<BB3, ...>
<BB3, i-1> 
<BB3, i+0>   m = x + 3;  <-- ref of variable `x` is used.
<BB3, i+1>
<BB3, ...>
```

There are only two possible result of UD chain:

- If the variable `x` **has set point(s) inside the same BB** one more many times: The UD Chain will **only contain the closest set point before line `i`.**
- No any set point for `x` in this BB: The UD Chain will be all set point of `x` inside $in[BB]$.

## Backward Analyze

Backward analyze used to detect the active variables in different position of the program. The formula is shown below:

$$
LiveIn[B] = LiveUsed[B] \cup (LiveOut[B] - Def[B])
$$

- $LiveIn[B]$ : The **active variables at the start** of the BB.
- $LiveUsed[B]$ : The **ref has been used in BB** and **no set point before** the use.
- $LiveOut[B]$ : Active variables **at the end of the BB.**
- $Def[B]$ : Variables that **has set point in this BB**, and **no any ref before the earliest set point.**

Based on the info, we know $LiveOut[B] = \cup LiveOut[C]$, where $C$ could be any following BB in the flow.

## DU Chaining

For a Set Point of variable `x`, if exists a path from this SP to a ref `R` to `x`, and there is no other SP in this path, then the ref info of `R` in contained in the DU Chaining of this SP of `x`.

To be simple, DU Chianing is the set representing all possible use of current Set Point.

Like the UD Chaining, we also have two situation here:

- If for a SP of `x`, no other SP of `x` after this one inside BB: 
  - $DU[SP] = LiveOut[B] \cup RefAfterSP$. Where $RefAfterSP$ refers to all refs of variable `x` after this single SP in this BB.
- If there are multiple SP of `x` in BB:
  - $DU[SP] = RefBeforeNextSP$. Where $RefBeforeNextSP$ refers to all refs of variable `x` after this SP and before the next SP of `x`.

