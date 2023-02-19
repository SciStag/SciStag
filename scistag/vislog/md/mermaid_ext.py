"""
A Mermaid extension of Python Markdown, replaces mermaid code blocks through mermaid
html divs.
"""

import markdown
from markdown.preprocessors import Preprocessor


class MermaidProcessor(Preprocessor):
    """
    Searches for code-blocks flagged with the language mermaid and replaces them
    with a mermaid div
    """

    def embed_block(self, code: list[str], output: list[str]):
        """
        Embeds a code block

        :param code: The original code
        :param output: The list to which the output shall be added
        """
        output.append('<div class="mermaid">')
        for line in code:
            output.append(line)
        output.append("</div><script>mermaid.contentLoaded()</script>")

    def run(self, lines):
        """Find code blocks and store in htmlStash."""
        result_lines = []
        in_block = False
        is_target = False
        code_block = []
        for index, cur_line in enumerate(lines):
            cur_line: str
            if cur_line.startswith("```"):
                if in_block:
                    if not is_target:
                        result_lines.append(cur_line)
                    if is_target:
                        self.embed_block(code_block, result_lines)
                    in_block = False
                    is_target = False
                else:
                    in_block = True
                    code_block = []
                    is_target = cur_line[3:].lstrip(" ").startswith("mermaid")
                    if not is_target:
                        result_lines.append(cur_line)
            else:
                if is_target:
                    code_block.append(cur_line)
                else:
                    result_lines.append(cur_line)

        return result_lines


class MermaidExtension(markdown.Extension):
    """
    Adds Mermaid support to Markdown by replacing code-blocks flagged as mermaid code
    """

    def __init__(self):
        super().__init__()

    def extendMarkdown(self, md):
        mmproc = MermaidProcessor(md)
        md.preprocessors.register(mmproc, "mermaid", 0)
        md.registerExtension(self)
