# MPEG-DASH (Video Downloader)
## Description

Foobar is a Python library for dealing with word pluralization.

## Installation

General advice is to use **virtual environment** before installing any packages.

### Create venv

```bash
python -m vevn venv_path
```

### Activate venv

```bash
source venv_path/Scripts/activate
```

### Use pip

Use the package manager **pip** to install dash.

```bash
pip install git+https://github.com/beckamartin/mpeg-dash
```

## Usage

```python
import vimeo

# returns 'words'
foobar.pluralize('word')

# returns 'geese'
foobar.pluralize('goose')

# returns 'phenomenon'
foobar.singularize('phenomena')
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)

## References
- [Wikipedia - Dynamic Adaptive Streaming over HTTP](https://en.wikipedia.org/wiki/Dynamic_Adaptive_Streaming_over_HTTP)
- [FFmpeg](https://www.ffmpeg.org/download.html)