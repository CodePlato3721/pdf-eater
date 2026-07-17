背景：目前 Q&A 回答只返回 LLM 生成的结论性文字，例如：

"John Brooke first appears in the book "Little Women" in Chapter 22, which is titled "Pleasant Meadows.""

用户无法看到这个结论是基于原文哪一段得出的，需要增加原文引用，方便用户核对。

## 需求

在回答内容之后，追加一段原文引用，格式大致如下：

```
John Brooke first appears in the book "Little Women" in Chapter 22, which is titled "Pleasant Meadows."
----------------------quote from Chapter 22 Page xx------------------------
<原文片段>
```

- 分隔行标注引用来源的章节（Chapter）和页码（Page）。
- `<原文片段>` 是从原文中定位到支撑该回答的那句话（下称"命中句"），取其前后各 2 句，加上命中句本身，一共约 5 句。
- 边界情况：
  - 如果命中句是所在章节的第一句，则前面没有可取的句子，直接从命中句开始。
  - 如果命中句是所在章节的最后一句，则后面没有可取的句子，到命中句结束。
