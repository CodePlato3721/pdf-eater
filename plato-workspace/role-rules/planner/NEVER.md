Never create a standalone "write tests" task — test cases for a piece of work belong inside the task that implements that piece of work.
改动量很小、且跨层强耦合的任务，不要为了凑 tech-stack 层数硬拆成多个任务；只有在各层有实质独立工作量时才按 MATRIX_SPLIT.md 拆分。
