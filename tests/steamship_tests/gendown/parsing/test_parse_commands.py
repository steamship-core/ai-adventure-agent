from gendown.gendown_parser import parse_gendown, NodeKind

def test_parse_oneline_command():
    nodes = parse_gendown("""[Generate] Hi there""")
    assert len(nodes) == 1
    assert nodes[0].kind == NodeKind.command
    assert nodes[0].command == "Generate"
    assert nodes[0].text == "Hi there"

def test_parse_oneline_command_inline_arg():
    nodes = parse_gendown("""[Input name] """)
    assert len(nodes) == 1
    assert nodes[0].kind == NodeKind.command
    assert nodes[0].command == "Input"
    assert nodes[0].text == ""
    assert nodes[0].inline_command_arg == "name"

def test_parse_one_para_command():
    nodes = parse_gendown("""[Generate] Hi there
This is
A Paragraph Prompt""")
    assert len(nodes) == 1
    assert nodes[0].kind == NodeKind.command
    assert nodes[0].command == "Generate"
    assert nodes[0].text == "Hi there\nThis is\nA Paragraph Prompt"

def test_parse_multi_para_command():
    nodes = parse_gendown("""
This is regular output.

    [Generate] Hi there
    This is
    A Paragraph Prompt

    * Paragraph two of the prompt

This is regular output.
    """)
    assert len(nodes) == 3
    assert nodes[0].kind == NodeKind.output
    assert nodes[0].text == "This is regular output."

    assert nodes[1].kind == NodeKind.command
    assert nodes[1].command == "Generate"
    assert nodes[1].text == "Hi there\nThis is\nA Paragraph Prompt\n\n* Paragraph two of the prompt"

    assert nodes[2].kind == NodeKind.output
    assert nodes[2].text == "This is regular output."


def test_parse_one_para_command_then_text():
    nodes = parse_gendown("""[Generate] Hi there
This is
A Paragraph Prompt

And now we say this.""")
    assert len(nodes) == 2
    assert nodes[0].kind == NodeKind.command
    assert nodes[0].command == "Generate"
    assert nodes[0].text == "Hi there\nThis is\nA Paragraph Prompt"

    assert nodes[1].kind == NodeKind.output
    assert nodes[1].text == "And now we say this."
