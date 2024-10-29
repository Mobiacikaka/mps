# MPS
Multi Party Shuffling

## 11.08.2023

Graph $G = \{V, E\}$ has $N$ nodes, $|V| = N$. Each node $v_i$ has value $n_i$.
 - Choose $K$ subgraphs $G = \{G_i\}, i\in[1,K]$
 - Each subgraph $G_i$, we have $G_i = \{V_i, E_i\}$
 - For $\forall v_{i,j} \in V_i$, we have edges $E_{i,j}$ which has $v_{i,j}$ connected. (both real and fake edges)
 - And we have edge values' summation $\sum E_{i,j}$, and the atomic function is $f$. (不一定是求和, 有可能是最大值)
 - For $\forall v_{i,j} \in V_i$, we have communication overhead $C_{i,j} = n_{i,j} \times f(\sum E_{i,j})$
 - For subgraph $G_i$, we have communication overhead $C_i = \sum\limits_{n_{i,j} \in V_i} C_{i,j}$
 - The overall communication overhead is $C = \sum C_i = \sum\limits_{i=1}^K \sum\limits_{v_{i,j} \in V_i} n_{i,j} \times f(\sum E_{i,j})$
 - 一般的图划分问题是限制子图最大顶点的数量，我们的则是需要限制最小顶点的数量；

Base station placement
- The resulting technique jointly optimizes the drone’s 3D positioning to maximize coverage and allocates the network resources in such a way that gives high priority to the delay-sensitive machine-to-machine (M2M) traffic.
- 无人机部署位置优化, 即如何优化无人机在三维空间中的位置为地面用户提供服务, 以满足最大覆盖、节能可持续覆盖等目标.
- 通过优化无人机部署, 避免无人机之间的信号干扰, 同时提高无人机的电池能量利用率、信号覆盖范围.

## 
