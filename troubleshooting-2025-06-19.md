# Troubleshooting Guide - June 19, 2025

## ArXiv MCP Server Import Issue

### Problem
When implementing an MCP server for ArXiv paper search, encountered the error:
```
Error executing tool search_papers: module 'arxiv' has no attribute 'Search'
```

### Root Cause
The issue was caused by a **filename conflict**. The server file was originally named `arxiv.py`, which was shadowing the actual `arxiv` library import.

### Debugging Steps
1. **Initial assumption**: Wrong arxiv library version
   - Checked library version and available attributes
   - Confirmed `Search` and `Client` classes were available

2. **Environment testing**: 
   ```bash
   uv run python -c "import arxiv; print(dir(arxiv))"
   # Output showed Search was available
   ```

3. **Directory-specific testing**:
   ```bash
   # When run from servers/ directory:
   uv run python -c "import arxiv; print(hasattr(arxiv, 'Search'))"
   # Output: False (!)
   
   # When run from parent directory:
   # Output: True
   ```

4. **Discovery**: The filename `arxiv.py` was causing Python to import the local file instead of the installed library.

### Solution
1. **Renamed the server file** from `arxiv.py` to `arxiv_server.py`
2. **Optimized the arxiv client** for better responsiveness:
   ```python
   client = arxiv.Client(
       page_size=max_results,
       delay_seconds=1,  # Reduced from default 3 seconds
       num_retries=2     # Reduced from default 3 retries
   )
   ```

### Key Learnings
- **Naming conflicts** can cause subtle import issues that are hard to debug
- Always avoid naming Python files the same as installed packages
- The arxiv library v2.x uses `Client.results(search)` instead of deprecated `search.results()`
- MCP Inspector timeouts can be resolved by optimizing API client settings

### Prevention
- Use descriptive, non-conflicting filenames (e.g., `arxiv_server.py`, `weather_client.py`)
- Test imports in isolation when debugging
- Check for filename conflicts when encountering unexpected import errors