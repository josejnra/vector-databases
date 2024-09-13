## Ollama locally

### Download models

```bash
ollama pull all-minilm
ollama pull llama3.1:8b
```


```bash
curl http://localhost:11434/api/generate -d '{"model": "llama3.1:8b","prompt":"What is a vector database?", "stream": false }'
```
