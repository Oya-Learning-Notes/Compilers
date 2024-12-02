本文将简要介绍一种通过构造前缀树来实现提取左公因子的代码思路和实现方法。

说明：在本文文本以及代码中，将使用以下标记：

- `Terminal` 终结符。
- `NonTerminal` 非终结符。
- `Piece` 包含终结符和非终结符的所有符号。
- `Production` 产生式。
- `CFG` Context-free Grammar，上下文无关文法。
- `Source`/`LHS` Left-hand side， 产生式左部。在 `CFG` 中，其一定是一个 `NonTerminal`
- `Target`/`Derivation`/`RHS` Right-hand side，产生式右部。

# 算法思想

## 关于左公因子

在讨论对于左公因子的提取时，我们需要**对语法中所有的 `NonTerminal` 分别进行讨论**。这是因为，对于产生式来说，**只有当左部 `LHS` 相同时，左公因子才会直接对自顶向下分析产生影响**。

## 符号前缀树

### 介绍

不妨考虑这样一组 `LHS` 相同的产生式：

$$
\begin{aligned}
S \to &T \\
|& T + A \\
|& T + B \\
|& T + B + C \\
\end{aligned}
$$

如果我们以 `Derivation` 中的元素 `Piece` 为单位，构造所有 `Derivation` 组成的前缀树，我们将得到类似如下的结果：

