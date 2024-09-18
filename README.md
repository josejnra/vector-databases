## Concepts

### Vector Database



### Embedding Models

Embedding models are models that are trained specifically to generate vector embeddings: long arrays of numbers that represent semantic meaning for a given sequence of text:


## Ollama locally

### Download models

```bash
ollama pull all-minilm
ollama pull llama3.1:8b
```


```bash
curl http://localhost:11434/api/generate -d '{"model": "llama3.1:8b","prompt":"What is a vector database?", "stream": false }'

# remote
curl http://192.168.0.12:11434/api/generate -d '{"model": "llama3.1:8b","prompt":"What is a vector database?", "stream": false }'
```

## References
- [Embedding Models](https://ollama.com/blog/embedding-models)
