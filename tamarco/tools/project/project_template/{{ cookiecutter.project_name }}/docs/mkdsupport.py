"""An Sphinx extension supporting for sphinx.ext.autodoc with modules containing docstrings in Markdown
"""

import pypandoc
from recommonmark.transform import AutoStructify

# Since pypandoc.convert_text will always return strings ended with \r\n, the separator should also set to it
SEP = u'\r\n'


def setup(app):
    """Add extension's default value and set new function to ```autodoc-process-docstring``` event"""

    # The 'rebuild' parameter should set as 'html' rather than 'env' since this extension needs a full rebuild of HTML
    # document
    app.add_config_value('mkdsupport_use_parser', 'markdown_github', 'html')
    app.connect('autodoc-process-docstring', pandoc_process)

    # for mkd files extended directives for rst transformation
    # http://recommonmark.readthedocs.io/en/latest/auto_structify.html#autostructify-component
    app.add_transform(AutoStructify)


def pandoc_process(app, what, name, obj, options, lines):
    """"Convert docstrings in Markdown into reStructureText using pandoc
    """

    if not lines:
        return None
    if lines[0] != "mkd":
        return

    input_format = app.config.mkdsupport_use_parser
    output_format = 'rst'

    # Since default encoding for sphinx.ext.autodoc is unicode and pypandoc.convert_text, which will always return a
    # unicode string, expects unicode or utf-8 encodes string, there is on need for dealing with coding
    text = SEP.join(lines)
    text = pypandoc.convert_text(text, output_format, format=input_format)

    # The 'lines' in Sphinx is a list of strings and the value should be changed
    del lines[:]
    lines.extend(text.split(SEP))
