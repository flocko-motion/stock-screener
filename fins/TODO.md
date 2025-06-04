Next steps:

- file ops: 
  - remove persisted baskets

- multithreaded fin data fetching:
  - create baskets from lists, not iteratively. this allows centralized implementation of multithreaded fetching. 10x speedup should be the minimum, 100x should be possible