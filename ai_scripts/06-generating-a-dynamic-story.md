# Generating a Dynamic Story Scene

Here's how you can put it all together.

Let's have the AI generate a character name.

[GenerateText name] Create a name for a character. Respond with only the name. It should be silly!

We generated {name}

Now we'll generate a setting..

[GenerateText background] Create a two-sentence character background for someone named {name}.

We generated {background}

Now we'll generate a goal..

[GenerateText goal] You're writing a story. Create a one sentence goal for {name}, whose background is {background}.

We generated {goal}

Are you ready? Let's make some story.

[GenerateImage] pixel art image of {name}, a {background}

[GenerateMusic] ambient music for story about {goal}

We've queued the streaming of our media assets, while those are loading we'll generate some sory text..

[GenerateText] Write a paragraph about how {name} sets out to achieve {background} one day. It should be creative! #problem

Now let's generate a problem.

[GenerateText] On no! {name} encountered a problem! What is it!?

How did {name} solve the problem? It's your turn to answer.

[Input solution]

Let's generate an ending for that quest.

[GenerateText] Generate an ending to problem based on {solution}
The ending should be a single graph.

THE END!