![Pieces Prefix Tree Example](https://github.com/user-attachments/assets/9b79b61b-2367-4456-b868-90363f20372d)

后文中，我们将称这棵树为该文法中关于 `S` 的**右部符号前缀树**（_Derivations Pieces Prefix Tree_），本文中也简称`S`的前缀树。

> 需要注意的是，在这棵树中，我们在**每个 `Derivation` 的右侧（也就是末尾）添加了一个 `None` 节点**。这一个多余的节点，在本文将要介绍的代码实现中是**不可省略**的。

### 前缀树与左公因子的关系

通过前缀树，我们可以清晰的了解到，`S` 的所有 RHS 对于前缀的共享情况。

这里，我们注意到前缀树有如下性质：

- **有且仅有叶子节点为 `None` 节点**（结尾标识符节点）
- 前缀树中，从**树根（最左边）出发到某一个 `None`节点 所经过的路径，必定为 `S` 的某一个 `RHS`（右部）**。
  - 例：如对于最右上角的 `None` 节点，其路径为：`T + B + C None`，对应`RHS`为 $T+B+C$，我们**称这个右部为该`None`节点对应的 `RHS`**
- 前缀树中，若**两个`None`节点拥有公共祖先，则其对应`RHS`存在左公因子**，因为拥有公共祖先，说明树根到这两者的路径前缀必定重合。

理想的情况下，我们需要对所有 `RHS` 进行处理，使得没有**任何两个 `None` 节点拥有公共祖先**。而我们已知所有叶子节点都是 `None` 节点，从而可知，我们**需要使得前缀树所有非叶子节点有且只有一个后继节点**。因为一旦有某个节点拥有超过一个后继节点，那么意味着它必定至少是某两个叶子节点的公共祖先，而这意味着坐公因子的存在。

用更通俗的话来说就是，**前缀树中不能存在任何分叉**。

### 前缀树森林

上面的例子中，所有 `S` 的右部都以 `T` 开始，这实际上并不是一般情况。大部分情况下，**对于某一个左部 `S`，我们实际上需要一个前缀树森林来表示其所有的 `RHS` 信息**：

$$
\begin{aligned}
S \to &T \\
|& T + A \\
|& T + B \\
|& T + B + C \\
|& d X \\
\end{aligned}
$$

![Prefix Forest](https://github.com/user-attachments/assets/71f0fc1b-3eec-4dca-ac1c-12b20ef876fe)

其工作原理和前缀树没有什么区别，只是允许多个树根的存在。

## 消除前缀森林中的公共祖先

### 最终目标

简单来说，我们需要对存在分叉的前缀森林进行处理，使得森林中的任意一棵树不存在分叉。

我们用上面给出的森林做例子，最终，我们需要将其拆分为形如下面这几个森林：

`S` 的前缀树

![image](https://github.com/user-attachments/assets/4d853dde-583e-43b2-b03a-f8433a196d6e)

`Z`

![image](https://github.com/user-attachments/assets/9ce38324-8367-4d3b-a8f6-76e7b7826d24)

`Y`

![image](https://github.com/user-attachments/assets/16febc93-e86e-47f1-b4f1-7bfeae4cac63)

`W`

![image](https://github.com/user-attachments/assets/bc4154b9-7d12-4a23-9390-523cddf7695a)

注意到，由于我们使用了新的 `NonTerminal` 符号 `W` `Y` `Z`，原来在 `S` 前缀森林中的一部分内容，并不再以 `S` 作为 `LHS`，故不会再出现在 `S` 的前缀森林中，**而是以被拆分的形式，出现在一些我们创建的，新的 `NonTerminal` 的森林中**。

此外，不难发现完成拆分之后，所有的 `NonTerminal` 的前缀树都没有任何分叉，说明所有左公因子都完成了提取，而这就是我们想要实现的效果。

### 拆分步骤

简单来说，对于任意一个前缀森林，我们递归地做以下操作：

- 对于森林中的每一棵树：
  - 从树根开始往末尾搜索：
    - 直到末尾都没有发现分叉：这棵树无需改动，处理结束
  - 发现分叉：在分叉处切断，构成两个部分：
    - 分叉前：仍然是一个无分叉的数，在其末尾添加一个生成的新 `NonTerminal`，处理完成
    - 分叉后：各个分叉恰好构成新的森林，认定该森林对应的`LHS`（左部）为刚刚生成的新 `NonTerminal`，递归处理该森林

我们仍然以上面的森林为例子：

---

第一棵树，没有分叉，无需处理。

![p1](https://github.com/user-attachments/assets/0759ae5d-9938-4c7f-a062-d54e19e0f674)

---

第二棵树，发现分叉，按照规则进行拆分。

![p2](https://github.com/user-attachments/assets/ab797b3d-e706-4540-883b-daa873be32c9)

对于切开的左边 `T`，在其后添加新创建的 `Nonterminal` `Z`，结束。
对于切开的右边，认定新的 `Nonterminal` `Z`为新的子森林的左部。

![p3](https://github.com/user-attachments/assets/354d8a16-0898-4643-a8b3-b2319d4df194)

`S`的前缀森林已经没有分叉，但是新产生的 `Z` 符号的前缀树中存在分叉，以同样的规则，递归地进行处理，直到文法中所有 `NonTerminal` 的前缀树都没有分叉为止。

## 将森林转换为产生式

在完成对于森林的处理后，我们需要将森林转换回一组组新的产生式。具体流程如下：

对于一个森林：

- 其转换而成的所有产生式的`LHS`，为该森林的`LHS`。
- 其转换而成的所有产生式的`RHS`，为所有 `None` 节点对应的 `RHS`（即：森林中所有树的路径）。

这里举个例子，对于下面这个森林 （假设其对应 `LHS` 为 `S`）：

![forest](https://github.com/user-attachments/assets/750e16ab-1656-407b-a976-35263d644c01)

由于森林的 `LHS` 为 `S`，所以所有的产生式均形如： $S \to \dots$

同时，`None` 节点对应着两个 `RHS`: $dX, TZ$，故我们可以得到两条产生式：

$$
S \to dX
S \to TZ
$$

> 注：如果森林中存在树根直接是 `None` 节点的情况，则添加空产生式 $S \to \varepsilon$

至此，我们已经将所有需要的算法描述完毕。

# 算法实现

## 思路

根据上方算法的思想，我们可以按照如下思路实现代码：

- 对于一个文法系统，遍历其所有 `NonTerminal`:
  - 对于每一个 `NonTerminal`，构造前缀森林，并消除公共祖先，得到一组符合条件新的前缀森林。
- 将所有得到的无公共祖先前缀森林，转换成一组新的 `Production`
- 通过这一组新的 `Production` 构造一个新的文法系统（新的文法系统开始符号和结束终结符均和原系统中保持一致）。新的文法系统中，必定不含有左公共因子，处理完成。

## 实现概要

我们需要分别实现：

- `CFGSystem` 上下文无关文法类，可以对文法进行储存和基本操作，如求出 $first$, $follow$ 集合等。
  - `LL1CFGSystem` 继承上述类，提供诸如提左公因子，检查文法是否是 LL(1)的等等功能。
- `Piece` 符号数据类
  - `Terminal` / `NonTerminal` 继承上述类，储存终结符和非终结符。
- `PrefixTreeNode` 储存前缀树节点，前缀树。
- `PrefixTreeManager` 储存前缀森林，并提供诸如 消除公共祖先，树的切分，森林可视化等等方法。

这里强烈推荐，对于上述的所有数据类，都为`__hash__`, `__eq__` 方法提供合理的重载，因为各种数据类后续都可能需要作为 `dict`的 Key 进行使用，或者存放在`set`等容器中。

## 示例代码

您可以查看 [这个 GitHub 项目](https://github.com/Oya-Learning-Notes/Compilers/tree/4_ll/code/py_impl/packages/cfg) 中的 `cfg` 目录部分，其中的各个文件分别完成了上述实现概要中提到的类：

- 实现
  - [cfg/type.py](https://github.com/Oya-Learning-Notes/Compilers/blob/4_ll/code/py_impl/packages/cfg/type.py) `Piece`, `NonTerminal`, `Terminal`, `CFGSystem`
  - [cfg/ll1.py](https://github.com/Oya-Learning-Notes/Compilers/blob/4_ll/code/py_impl/packages/cfg/ll1.py) `PrefixTreeNode`, `PrefixTreeManager`, `LL1CFGSystem`
- 测试
  - [tests/cfg_left_factors_test.py](https://github.com/Oya-Learning-Notes/Compilers/blob/4_ll/code/py_impl/tests/cfg_left_factors_test.py) 测试用例和测试代码

由于篇幅原因，很多实现细节并没有直接在本文档中给出。详情请查看文件中各个部分的代码注释。

> 文件中同样包含了关于消除左递归的代码实现，详情请查看 `LL1CFGSystem`.

### 在本地运行代码

如果您想在本地运行本代码库中的相关内容，请按照 [此文档](https://github.com/Oya-Learning-Notes/Compilers/blob/4_ll/code/py_impl/doc/install.md) 的指引正确配置本地环境。配置完成后，方可运行本仓库中的代码。
