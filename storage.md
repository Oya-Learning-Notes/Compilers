- [Activation Record](#activation-record)
- [NonLocals In Nested Procedure](#nonlocals-in-nested-procedure)
  - [Display Table](#display-table)
    - [Layers](#layers)
    - [Maintain Display Table](#maintain-display-table)
  - [Access Link](#access-link)
- [Function Call](#function-call)
  - [Structure](#structure)
  - [Dynamic Dispatch](#dynamic-dispatch)


This article will mainly talk about the Storage Management in Compilers.

# Activation Record

Could be considered a stack that records the info of the nested structure of how funcitons are triggered.

# NonLocals In Nested Procedure

This problem exists in the languages that allows nested procedure / function declration. Consider the example:

```python
def func_a():
    val_in_a = 1

    def func_b():
        val_in_b = 2

        def func_c():
            val_in_c = 3
            val_in_a += 1
            val_in_b += 1
```

As you see, the inner function should have the ability to access the data in the outer function scope.

-----

Basically, we could use the power of Activation Record. The corresponding Activation Record of the outer scope function is always the latest one:

```
If: the nest strcuture is A > B > C

Activation Record: A > B > A > B > C

Then we should use the second A and B when accessing outer scope.
```

-----

Now the problem becomes **how to track the latest Activation Record item of the outer scope**. There are two general approaches:

- Display Table
- Static Link (Access Link)

## Display Table

This method uses a table to record the address of the AR(Activation Record) of each layer of the nested function.

![image](https://github.com/user-attachments/assets/71d77608-45e9-4404-a1ed-1bf6157fc21c)

As we see, the structure is like `table[layer] = addr`

### Layers

In this case, we defined that:

- Main Scope is in 0 layer.
- Any top-level defined function is in 1 layer.
- Nested functions has 1 + [nested_layers] layer.

In example above, `func_a` has layer `1`, `func_b` has layer `2`.

### Maintain Display Table

First we need to acknowledge that Display Table will change during program execution. Probably when a new function is called.

-----

One way to maintain such table is using Traceback method.

Everytime when a new function is called, we preform following actions:

- Get the layer $L$ of the newly called function.
- Get previous Display Table Item of this layer $Table[L]$
- Store the info of the previous item (Actually that is the address of the Activation Record which $Table[L]$ points to) in the new Activation Record.
- Override $Table[L]$ = Activation Record of newly called function.

In this method, we notice that:

- Only one table used, that is Global Display Table.
- Some Table Item may be stored in some of the Activation Record.

-----

Here is an example, consider a nested function declaration structure `a > b > c`. And the call stack `a > b > c > s > a > b > c`. (In which function `s` is a top level function which means it has layer 1)

Then the Global Display Table and the Activation Stack will be like:

![image](https://github.com/user-attachments/assets/9b373046-e00a-4407-8511-eec002885558)

Notice that Global Display Table always store that newest info. And if some item has been overridden when updating table, then the Traceback Info will be stored in the Activation Record.

## Access Link

> There is a corresponding concept called Control Link (or Dynamic Link)

The core rule for Access Link is quite simple: **For a Activation Record of function $F$, if $Layer(F) = L$, then the Access Link in this AR should point to the latest AR with function in layer $L-1$.** That is, always point to the latest AR that has lower layer.

![image](https://github.com/user-attachments/assets/ad4fba62-57c0-43aa-9367-228afa3687ca)

![image](https://github.com/user-attachments/assets/7f012b54-698e-4df9-90f0-32d10cc636af)

> Also notice that Dynamic Link always points to the AR that directly before it.

# Function Call

## Structure

There are two important part of the function call:

- Calling Sequence
- Return Sequence

Calling Sequence could be performed both by caller and callee. Return Sequence is usually done by callee.

However, we hope that most of the Calling Sequence operation is done by callee.

## Dynamic Dispatch

Actually, the core problem in this part is to figure out how Dynamic Dispatch works. One of the balanced way is to use Routine Table, which is something like the VTable in C++.

[VTable & VPointers in C++, Explained](https://pabloariasal.github.io/2017/06/10/understanding-virtual-tables/)