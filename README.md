# Latent Capability Discovery (LCD)

> ## What if we already know the answer...we just don't know that we know it?

**An experiment in using AI to find solutions hidden by the way humans organize knowledge.**

We divide knowledge into fields: software engineering, physics, biology, medicine, economics, manufacturing, and thousands more.

AI doesn't necessarily have to.

LCD decomposes a problem into its underlying **capabilities and mechanisms**, then searches across fields for existing knowledge that works the same way—even when the terminology and subject matter look completely unrelated.

### Traditional search

> **"Find things that sound like my problem."**

### Latent Capability Discovery

> **"Find things that work like my problem."**

The first prototype suggests this distinction matters.

Using the same 40-item knowledge base:

- **Text-based RAG** ranked the correct cross-domain mechanism at **3.00 on average**
- **LCD** improved that average rank to **1.42**
- With a fixed 5-attempt budget, **RAG solved 9 of 12 problems (75%)**
- **LCD solved 11 of 12 (92%)**, while using about **35% fewer attempts**

Given enough attempts, both approaches eventually find all the solutions in this small knowledge base. The interesting result isn't that RAG *can't* find them.

**LCD finds useful knowledge faster by representing the problem differently.**

The long-term idea is simple:

> **Don't just give AI more knowledge. Help it recognize more of what is already hidden inside the knowledge we have.**

Or, even shorter:

> ## Don't search for things that sound alike. Search for things that work alike.