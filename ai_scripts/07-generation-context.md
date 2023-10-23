# Generation Context

THIS IS JUST AN IDEA SKETCH

When you're using generative AI, it's helpful to filter the context that gets send to the AI.

Every line in your Gendown story can use a carat character `^tag` to tag it.

We use a carat instead of a hashtag because we don

For example, if you wanted to tag the back-and-forth of asking a user their name, you could say:

What's your name? ^name

[Input name] ^name

Then, if you wanted to generate content and INCLUDE that exchange, you could say:

[GenerateText greeting ^name] Greet the that just introduced themselves.


