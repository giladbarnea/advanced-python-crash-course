#!python3
from rich import print
from rich.traceback import install

install(extra_lines=5, show_locals=True, width=150)
from pathlib import Path
import os
import click
from bs4 import BeautifulSoup as BS, Tag


def find_reveal_js():
    if (Path.cwd() / "reveal.js").exists():
        return Path.cwd() / "reveal.js"
    this_files_dir = Path(__file__).parent
    if (this_files_dir / ".internal/reveal.js").exists():
        return (this_files_dir / ".internal/reveal.js").resolve()
    if (this_files_dir.parent / ".internal/reveal.js").exists():
        return (this_files_dir.parent / ".internal/reveal.js").resolve()
    if (this_files_dir.parent.parent / ".internal/reveal.js").exists():
        return (this_files_dir.parent.parent / ".internal/reveal.js").resolve()
    return None





@click.command()
@click.argument("notebook_path", type=click.Path(exists=True))
@click.option("--reveal-prefix", required=False, default="https://unpkg.com/reveal.js@4.0.2")
@click.option(
    "--theme",
    default="dark",
    type=click.Choice(["dark", "light"]),
    help="nbconvert slides theme. Looks like it only understands light and dark, not dracula etc. dark works best if c.SlidesExporter.reveal_theme = 'dracula' in jupyter_nbconvert_config.py",
)
@click.option(
    "--reveal-theme",
    default="dracula",
    type=click.Choice(["sky","serif","solarized","white","beige","moon","dracula","league","blood","simple","black","night"]),
    help="Looks like it only understands light and dark, not dracula etc. dark works best if c.SlidesExporter.reveal_theme = 'dracula' in jupyter_nbconvert_config.py",
)
def main(notebook_path: Path, reveal_prefix="https://unpkg.com/reveal.js@4.0.2", theme="dark", reveal_theme="dracula"):
    run_jupyter_nbconvert(notebook_path, reveal_prefix, theme, reveal_theme)
    html_path: Path = Path(notebook_path).with_suffix(".slides.html")
    assert Path(html_path).exists(), f"html file {html_path} not found"
    txt = replace_some_content(html_path, reveal_prefix)
    html_path.write_text(txt)
    # bs = replace_jupyter_code_with_reveal_code(html_path)
    # html_path.write_text(str(bs))
    print(f"Converted {notebook_path} to modified {html_path}")


def run_jupyter_nbconvert(notebook_path, reveal_prefix, theme, reveal_theme):
    # reveal_js_path = reveal_prefix or find_reveal_js()
    # reveal_js_path = "https://unpkg.com/reveal.js@4.0.2"
    cmd = (
        f"jupyter nbconvert {notebook_path} "
        f"--to slides "
        f"--SlidesExporter.reveal_theme={reveal_theme} "
        f"--theme={theme} "
    )
    if reveal_prefix:
        cmd += f"--reveal-prefix={reveal_prefix} "
    exit_code = os.system(cmd)
    if exit_code != 0:
        raise RuntimeError(f"jupyter nbconvert failed with exit code {exit_code}")


def replace_some_content(html_path, reveal_prefix):
    txt = Path(html_path).read_text()
    reveal_initialize = dict(
        search="""],

    function(Reveal, RevealNotes){
        // Full list of configuration options available here: https://github.com/hakimel/reveal.js#configuration
        Reveal.initialize({
            controls: true,
            progress: true,
            history: true,
            transition: "slide",
            slideNumber: "",
            plugins: [RevealNotes]
        });""",
        replace=f""",
            "{reveal_prefix}/plugin/highlight/highlight.js",
        ],

        function (Reveal, RevealNotes, RevealHighlight) {{
            Reveal.initialize({{
            controls: false,
            progress: true,
            history: true,
            transition: "slide",
            slideNumber: "c/t",
            navigationMode: "linear",
            // autoAnimateDuration: 0.2,
            transitionSpeed: "fast",
            // width: "80%",
            plugins: [RevealNotes, RevealHighlight]
     }});""",
    )
    add_monokai_theme_and_some_css = dict(
        search="""id="theme">""",
        replace=f"""id="theme">
<link rel="stylesheet" href="{reveal_prefix}/plugin/highlight/monokai.css">
<style>
.reveal p {{
    margin: var(--r-block-margin) 20% var(--r-block-margin) 0;
}}
.reveal pre {{
    width: 100%;
    font-size: var(--jp-code-font-size);
    line-height: 1.3em;
    font-family: 'Fira Code', 'Roboto Mono', 'Courier New', Courier, monospace;
}}
</style>
""",
    )
    set_reveal_slides_height_to_650px = dict(
        search=""".reveal .slides {
  text-align: left;
}""",
        replace=""".reveal .slides {
    text-align: left;
    height: 650px !important;
}""",
    )
    make_jp_vars_smaller = dict(
        search="""
    --jp-ui-font-size1: 20px;       /* instead of 14px */
    --jp-content-font-size1: 20px;  /* instead of 14px */
    --jp-code-font-size: 19px;      /* instead of 13px */
    --jp-cell-prompt-width: 110px;  /* instead of 64px */
                """.strip(),
        replace="""
    --jp-ui-font-size1: 18px;       /* instead of 14px */
    --jp-content-font-size1: 18px;  /* instead of 14px */
    --jp-code-font-size: 16px;      /* instead of 13px */
    --jp-cell-prompt-width: 80px;  /* instead of 64px */
                """,
    )
    helvetica_neue = dict(
        search="""--jp-content-font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',""",
        replace="""--jp-content-font-family: 'Helvetica Neue';""",
    )
    rgb_225 = dict(
        search="rgba(255, 255, 255, 1);",
        replace="rgba(225, 225, 225, 1);",
    )
    for search_replace in [
        reveal_initialize,
        add_monokai_theme_and_some_css,
        make_jp_vars_smaller,
        helvetica_neue,
        # rgb_225,
        # set_reveal_slides_height_to_650px,
    ]:
        search, replace = search_replace["search"], search_replace["replace"]
        assert search in txt, "Not in txt: \n" + search
        txt = txt.replace(search, replace)
    return txt


def replace_jupyter_code_with_reveal_code(html_path):
    bs = BS(html_path.read_text())
    for code_cell in bs.find_all(attrs={"class": "jp-CodeCell"}):
        new_code = code_cell.get_text().strip()
        code = Tag(name="code")
        code.string = new_code
        pre = Tag(name="pre")
        section = Tag(name="section")
        pre.insert(0, code)
        section.insert(0, pre)
        code_cell.parent.replaceWith(section)
    return bs


if __name__ == "__main__":
    main()
