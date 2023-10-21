AI Script is a lightweight extension of Markdown that allows an editor-friendly markdown
    document to craft a multimedia storytelling experience.

    Here's how it works.

    # Headings just headings.

    The agent will say normal text exactly as written.

        A block quote is appended to the system prompt.
        No interaction with the user is implied.
        This block is now in the history!

    The script keeps generating until a Collect event happens.
    This is a collect event.

    By the way, what's your name?

    [Collect {name}]

    Amazing {name}! It's great to meet you.

    ## Conditionals

    {% if description %}

    Lightweight boolean expressions about variables are supported, like github actions.

    This lets us know we know {description} about you.

    {% else %}

    What's your description?

    [Collect {description}]

    { % endif %}

    ## Sending Generated Content

    Sometimes you want to send something the LLM generates to the user.

    To do that, use the [Generate] token. It's usually best to preceed this with a system message.

        Tell the user a knock knock joke.

    [Generate]

    ## Generating to a variable

    Sometimes you want to generate to a variable.
    This won't go into the chat history.

    Just say: [Generate {variable_name}]

    For example:

        Write a stable diffusion prompt for a cow standing on a hill.

    [Generate {variable_name}]

    Now that variable is set to the output of that generation.

    Let's try an example!

    What's a country you like?

    [Collect {country}]

        Who is a famous person from {country}?

    [Generate {person}]

    A famous person from that country is: {person}

    Let's try generating something

        Write a

    ## Hash Tags

    Hash tags are an important filtering mechanism.

    ## Sending Images

    In markdown you send an image like this:

    ![Alt Text](Isolated.png "Title")

    In Ai Script, you send an image like this:

    ```define: item gen

    ```

    ![Alt Text](item-image "Title")

