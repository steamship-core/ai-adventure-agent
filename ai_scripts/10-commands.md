# Commands

Let's talk about commands.

You can probably guess by now that a GenDown command is something in brackets, like this: `[GenerateText]`

## Invoking a Command

A command is always associated with text -- which could be empty!

If the command begins a Gendown sentence or paragraph, that sentence or paragraph is its **default argument**

Here are some examples:

[GenerateText] I am the default argument to the `GenerateText` command -- a prompt!

[GenerateText] 
I am the default argument to 
the `GenerateText` command -- a 
prompt! I am taking advantage of Markdown
paragraph rules!

Sometimes you need to associate more than one paragraph of text with a command. 
For that, use a block quote.

    [GenerateText]
    Everything in this block quote.

    Is the default argument of the command!

## Passing Arguments

Sometimes you need to pass more arguments to a command.
For example: what if you wanted to set the temperature of a generation?

If a code block immediately follows a command, it is assumed that code-block provide the arguments.

[Generate] Tell a joke

```json
{
  "temperature": 0.9
}
```

## Defining New Commands

You can define a new command easily using the format below.

This means 

### DEFINE HighTempGenerate FROM Generate

The text inside this header {caller._content} is the content template for this command.

```json
{
  "temperature": 0.9
}
```

## Reserved Commands

GenDown has a few reserved commands:

* `[If (condition)]` To start a conditional block
* `[ElseIf (condition)]` To implement an else-if block
* `[Else]` To implement an else block
* `[EndIf]` To finish a conditional block
* `[ForEach (var])`
* `[Repeat n]` To repeat something N times
* `[Run]` Runs a document or fragment, as a subroutine
* `[Return]` Returns immediately to the calling document fragment

These let you implement rudimentary logic flow in your stories.

