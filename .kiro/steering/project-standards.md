## UI: Streamlit

- Please use Streamlit UI

## Anaconda Environment

- Please use Anaconda 'project' environment

## Shutdown Streamlit Button

- Include one Shutdown App button in Streamlit UI.
- Below is a sample code:

```python
def shutdown_app():
    """Gracefully terminate the Streamlit application."""
    logger.warning("Shutdown requested by user")
    st.warning("Shutting down...")
    time.sleep(0.5)
    try:
        keyboard.press_and_release("ctrl+w")
        pid = os.getpid()
        logger.info(f"Terminating process PID={pid}")
        p = psutil.Process(pid)
        p.terminate()
    except Exception as e:
        logger.error(f"Shutdown failed, forcing exit: {e}")
        os._exit(0)
```

## Dependencies

- Always create a `requirements.txt` file listing all pip dependencies required by the project.

## Secrets Management

- Store all API keys and secrets in a `.env` file.
- Add `.env` to `.gitignore` to prevent secrets from being committed.
- Never expose or link any API keys or secrets to the internet.

## Documentation

- Create a `README.md` at the project root.
- Update `README.md` whenever there is a feature change.
